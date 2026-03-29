"""
Entry point.
Smart router: known command patterns run directly, everything else goes through AI.
"""
from __future__ import annotations

import random
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

# Ensure UTF-8 output on Windows — wrapped in try so winpty pipes are not broken
try:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if sys.platform == "win32" and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import typer
from rich.console import Console
from rich.prompt import Confirm

from . import config, display
from .ai import ParsedCommand, parse as ai_parse

app     = typer.Typer(help="trade — Angel One CLI with AI natural language support", add_completion=False)
console = Console()

# ------------------------------------------------------------------ splash

C  = "\033[1;36m"   # bold cyan
DIM= "\033[2m"
RST= "\033[0m"

_LOGO = [
    "  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557\u2588\u2588\u2588\u2588\u2588\u2588\u2557  \u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2557 \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
    "     \u2588\u2588\u2554\u2550\u2550\u255d\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2550\u2550\u255d",
    "     \u2588\u2588\u2551   \u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2557  ",
    "     \u2588\u2588\u2551   \u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2557\u2588\u2588\u2554\u2550\u2550\u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2554\u2550\u2550\u255d  ",
    "     \u2588\u2588\u2551   \u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2551  \u2588\u2588\u2551\u2588\u2588\u2588\u2588\u2588\u2588\u2554\u255d\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2557",
    "     \u255a\u2550\u255d   \u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u255d  \u255a\u2550\u255d\u255a\u2550\u2550\u2550\u2550\u2550\u255d \u255a\u2550\u2550\u2550\u2550\u2550\u2550\u255d",
]


def _splash():
    """Animated intro using plain print — works on all terminals incl. winpty."""
    from trade import __version__

    print()
    for line in _LOGO:
        print(f"{C}{line}{RST}")
        sys.stdout.flush()
        time.sleep(0.07)

    print()
    print(f"  {DIM}Angel One  |  AI-powered trading   v{__version__}{RST}")
    print(f"  {DIM}{'─' * 44}{RST}")
    print()


# ------------------------------------------------------------------ help

def _help():
    print()
    print(f"  {C}PRICES{RST}")
    print(f"  {DIM}  price ITC                      live price{RST}")
    print(f"  {DIM}  price ITC RELIANCE HDFC        multiple{RST}")
    print(f"  {DIM}  search spandana                find a stock{RST}")
    print(f"  {DIM}  history ITC                    chart (1m default){RST}")
    print(f"  {DIM}  history ITC --period 6m        6 month chart{RST}")
    print()
    print(f"  {C}TRADING{RST}")
    print(f"  {DIM}  buy ITC 10                     market buy{RST}")
    print(f"  {DIM}  buy ITC 10 --limit 450         limit buy{RST}")
    print(f"  {DIM}  sell RELIANCE 5                market sell{RST}")
    print(f"  {DIM}  buy ITC 10 --user dad          from dad's account{RST}")
    print()
    print(f"  {C}ACCOUNT{RST}")
    print(f"  {DIM}  portfolio                      my holdings + P&L{RST}")
    print(f"  {DIM}  portfolio --user dad           dad's holdings{RST}")
    print(f"  {DIM}  positions                      intraday positions{RST}")
    print(f"  {DIM}  funds                          available cash{RST}")
    print(f"  {DIM}  orders                         today's orders{RST}")
    print(f"  {DIM}  list-users                     all configured users{RST}")
    print()
    print(f"  {C}NATURAL LANGUAGE{RST}")
    print(f"  {DIM}  buy spandana sphoorty 15 from dad{RST}")
    print(f"  {DIM}  how is my portfolio doing{RST}")
    print(f"  {DIM}  which of dad's stocks are in loss{RST}")
    print()
    print(f"  {DIM}  exit / quit   →   close{RST}")
    print()


# ------------------------------------------------------------------ REPL

def _repl():
    """Interactive prompt loop — type anything, Ctrl-C or 'exit' to quit."""
    print(f"  {DIM}Type a command or ask anything in plain English.{RST}")
    print()

    while True:
        try:
            raw = input("  \033[1;36m>\033[0m ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  [Ctrl+C] Closing trading terminal. Goodbye.\n")
            break

        if not raw:
            continue

        if raw.lower() in ("exit", "quit", "q", ":q", "close"):
            console.print("[dim]  Closing trading terminal. Goodbye.[/dim]\n")
            break

        if raw.lower() in ("help", "?"):
            _help()
            continue

        console.print()
        try:
            _route(raw)
        except KeyboardInterrupt:
            console.print("\n[dim]  Cancelled.[/dim]")
        console.print()

