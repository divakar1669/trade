"""
All terminal rendering — Rich tables + plotext charts.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box
from rich.text import Text

from .brokers.base import (
    Candle, Funds, Holding, Instrument,
    Order, OrderResult, Position, Quote,
)

console = Console()


# ------------------------------------------------------------------ helpers

def _fmt_price(v: float) -> str:
    return f"₹ {v:,.2f}"


def _fmt_change(v: float, pct: float) -> Text:
    arrow = "▲" if v >= 0 else "▼"
    color = "green" if v >= 0 else "red"
    return Text(f"{arrow} {pct:+.2f}%", style=color)


def _pnl_text(pnl: float, pct: Optional[float] = None) -> Text:
    color = "green" if pnl >= 0 else "red"
    sign  = "+" if pnl >= 0 else ""
    txt   = f"{sign}₹ {abs(pnl):,.0f}"
    if pct is not None:
        txt += f"  {sign}{abs(pct):.2f}%"
    return Text(txt, style=color)


# ------------------------------------------------------------------ quotes

def show_quotes(quotes: list[Quote], **_):
    if len(quotes) == 1:
        q = quotes[0]
        console.print(
            f"[bold]{q.symbol}[/bold]   [cyan]{_fmt_price(q.ltp)}[/cyan]   ",
            _fmt_change(q.change, q.change_pct),
            f"   Vol: {q.volume:,}",
        )
        return

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    table.add_column("Symbol",  style="bold")
    table.add_column("LTP",     justify="right")
    table.add_column("Change",  justify="right")
    table.add_column("Volume",  justify="right")

    for q in quotes:
        table.add_row(
            q.symbol,
            _fmt_price(q.ltp),
            _fmt_change(q.change, q.change_pct),
            f"{q.volume:,}",
        )
    console.print(table)


# ------------------------------------------------------------------ search

def show_instruments(results: list[Instrument], query: str):
    if not results:
        console.print(f"[yellow]No results for '{query}'[/yellow]")
        return

    table = Table(box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Symbol", style="bold")
    table.add_column("Name")
    table.add_column("Exchange")

    for inst in results:
        table.add_row(inst.symbol, inst.name, inst.exchange)
    console.print(table)


# ------------------------------------------------------------------ history

def show_history(candles: list[Candle], symbol: str, period: str, interval: str, **_):
    if not candles:
        console.print("[yellow]No historical data found.[/yellow]")
        return

    try:
        import plotext as plt
    except ImportError:
        console.print("[yellow]Install plotext for charts: pip install plotext[/yellow]")
        _show_history_table(candles, symbol)
        return

    closes = [c.close for c in candles]
    labels = [c.timestamp.strftime("%d %b") for c in candles]

    plt.clear_figure()
    plt.theme("dark")
    plt.plot(closes, color="cyan")
    plt.title(f"{symbol} — {period.upper()} ({interval})")
    plt.xlabel("Date")
    plt.ylabel("Price (₹)")

    # Show only ~6 x-axis labels
    step = max(1, len(labels) // 6)
    plt.xticks(list(range(0, len(labels), step)), labels[::step])
    plt.show()

    # Summary below chart
    first, last = candles[0], candles[-1]
    high  = max(c.high  for c in candles)
    low   = min(c.low   for c in candles)
    chg   = last.close - first.open
    chg_p = (chg / first.open * 100) if first.open else 0
    sign  = "+" if chg >= 0 else ""
    color = "green" if chg >= 0 else "red"

    console.print(
        f"Open [cyan]{_fmt_price(first.open)}[/cyan]  "
        f"High [cyan]{_fmt_price(high)}[/cyan]  "
        f"Low [cyan]{_fmt_price(low)}[/cyan]  "
        f"Close [cyan]{_fmt_price(last.close)}[/cyan]  "
        f"Change [{color}]{sign}{chg_p:.2f}%[/{color}]"
    )


def _show_history_table(candles: list[Candle], symbol: str):
    table = Table(title=symbol, box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Date")
    table.add_column("Open",  justify="right")
    table.add_column("High",  justify="right")
    table.add_column("Low",   justify="right")
    table.add_column("Close", justify="right")
    table.add_column("Volume",justify="right")
    for c in candles[-20:]:
        table.add_row(
            c.timestamp.strftime("%d %b %Y"),
            _fmt_price(c.open),
            _fmt_price(c.high),
            _fmt_price(c.low),
            _fmt_price(c.close),
            f"{c.volume:,}",
        )
    console.print(table)


# ---------------------------------------------------------------- portfolio

def show_portfolio(holdings: list[Holding], user: str):
    if not holdings:
        console.print(f"[yellow]No holdings found for {user}.[/yellow]")
        return

    table = Table(
        title=f"Portfolio — {user}   [dim]{datetime.now().strftime('%d %b %Y')}[/dim]",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Symbol",   style="bold")
    table.add_column("Qty",      justify="right")
    table.add_column("Avg Cost", justify="right")
    table.add_column("LTP",      justify="right")
    table.add_column("P&L",      justify="right")
    table.add_column("Return",   justify="right")

    total_invested = 0.0
    total_current  = 0.0

    for h in holdings:
        table.add_row(
            h.symbol,
            str(h.qty),
            _fmt_price(h.avg_cost),
            _fmt_price(h.ltp),
            _pnl_text(h.pnl),
            _pnl_text(h.pnl_pct),
        )
        total_invested += h.invested_value
        total_current  += h.current_value

    table.add_section()
    total_pnl = total_current - total_invested
    total_pct = (total_pnl / total_invested * 100) if total_invested else 0
    table.add_row(
        "[bold]TOTAL[/bold]", "", "",
        f"[bold]{_fmt_price(total_current)}[/bold]",
        _pnl_text(total_pnl),
        _pnl_text(total_pct),
    )
    console.print(table)


# --------------------------------------------------------------- positions

def show_positions(positions: list[Position], user: str):
    if not positions:
        console.print(f"[yellow]No open positions for {user}.[/yellow]")
        return

    table = Table(
        title=f"Intraday Positions — {user}",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Symbol",      style="bold")
    table.add_column("Qty",         justify="right")
    table.add_column("Entry",       justify="right")
    table.add_column("LTP",         justify="right")
    table.add_column("P&L",         justify="right")

    total_pnl = 0.0
    for p in positions:
        table.add_row(
            p.symbol, str(p.qty),
            _fmt_price(p.entry_price),
            _fmt_price(p.ltp),
            _pnl_text(p.pnl),
        )
        total_pnl += p.pnl

    table.add_section()
    table.add_row("[bold]Day P&L[/bold]", "", "", "", _pnl_text(total_pnl))
    console.print(table)


# ------------------------------------------------------------------ funds

def show_funds(funds: Funds, user: str):
    table = Table(title=f"Funds — {user}", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("", style="bold")
    table.add_column("Amount", justify="right")
    table.add_row("Available Cash", _fmt_price(funds.available_cash))
    table.add_row("Used Margin",    _fmt_price(funds.used_margin))
    table.add_row("Net Available",  f"[cyan]{_fmt_price(funds.net_available)}[/cyan]")
    console.print(table)


# ------------------------------------------------------------------ orders

def show_orders(orders: list[Order], user: str):
    if not orders:
        console.print(f"[yellow]No orders today for {user}.[/yellow]")
        return

    table = Table(
        title=f"Orders Today — {user}",
        box=box.SIMPLE_HEAVY,
        header_style="bold cyan",
    )
    table.add_column("Order ID")
    table.add_column("Symbol",  style="bold")
    table.add_column("Action",  justify="center")
    table.add_column("Qty",     justify="right")
    table.add_column("Type",    justify="center")
    table.add_column("Status",  justify="center")

    for o in orders:
        action_style = "green" if o.action == "BUY" else "red"
        status_style = "green" if o.status == "COMPLETE" else (
            "yellow" if o.status == "PENDING" else "dim"
        )
        table.add_row(
            o.order_id,
            o.symbol,
            Text(o.action, style=action_style),
            str(o.qty),
            o.order_type,
            Text(o.status, style=status_style),
        )
    console.print(table)


# ----------------------------------------------------------- order preview

def show_order_preview(
    action: str,
    symbol: str,
    qty: int,
    order_type: str,
    ltp: float,
    user: str,
    limit_price: Optional[float] = None,
):
    price_str = (
        f"LIMIT @ {_fmt_price(limit_price)}"
        if order_type == "LIMIT" and limit_price
        else "MARKET"
    )
    estimated = (limit_price or ltp) * qty

    table = Table(title="Order Preview", box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("Field", style="dim")
    table.add_column("Value", style="bold")
    table.add_row("Stock",  symbol)
    table.add_row("Action", Text(action, style="green" if action == "BUY" else "red"))
    table.add_row("Qty",    str(qty))
    table.add_row("Type",   price_str)
    table.add_row("LTP",    _fmt_price(ltp))
    table.add_row("Est.",   f"[cyan]{_fmt_price(estimated)}[/cyan]")
    table.add_row("User",   user)
    console.print(table)


def show_order_result(result: OrderResult):
    console.print(
        f"[green]✓ Order placed[/green] — Order ID: [bold]{result.order_id}[/bold]"
    )


# ------------------------------------------------------------ list users

def show_users(users: list[str], default: str):
    table = Table(title="Users", box=box.SIMPLE_HEAVY, header_style="bold cyan")
    table.add_column("Name", style="bold")
    table.add_column("Status")

    for u in users:
        status = "[green]✓ default[/green]" if u == default else ""
        table.add_row(u, status)
    console.print(table)
