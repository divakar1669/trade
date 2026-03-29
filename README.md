# trade-cli

A multi-user stock trading CLI for Angel One with AI-powered natural language support.
Works without an AI key — all structured commands run instantly with no API calls.

```
  ███████╗██████╗  █████╗ ██████╗ ███████╗
     ██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝
     ██║   ██████╔╝███████║██║  ██║█████╗
     ██║   ██╔══██╗██╔══██║██║  ██║██╔══╝
     ██║   ██║  ██║██║  ██║██████╔╝███████╗
     ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚══════╝

  Angel One  |  AI-powered trading   v0.1.0
```

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Credentials Setup](#credentials-setup)
3. [Using the App](#using-the-app)
4. [Command Reference](#command-reference)
5. [Natural Language Examples](#natural-language-examples)
6. [Public Mode — No Login](#public-mode--no-login)
7. [Adding a New User](#adding-a-new-user)
8. [Adding a New Broker](#adding-a-new-broker)
9. [Technical Architecture](#technical-architecture)
10. [File Reference](#file-reference)

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/divakar1669/trade
cd trade

# 2. Run setup once — installs everything, wires up the 'trade' command
bash setup.sh

# 3. Reload shell
source ~/.bashrc

# 4. Open the app
trade
```

That's it. `setup.sh` handles Python deps, config directory, and the bash function automatically on any machine.

---

## Credentials Setup

All secrets live in `~/.trade-cli/.env` — never inside the repo.

```bash
# Location
~/.trade-cli/.env          # Linux / macOS / Git Bash
C:\Users\<you>\.trade-cli\.env   # Windows
```

```env
# AI layer — optional, enables natural language commands
CLAUDE_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # fallback if no Claude key

# Default user when --user is not specified
DEFAULT_USER=me

# ── me ──────────────────────────────────────────────────
ME_BROKER=angelone
ME_CLIENT_ID=AXXX123           # Angel One Client ID
ME_API_KEY=your-api-key        # from smartapi.angelbroking.com
ME_PASSWORD=your-password      # trading password
ME_TOTP_SECRET=BASE32SECRET    # from authenticator app setup

# ── dad ─────────────────────────────────────────────────
DAD_BROKER=angelone
DAD_CLIENT_ID=BYYY456
DAD_API_KEY=...
DAD_PASSWORD=...
DAD_TOTP_SECRET=...
```

### Where to get Angel One credentials

1. Log in to [smartapi.angelbroking.com](https://smartapi.angelbroking.com)
2. Create an app → copy the **API Key**
3. **Client ID** — your Angel One login ID
4. **Password** — your Angel One trading password
5. **TOTP Secret** — when setting up 2FA in Angel One, save the Base32 secret string (the one behind the QR code)

---

## Using the App

Type `trade` to open the interactive session:

```
  ███████╗██████╗  █████╗ ██████╗ ███████╗
     ██╔══╝...
  ────────────────────────────────────────
  Angel One  |  AI-powered trading   v0.1.0

  Type a command or ask anything in plain English.

  > _
```

Inside the session, type any command or ask in plain English. Every action shows a rotating finance-themed loading message while it runs.

### Exiting

Any of these close the session:

```
> exit      > quit      > q      > :q      > close      Ctrl+C
```

### Getting help inside the app

```
> ?
> help
```

---

## Command Reference

All commands work both inside the interactive session and directly from the shell:

```bash
trade price ITC           # from shell
# or
> price ITC               # inside the app
```

---

### `price`

Live last-traded price. Works without login — uses Yahoo Finance if no credentials.

```bash
price <SYMBOL> [SYMBOL ...] [--public]
```

```
> price ITC

ITC    ₹ 452.30   ▲ +1.20%   Vol: 2,34,512   (live)
```

```
> price ITC RELIANCE HDFCBANK

Symbol       LTP            Change       Volume
──────────────────────────────────────────────────   (yahoo · ~15min delay)
ITC          ₹   452.30    ▲ +1.20%     2,34,512
RELIANCE     ₹ 2,891.00    ▼ -0.40%     1,12,300
HDFCBANK     ₹ 1,678.50    ▲ +0.80%       98,450
```

---

### `search`

Search stocks by company name or partial symbol. Works without login.

```bash
search <query>
```

```
> search spandana

Symbol          Name                              Exchange
──────────────────────────────────────────────────────────
SPANDANASPH     Spandana Sphoorty Financial Ltd   NSE
SPANDANAFIN     Spandana Finance Ltd              BSE
```

```
> search reliance

Symbol       Name                              Exchange
────────────────────────────────────────────────────────
RELIANCE     Reliance Industries Limited       NSE
RELINFRA     Reliance Infrastructure Limited   BSE
RCOM         Reliance Communications Limited   BSE
```

---

### `history`

ASCII price chart in the terminal. Works without login.

```bash
history <SYMBOL> [--period 1m] [--interval 1d]
```

| Option | Values | Default |
|--------|--------|---------|
| `--period` | `1w` `1m` `3m` `6m` `1y` | `1m` |
| `--interval` | `1m` `5m` `15m` `1h` `1d` | `1d` |

```
> history ITC --period 1m

ITC — 1M (1d)  [live]
₹ 480 ┤                                    ╭─╮
₹ 470 ┤                          ╭──╮    ╭─╯ │
₹ 460 ┤              ╭─╮        ╭╯  ╰────╯   ╰
₹ 450 ┤          ╭───╯ ╰──╮   ╭╯
₹ 440 ┤      ╭───╯        ╰───╮╯
₹ 430 ┼──────╯
       Mar 1          Mar 15          Mar 28

Open ₹431.00   High ₹478.50   Low ₹429.00   Close ₹452.30   Change +4.90%
```

---

### `buy`

Place a buy order. Requires login.

```bash
buy <SYMBOL> <QTY> [--limit PRICE] [--user NAME]
```

```
> buy ITC 10

  Locking in the market rate…

┌─ Order Preview ─────────────┐
│ Stock    ITC                │
│ Action   BUY                │
│ Qty      10                 │
│ Type     MARKET             │
│ LTP      ₹ 452.30           │
│ Est.     ₹ 4,523.00         │
│ User     me                 │
└─────────────────────────────┘
Confirm? [y/N]: y

  Order flying to Dalal Street…

✓ Order placed — Order ID: 12345678
```

```
> buy ITC 10 --limit 445 --user dad
> sell RELIANCE 5 --user mom
> sell HDFCBANK 3 --limit 1800
```

---

### `portfolio`

Holdings and P&L. Requires login.

```bash
portfolio [--user NAME]
```

```
> portfolio

  Counting your rupees…

Portfolio — me                                     28 Mar 2026
──────────────────────────────────────────────────────────────────
Symbol       Qty    Avg Cost      LTP          P&L          Return
──────────────────────────────────────────────────────────────────
ITC           50    ₹   420.00   ₹   452.30   +₹  1,615    +7.69%
RELIANCE      10    ₹ 2,750.00   ₹ 2,891.00   +₹  1,410    +5.13%
HDFCBANK      15    ₹ 1,700.00   ₹ 1,678.50    -₹    322   -1.26%
INFY          20    ₹ 1,500.00   ₹ 1,423.75    -₹  1,525   -5.08%
──────────────────────────────────────────────────────────────────
TOTAL                            ₹ 1,23,678   +₹  1,178    +0.96%
```

---

### `positions`

Intraday open positions. Requires login.

```bash
positions [--user NAME]
```

```
> positions

  Checking the intraday scoreboard…

Intraday Positions — me
──────────────────────────────────────────────────
Symbol       Qty    Entry         LTP         P&L
──────────────────────────────────────────────────
ITC           10    ₹   450.00   ₹  452.30   +₹  23
INFY           5    ₹ 1,430.00   ₹ 1,423.75   -₹  31
──────────────────────────────────────────────────
Day P&L                                       -₹   8
```

---

### `funds`

Available cash and margin. Requires login.

```bash
funds [--user NAME]
```

```
> funds --user mom

  Counting dry powder…

Funds — mom
──────────────────────────────────
Available Cash     ₹ 45,230.00
Used Margin        ₹ 12,400.00
Net Available      ₹ 32,830.00
```

---

### `orders`

Today's order book. Requires login.

```bash
orders [--user NAME]
```

```
> orders

  Pulling up the order book…

Orders Today — me
───────────────────────────────────────────────────────────────────
Order ID     Symbol       Action    Qty    Type      Status
───────────────────────────────────────────────────────────────────
12345678     ITC          BUY        10    MARKET    COMPLETE
87654321     ITC          BUY        10    LIMIT     PENDING
99887766     RELIANCE     SELL        5    MARKET    COMPLETE
```

---

### `list-users`

All configured user profiles.

```
> list-users

Users
──────────────────────────
me        ✓ default
dad
mom
```

---

## Natural Language Examples

Add a `CLAUDE_API_KEY` or `OPENAI_API_KEY` to `.env` and type anything naturally. No special prefix needed.

| What you type | What happens |
|---------------|--------------|
| `buy 10 ITC from dad` | BUY ITC × 10 from dad's account |
| `sell all my Reliance` | Looks up your qty, places SELL |
| `buy Spandana Sphoorty 15` | Resolves name → SPANDANASPH, places BUY |
| `how is my portfolio doing` | Summarises P&L in plain English |
| `which of dad's stocks are in loss` | Filters dad's holdings by P&L |
| `do I have enough to buy 10 RELIANCE` | Checks funds vs estimated cost |
| `show INFY history for 6 months` | Runs `history INFY --period 6m` |
| `what's the price of HDFC Bank` | Resolves name → HDFCBANK, shows LTP |

**Confirmation is always shown before any order executes.**

Without an AI key, natural language shows a friendly message and structured commands still work fully.

---

## Public Mode — No Login

`price`, `search`, and `history` work without any Angel One credentials using Yahoo Finance (~15 min delayed data).

```bash
> price ITC                    # auto-detects no creds → uses Yahoo
> search reliance              # searches NSE/BSE listings
> history ITC --period 3m      # full chart, no login

# force public mode even if logged in
> price ITC --public
> history RELIANCE --period 1y --public
```

The data source is shown on every result: `(live)` or `(yahoo · ~15min delay)`.

---

## Adding a New User

Open `~/.trade-cli/.env` and add 5 lines:

```env
SPOUSE_BROKER=angelone
SPOUSE_CLIENT_ID=DXXX000
SPOUSE_API_KEY=...
SPOUSE_PASSWORD=...
SPOUSE_TOTP_SECRET=...
```

No code changes. The tool auto-discovers any profile with a `_CLIENT_ID` key.

```
> list-users
# me  dad  mom  spouse  ← spouse appears immediately

> portfolio --user spouse
> buy ITC 5 --user spouse
```

---

## Adding a New Broker

### Step 1 — Implement the interface

Create `trade/brokers/zerodha.py`:

```python
from .base import BaseBroker, Quote, Holding, OrderResult, ...

class ZerodhaBroker(BaseBroker):

    def login(self, credentials: dict) -> None:
        ...

    def get_quote(self, symbols: list[str]) -> list[Quote]:
        ...

    def buy(self, symbol, qty, order_type, price, product) -> OrderResult:
        ...

    # implement all other abstract methods from BaseBroker
```

### Step 2 — Register it

In `trade/brokers/__init__.py`:

```python
from .zerodha import ZerodhaBroker

BROKER_REGISTRY = {
    "angelone": AngelOneBroker,
    "zerodha":  ZerodhaBroker,
}
```

### Step 3 — Use it in `.env`

```env
DAD_BROKER=zerodha
DAD_CLIENT_ID=...
DAD_API_KEY=...
```

No other code changes needed.

---

## Technical Architecture

```
User types:  "buy spandana sphoorty 15 from dad"
                        │
                    cli.py
                        │
           first word = known command?
                        │
          YES ──────────┘──────────── NO
           │                           │
    run directly                    ai.py
    (no AI call)             Claude / OpenAI
                             function calling
                                       │
                              ParsedCommand {
                                action: "buy",
                                symbol: "SPANDANASPH",
                                qty: 15,
                                user: "dad"
                              }
                                       │
                              ─────────┴─────────
                                       │
                                  config.py
                             loads dad's creds
                           from ~/.trade-cli/.env
                                       │
                               broker login
                             (TOTP auto-generated)
                                       │
                             Angel One SmartAPI
                              places the order
                                       │
                                  display.py
                               Rich table output
```

### Smart router

Known first words (`price`, `buy`, `sell`, `portfolio`, etc.) execute directly — zero AI API calls, instant response. Everything else goes to the AI layer.

### User discovery

`config.py` scans `.env` for keys ending in `_CLIENT_ID`. The prefix becomes the user name — `DAD_CLIENT_ID` → user `dad`. No registration, no database.

### AI layer

Uses Claude / OpenAI **function/tool calling** — the model is forced to return structured JSON, never free text. Result is always a typed `ParsedCommand` object. AI key is optional — without it, structured commands work fully.

### Broker abstraction

All brokers implement `BaseBroker` from `trade/brokers/base.py`. The CLI, AI, config, and display layers have zero knowledge of Angel One, Zerodha, or any other broker. Adding a new broker requires touching exactly 2 files.

---

## File Reference

| File | Purpose |
|------|---------|
| `setup.sh` | One-time setup — installs deps, creates config dir, wires `trade` command |
| `trade/__main__.py` | Entry point — runs splash + REPL or passes args to Typer |
| `trade/cli.py` | All commands, smart router, REPL, splash, help |
| `trade/config.py` | Loads `~/.trade-cli/.env`, discovers users, returns broker instances |
| `trade/ai.py` | Natural language → `ParsedCommand` via Claude / OpenAI tool calling |
| `trade/display.py` | All terminal output — Rich tables, plotext ASCII charts |
| `trade/brokers/base.py` | `BaseBroker` interface + shared dataclasses |
| `trade/brokers/angelone.py` | Angel One implementation via SmartAPI |
| `trade/brokers/yahoo.py` | Yahoo Finance — public data, no login required |
| `trade/brokers/__init__.py` | `BROKER_REGISTRY` — maps names to broker classes |
| `~/.trade-cli/.env` | All secrets — never committed |
| `~/.trade-cli/tokens/` | Session token cache per user — auto-managed |
| `pyproject.toml` | Package definition and dependencies |