# ------------------------------------------------------------------ helpers

_STRUCTURED = {
    "price":      lambda t: ParsedCommand(action="price",     symbols=t[1:]),
    "search":     lambda t: ParsedCommand(action="search",    symbol=" ".join(t[1:])),
    "history":    lambda t: _parse_history(t),
    "buy":        lambda t: _parse_order("buy",  t),
    "sell":       lambda t: _parse_order("sell", t),
    "portfolio":  lambda t: ParsedCommand(action="portfolio", user=_flag(t, "--user", "-u")),
    "positions":  lambda t: ParsedCommand(action="positions", user=_flag(t, "--user", "-u")),
    "funds":      lambda t: ParsedCommand(action="funds",     user=_flag(t, "--user", "-u")),
    "orders":     lambda t: ParsedCommand(action="orders",    user=_flag(t, "--user", "-u")),
    "list-users": lambda t: ParsedCommand(action="orders"),   # handled separately
}


def _flag(tokens: list[str], *flags: str) -> Optional[str]:
    """Extract value after a flag e.g. ['--user', 'dad'] → 'dad'."""
    for f in flags:
        if f in tokens:
            idx = tokens.index(f)
            if idx + 1 < len(tokens):
                return tokens[idx + 1]
    return None


def _parse_history(t: list[str]) -> ParsedCommand:
    period   = _flag(t, "--period")   or "1m"
    interval = _flag(t, "--interval") or "1d"
    symbol   = t[1] if len(t) > 1 else ""
    return ParsedCommand(action="history", symbol=symbol, period=period, interval=interval)


def _parse_order(action: str, t: list[str]) -> ParsedCommand:
    symbol = t[1] if len(t) > 1 else ""
    qty    = int(t[2]) if len(t) > 2 and t[2].isdigit() else None
    limit  = _flag(t, "--limit", "-l")
    user   = _flag(t, "--user",  "-u")
    return ParsedCommand(
        action=action, symbol=symbol, qty=qty,
        order_type="LIMIT" if limit else "MARKET",
        limit_price=float(limit) if limit else None,
        user=user,
    )


_MSGS = {
    "price": [
        "Peeking at the ticker tape…",
        "Bribing the market maker for a quote…",
        "Checking what Mr. Market is feeling today…",
        "Asking the bulls and bears for a price…",
        "Refreshing the Bloomberg terminal…",
        "Scanning the exchange floor…",
        "Waking up the algo for a quote…",
    ],
    "search": [
        "Flipping through the exchange directory…",
        "Scanning 5,000 listed stocks…",
        "Consulting the NSE scripmaster…",
        "Hunting through the exchange listings…",
        "Cross-referencing the watchlist…",
    ],
    "history": [
        "Pulling up the price chart…",
        "Dusting off the historical records…",
        "Rewinding the tape…",
        "Fetching the candlestick data…",
        "Checking what the stock was doing last month…",
        "Loading OHLC data from the vault…",
    ],
    "quote_for_order": [
        "Getting the last traded price…",
        "Locking in the market rate…",
        "Checking the bid-ask spread…",
        "Fetching live quote before order…",
    ],
    "place_order": [
        "Sending order to the exchange…",
        "Routing to the order management system…",
        "Knocking on the exchange's door…",
        "Submitting to the matching engine…",
        "Order flying to Dalal Street…",
    ],
    "portfolio": [
        "Counting your rupees…",
        "Tallying up the holdings…",
        "Checking what you own…",
        "Pulling your demat account…",
        "Asking the custodian for your holdings…",
        "Crunching your portfolio P&L…",
    ],
    "positions": [
        "Scanning today's open positions…",
        "Checking the intraday scoreboard…",
        "Tallying up today's bets…",
        "Fetching your open positions…",
    ],
    "funds": [
        "Checking your war chest…",
        "Counting dry powder…",
        "Checking available margin…",
        "How much ammo do you have left…",
        "Asking the broker what's left in the kitty…",
    ],
    "orders": [
        "Pulling up the order book…",
        "Checking what went through today…",
        "Reviewing today's trade log…",
        "Fetching the order ledger…",
    ],
    "ai": [
        "Reading the ticker tape…",
        "Consulting the algo brain…",
        "Decoding your trade intent…",
        "Running it through the quant…",
        "Parsing your order like a market wizard…",
        "Checking with the trading desk…",
    ],
}


def _spin(action: str) -> str:
    return f"  [dim]{random.choice(_MSGS.get(action, ['Loading…']))}[/dim]"


