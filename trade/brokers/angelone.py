"""
Angel One broker implementation using SmartAPI.
"""
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import httpx
import pyotp

from .base import (
    BaseBroker, Candle, Funds, Holding, Instrument,
    Order, OrderResult, Position, Quote,
)

INSTRUMENT_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
INSTRUMENT_CACHE = Path.home() / ".trade-cli" / "angelone_instruments.json"
CACHE_TTL_HOURS = 12

# Map user-facing interval strings → SmartAPI interval strings
INTERVAL_MAP = {
    "1m":  "ONE_MINUTE",
    "5m":  "FIVE_MINUTE",
    "15m": "FIFTEEN_MINUTE",
    "30m": "THIRTY_MINUTE",
    "1h":  "ONE_HOUR",
    "1d":  "ONE_DAY",
    "1w":  "ONE_WEEK",
    "1mo": "ONE_MONTH",
}


class AngelOneBroker(BaseBroker):
    def __init__(self):
        self._client = None
        self._instruments: list[dict] = []

    # ------------------------------------------------------------------ auth

    def login(self, credentials: dict) -> None:
        from SmartApi import SmartConnect  # lazy import

        api_key     = credentials["api_key"]
        client_id   = credentials["client_id"]
        password    = credentials["password"]
        totp_secret = credentials["totp_secret"]

        self._client = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()
        resp = self._client.generateSession(client_id, password, totp)

        if not resp.get("status"):
            raise RuntimeError(f"Angel One login failed: {resp.get('message')}")

        self._load_instruments()

    # ----------------------------------------------------------- instruments

    def _load_instruments(self):
        """Download + cache the full NSE/BSE instrument list."""
        if INSTRUMENT_CACHE.exists():
            age = time.time() - INSTRUMENT_CACHE.stat().st_mtime
            if age < CACHE_TTL_HOURS * 3600:
                with open(INSTRUMENT_CACHE) as f:
                    self._instruments = json.load(f)
                return

        resp = httpx.get(INSTRUMENT_URL, timeout=30)
        resp.raise_for_status()
        self._instruments = resp.json()
        INSTRUMENT_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(INSTRUMENT_CACHE, "w") as f:
            json.dump(self._instruments, f)

    def _find_instrument(self, symbol: str, exchange: str = "NSE") -> Optional[dict]:
        symbol = symbol.upper()
        for inst in self._instruments:
            if inst.get("symbol") == symbol and inst.get("exch_seg") == exchange:
                return inst
        return None

    def search_instruments(self, query: str) -> list[Instrument]:
        query = query.upper()
        results = []
        seen = set()
        for inst in self._instruments:
            sym  = inst.get("symbol", "")
            name = inst.get("name", "")
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

    # --------------------------------------------------------------- quotes

    def get_quote(self, symbols: list[str]) -> list[Quote]:
        quotes = []
        for symbol in symbols:
            inst = self._find_instrument(symbol)
            if not inst:
                continue
            try:
                data = self._client.ltpData("NSE", symbol, inst["token"])
                d = data.get("data", {})
                ltp   = float(d.get("ltp", 0))
                close = float(d.get("close", ltp))
                change = ltp - close
                change_pct = (change / close * 100) if close else 0
                quotes.append(Quote(
                    symbol=symbol,
                    ltp=ltp,
                    change=change,
                    change_pct=change_pct,
                    volume=int(d.get("tradedQty", 0)),
                    open=float(d.get("open", 0)),
                    high=float(d.get("high", 0)),
                    low=float(d.get("low", 0)),
                    close=close,
                ))
            except Exception:
                continue
        return quotes

    # --------------------------------------------------------------- history

    def get_history(
        self,
        symbol: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[Candle]:
        inst = self._find_instrument(symbol)
        if not inst:
            raise ValueError(f"Symbol not found: {symbol}")

        smartapi_interval = INTERVAL_MAP.get(interval, "ONE_DAY")
        params = {
            "exchange":    "NSE",
            "symboltoken": inst["token"],
            "interval":    smartapi_interval,
            "fromdate":    from_date,
            "todate":      to_date,
        }
        resp = self._client.getCandleData(params)
        candles = []
        for row in resp.get("data", []):
            # row = [timestamp, open, high, low, close, volume]
            ts = datetime.strptime(row[0][:19], "%Y-%m-%dT%H:%M:%S")
            candles.append(Candle(
                timestamp=ts,
                open=float(row[1]),
                high=float(row[2]),
                low=float(row[3]),
                close=float(row[4]),
                volume=int(row[5]),
            ))
        return candles

    # --------------------------------------------------------------- trading

    def _place_order(
        self,
        symbol: str,
        qty: int,
        transaction_type: str,
        order_type: str,
        price: Optional[float],
        product: str,
    ) -> OrderResult:
        inst = self._find_instrument(symbol)
        if not inst:
            raise ValueError(f"Symbol not found: {symbol}")

        order_params = {
            "variety":         "NORMAL",
            "tradingsymbol":   symbol,
            "symboltoken":     inst["token"],
            "transactiontype": transaction_type,
            "exchange":        "NSE",
            "ordertype":       order_type,
            "producttype":     product,
            "duration":        "DAY",
            "price":           str(price) if price else "0",
            "squareoff":       "0",
            "stoploss":        "0",
            "quantity":        str(qty),
        }
        resp = self._client.placeOrder(order_params)
        return OrderResult(
            order_id=str(resp),
            status="PLACED",
            symbol=symbol,
            qty=qty,
            action=transaction_type,
            order_type=order_type,
            price=price,
        )

    def buy(self, symbol, qty, order_type="MARKET", price=None, product="DELIVERY"):
        return self._place_order(symbol, qty, "BUY", order_type.upper(), price, product)

    def sell(self, symbol, qty, order_type="MARKET", price=None, product="DELIVERY"):
        return self._place_order(symbol, qty, "SELL", order_type.upper(), price, product)

    # --------------------------------------------------------------- account

    def get_portfolio(self) -> list[Holding]:
        resp = self._client.holding()
        holdings = []
        for h in resp.get("data", []) or []:
            qty         = int(h.get("quantity", 0))
            avg_cost    = float(h.get("averageprice", 0))
            ltp         = float(h.get("ltp", 0))
            invested    = qty * avg_cost
            current     = qty * ltp
            pnl         = current - invested
            pnl_pct     = (pnl / invested * 100) if invested else 0
            holdings.append(Holding(
                symbol=h.get("tradingsymbol", ""),
                qty=qty,
                avg_cost=avg_cost,
                ltp=ltp,
                pnl=pnl,
                pnl_pct=pnl_pct,
                current_value=current,
                invested_value=invested,
            ))
        return holdings

    def get_positions(self) -> list[Position]:
        resp = self._client.position()
        positions = []
        for p in resp.get("data", []) or []:
            qty = int(p.get("netqty", 0))
            if qty == 0:
                continue
            entry = float(p.get("netprice", 0))
            ltp   = float(p.get("ltp", 0))
            pnl   = float(p.get("unrealised", 0))
            positions.append(Position(
                symbol=p.get("tradingsymbol", ""),
                qty=qty,
                entry_price=entry,
                ltp=ltp,
                pnl=pnl,
                product=p.get("producttype", ""),
            ))
        return positions

    def get_funds(self) -> Funds:
        resp = self._client.rmsLimit()
        data = resp.get("data", {}) or {}
        return Funds(
            available_cash=float(data.get("availablecash", 0)),
            used_margin=float(data.get("utiliseddebits", 0)),
            net_available=float(data.get("net", 0)),
        )

    def get_orders(self) -> list[Order]:
        resp = self._client.orderBook()
        orders = []
        for o in resp.get("data", []) or []:
            orders.append(Order(
                order_id=o.get("orderid", ""),
                symbol=o.get("tradingsymbol", ""),
                action=o.get("transactiontype", ""),
                qty=int(o.get("quantity", 0)),
                order_type=o.get("ordertype", ""),
                status=o.get("status", ""),
                price=float(o.get("price", 0)) or None,
            ))
        return orders
