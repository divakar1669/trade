"""
Yahoo Finance broker — read-only, no login required.
Uses the yfinance library. Prices are ~15 min delayed.

Covers: get_quote, get_history, search_instruments.
All trade/account methods raise NotImplementedError.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .base import (
    BaseBroker, Candle, Funds, Holding, Instrument,
    Order, OrderResult, Position, Quote,
)

# NSE suffix for Yahoo Finance symbols
_NSE = ".NS"
_BSE = ".BO"

# Map our interval strings → yfinance interval strings
_INTERVAL_MAP = {
    "1m":  "1m",
    "5m":  "5m",
    "15m": "15m",
    "30m": "30m",
    "1h":  "1h",
    "1d":  "1d",
    "1w":  "1wk",
    "1mo": "1mo",
}

# Map our period strings → yfinance period strings
_PERIOD_MAP = {
    "1w": "5d",
    "1m": "1mo",
    "3m": "3mo",
    "6m": "6mo",
    "1y": "1y",
}

# Cached instrument list from Angel One (if available) — used for search
_AO_CACHE = Path.home() / ".trade" / "angelone_instruments.json"


class YahooFinanceBroker(BaseBroker):
    """
    Public market data via Yahoo Finance.
    No credentials or login required.
    """

    def login(self, credentials: dict) -> None:
        # No-op — Yahoo Finance needs no auth
        pass

    # ---------------------------------------------------------------- quote

    def get_quote(self, symbols: list[str]) -> list[Quote]:
        import yfinance as yf

        tickers = yf.Tickers(" ".join(f"{s}{_NSE}" for s in symbols))
        quotes  = []

        for symbol in symbols:
            try:
                info  = tickers.tickers[f"{symbol}{_NSE}"].fast_info
                ltp   = float(info.last_price or 0)
                prev  = float(info.previous_close or ltp)
                chg   = ltp - prev
                chgp  = (chg / prev * 100) if prev else 0
                vol   = int(info.three_month_average_volume or 0)
                quotes.append(Quote(
                    symbol=symbol,
                    ltp=ltp,
                    change=chg,
                    change_pct=chgp,
                    volume=vol,
                ))
            except Exception:
                continue

        return quotes

    # -------------------------------------------------------------- history

    def get_history(
        self,
        symbol: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[Candle]:
        import yfinance as yf

        # yfinance works better with period strings than explicit dates
        # We derive period from the date range width
        from_dt = datetime.strptime(from_date[:10], "%Y-%m-%d")
        to_dt   = datetime.strptime(to_date[:10],   "%Y-%m-%d")
        days    = (to_dt - from_dt).days

        if   days <= 7:   yf_period = "5d"
        elif days <= 30:  yf_period = "1mo"
        elif days <= 90:  yf_period = "3mo"
        elif days <= 180: yf_period = "6mo"
        else:             yf_period = "1y"

        yf_interval = _INTERVAL_MAP.get(interval, "1d")

        ticker = yf.Ticker(f"{symbol}{_NSE}")
        df     = ticker.history(period=yf_period, interval=yf_interval)

        candles = []
        for ts, row in df.iterrows():
            candles.append(Candle(
                timestamp=ts.to_pydatetime().replace(tzinfo=None),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            ))
        return candles

    # ------------------------------------------------------------- search

    def search_instruments(self, query: str) -> list[Instrument]:
        """
        Search using cached Angel One instrument list if available,
        otherwise fall back to a yfinance lookup.
        """
        # Try local cache first (fast, offline)
        if _AO_CACHE.exists():
            return self._search_cache(query)

        # Fallback: yfinance search
        return self._search_yfinance(query)

    def _search_cache(self, query: str) -> list[Instrument]:
        with open(_AO_CACHE) as f:
            instruments = json.load(f)

        query = query.upper()
        results, seen = [], set()
        for inst in instruments:
            sym  = inst.get("symbol", "")
            name = inst.get("name",   "")
            exch = inst.get("exch_seg", "")
            if exch not in ("NSE", "BSE"):
                continue
            if query in sym or query in name.upper():
                key = sym + exch
                if key not in seen:
                    seen.add(key)
                    results.append(Instrument(
                        symbol=sym,
                        name=name,
                        exchange=exch,
                        token=inst.get("token", ""),
                    ))
        return results[:20]

    def _search_yfinance(self, query: str) -> list[Instrument]:
        try:
            from yfinance import Search
            quotes = Search(query, max_results=20).quotes
            results, seen = [], set()
            for r in quotes:
                sym  = r.get("symbol", "")
                exch = r.get("exchDisp", "")
                name = r.get("longname") or r.get("shortname", "")

                if sym.endswith(_NSE):
                    clean, exchange = sym[:-len(_NSE)], "NSE"
                elif sym.endswith(_BSE):
                    clean, exchange = sym[:-len(_BSE)], "BSE"
                else:
                    continue

                key = clean + exchange
                if key not in seen:
                    seen.add(key)
                    results.append(Instrument(
                        symbol=clean,
                        name=name,
                        exchange=exchange,
                        token="",
                    ))
            return results
        except Exception:
            return []

    # --------- trade operations — not supported in public mode -----------

    def buy(self, *a, **kw) -> OrderResult:
        raise NotImplementedError("Login required to place orders.")

    def sell(self, *a, **kw) -> OrderResult:
        raise NotImplementedError("Login required to place orders.")

    def get_portfolio(self) -> list[Holding]:
        raise NotImplementedError("Login required to view portfolio.")

    def get_positions(self) -> list[Position]:
        raise NotImplementedError("Login required to view positions.")

    def get_funds(self) -> Funds:
        raise NotImplementedError("Login required to view funds.")

    def get_orders(self) -> list[Order]:
        raise NotImplementedError("Login required to view orders.")