def _route(text: str):
    """
    Route raw text:
      1. First word matches a known command → run directly, no AI needed.
      2. Otherwise → send to AI layer.
    """
    tokens = text.strip().split()
    if not tokens:
        return

    cmd_name = tokens[0].lower()

    if cmd_name == "list-users":
        users   = config.list_users()
        default = config.get_default_user()
        display.show_users(users, default)
        return

    if cmd_name in _STRUCTURED:
        cmd = _STRUCTURED[cmd_name](tokens)
        _run_command(cmd)
        return

    # Natural language — works if AI key configured, shows message if not
    with console.status(_spin("ai"), spinner="dots"):
        cmd = ai_parse(text)
    _run_command(cmd)


def _resolve_user(user: Optional[str]) -> str:
    return user or config.get_default_user()


def _period_to_dates(period: str) -> tuple[str, str]:
    """Convert period string to (from_date, to_date) for SmartAPI."""
    now  = datetime.now()
    ends = now.strftime("%Y-%m-%d %H:%M")
    delta_map = {
        "1w": timedelta(weeks=1),
        "1m": timedelta(days=30),
        "3m": timedelta(days=90),
        "6m": timedelta(days=180),
        "1y": timedelta(days=365),
    }
    delta = delta_map.get(period, timedelta(days=30))
    start = (now - delta).strftime("%Y-%m-%d %H:%M")
    return start, ends


def _get_broker(user: str, public: bool = False):
    """
    Return the right broker.
    - public=True or no credentials → Yahoo Finance (no login)
    - otherwise → configured broker (Angel One etc.)
    Also returns a label shown in the UI.
    """
    if public or not config.has_credentials(user):
        return config.get_public_broker(), "yahoo · ~15min delay"
    return config.get_broker(user), "live"


def _run_command(cmd: ParsedCommand, public: bool = False):
    """Execute a ParsedCommand — shared between structured CLI and AI router."""
    try:
        _run_command_inner(cmd, public)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")


def _run_command_inner(cmd: ParsedCommand, public: bool = False):
    user = _resolve_user(cmd.user)

    if cmd.action == "answer":
        console.print(cmd.answer or "")
        return

    if cmd.action == "price":
        symbols = cmd.symbols or ([cmd.symbol] if cmd.symbol else [])
        if not symbols:
            console.print("[red]Specify at least one symbol.[/red]")
            return
        with console.status(_spin("price"), spinner="dots"):
            broker, source = _get_broker(user, public)
            quotes = broker.get_quote(symbols)
        display.show_quotes(quotes, source=source)

    elif cmd.action == "search":
        if not cmd.symbol:
            console.print("[red]Specify a search query.[/red]")
            return
        with console.status(_spin("search"), spinner="dots"):
            broker, _ = _get_broker(user, public)
            results = broker.search_instruments(cmd.symbol)
        display.show_instruments(results, cmd.symbol)

    elif cmd.action == "history":
        if not cmd.symbol:
            console.print("[red]Specify a symbol.[/red]")
            return
        from_date, to_date = _period_to_dates(cmd.period)
        with console.status(_spin("history"), spinner="dots"):
            broker, source = _get_broker(user, public)
            candles = broker.get_history(cmd.symbol, cmd.interval, from_date, to_date)
        display.show_history(candles, cmd.symbol, cmd.period, cmd.interval, source=source)

    elif cmd.action in ("buy", "sell"):
        if not cmd.symbol or not cmd.qty:
            console.print("[red]Symbol and quantity are required.[/red]")
            return
        with console.status(_spin("quote_for_order"), spinner="dots"):
            broker = config.get_broker(user)
            quotes = broker.get_quote([cmd.symbol])
        ltp = quotes[0].ltp if quotes else 0.0
        display.show_order_preview(
            action=cmd.action.upper(),
            symbol=cmd.symbol,
            qty=cmd.qty,
            order_type=cmd.order_type,
            ltp=ltp,
            user=user,
            limit_price=cmd.limit_price,
        )
        if not Confirm.ask("Confirm?", default=False):
            console.print("[dim]Cancelled.[/dim]")
            return
        fn = broker.buy if cmd.action == "buy" else broker.sell
        with console.status(_spin("place_order"), spinner="dots"):
            result = fn(
                symbol=cmd.symbol,
                qty=cmd.qty,
                order_type=cmd.order_type,
                price=cmd.limit_price,
            )
        display.show_order_result(result)

    elif cmd.action == "portfolio":
        with console.status(_spin("portfolio"), spinner="dots"):
            broker   = config.get_broker(user)
            holdings = broker.get_portfolio()
        display.show_portfolio(holdings, user)

    elif cmd.action == "positions":
        with console.status(_spin("positions"), spinner="dots"):
            broker    = config.get_broker(user)
            positions = broker.get_positions()
        display.show_positions(positions, user)

    elif cmd.action == "funds":
        with console.status(_spin("funds"), spinner="dots"):
            broker = config.get_broker(user)
            funds  = broker.get_funds()
        display.show_funds(funds, user)

    elif cmd.action == "orders":
        with console.status(_spin("orders"), spinner="dots"):
            broker = config.get_broker(user)
            orders = broker.get_orders()
        display.show_orders(orders, user)

    else:
        console.print(f"[red]Unknown action: {cmd.action}[/red]")


# --------------------------------------------------------- structured commands

@app.command()
def price(
    symbols: list[str] = typer.Argument(..., help="NSE symbols e.g. ITC RELIANCE"),
    public: bool = typer.Option(False, "--public", "-p", help="No login — use Yahoo Finance"),
):
    """Live price for one or more stocks. Works without login (--public or auto)."""
    _run_command(ParsedCommand(action="price", symbols=symbols), public=public)


@app.command()
def search(
    query: list[str] = typer.Argument(..., help="Company name or partial symbol"),
    public: bool = typer.Option(False, "--public", "-p", help="No login — use cached instruments"),
):
    """Search for stocks by name or symbol. Works without login."""
    _run_command(ParsedCommand(action="search", symbol=" ".join(query)), public=public)


@app.command()
def history(
    symbol: str = typer.Argument(...),
    period: str = typer.Option("1m", help="1w | 1m | 3m | 6m | 1y"),
    interval: str = typer.Option("1d", help="1m | 5m | 15m | 1h | 1d"),
    public: bool = typer.Option(False, "--public", "-p", help="No login — use Yahoo Finance"),
):
    """Chart historical price in the terminal. Works without login (--public or auto)."""
    _run_command(ParsedCommand(action="history", symbol=symbol, period=period, interval=interval), public=public)


@app.command()
def buy(
    symbol: str = typer.Argument(...),
    qty: int    = typer.Argument(...),
    limit: Optional[float] = typer.Option(None, "--limit", "-l", help="Limit price"),
    user: Optional[str]   = typer.Option(None, "--user", "-u"),
):
    """Place a buy order."""
    _run_command(ParsedCommand(
        action="buy", symbol=symbol, qty=qty,
        order_type="LIMIT" if limit else "MARKET",
        limit_price=limit, user=user,
    ))


@app.command()
def sell(
    symbol: str = typer.Argument(...),
    qty: int    = typer.Argument(...),
    limit: Optional[float] = typer.Option(None, "--limit", "-l", help="Limit price"),
    user: Optional[str]   = typer.Option(None, "--user", "-u"),
):
    """Place a sell order."""
    _run_command(ParsedCommand(
        action="sell", symbol=symbol, qty=qty,
        order_type="LIMIT" if limit else "MARKET",
        limit_price=limit, user=user,
    ))


@app.command()
def portfolio(user: Optional[str] = typer.Option(None, "--user", "-u")):
    """View holdings and P&L."""
    _run_command(ParsedCommand(action="portfolio", user=user))


@app.command()
def positions(user: Optional[str] = typer.Option(None, "--user", "-u")):
    """View intraday open positions."""
    _run_command(ParsedCommand(action="positions", user=user))


@app.command()
def funds(user: Optional[str] = typer.Option(None, "--user", "-u")):
    """View available funds and margin."""
    _run_command(ParsedCommand(action="funds", user=user))


@app.command()
def orders(user: Optional[str] = typer.Option(None, "--user", "-u")):
    """View today's order book."""
    _run_command(ParsedCommand(action="orders", user=user))


@app.command(name="list-users")
def list_users():
    """Show all configured user profiles."""
    users   = config.list_users()
    default = config.get_default_user()
    display.show_users(users, default)


# --------------------------------------------------------- catch-all NL router

@app.callback(invoke_without_command=True)
def _catch_all(
    ctx: typer.Context,
    query: Optional[list[str]] = typer.Argument(None),
):
    """
    No args → animated splash + interactive REPL.
    Unrecognised args → AI natural language router.
    """
    if ctx.invoked_subcommand is not None:
        return

    if not query:
        # launch interactive session
        _splash()
        _repl()
        return

    # single-shot natural language command
    _route(" ".join(query))
