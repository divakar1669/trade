"""
Base broker interface.
Any new broker (Zerodha, Upstox, etc.) must implement this class.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Quote:
    symbol: str
    ltp: float
    change: float
    change_pct: float
    volume: int
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0


@dataclass
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


@dataclass
class Instrument:
    symbol: str
    name: str
    exchange: str
    token: str


@dataclass
class Holding:
    symbol: str
    qty: int
    avg_cost: float
    ltp: float
    pnl: float
    pnl_pct: float
    current_value: float = 0.0
    invested_value: float = 0.0


@dataclass
class Position:
    symbol: str
    qty: int
    entry_price: float
    ltp: float
    pnl: float
    product: str = "INTRADAY"


@dataclass
class Funds:
    available_cash: float
    used_margin: float
    net_available: float


@dataclass
class Order:
    order_id: str
    symbol: str
    action: str        # BUY / SELL
    qty: int
    order_type: str    # MARKET / LIMIT
    status: str
    price: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class OrderResult:
    order_id: str
    status: str
    symbol: str
    qty: int
    action: str
    order_type: str
    price: Optional[float] = None


class BaseBroker(ABC):
    """
    Abstract broker interface.

    To add a new broker:
      1. Create trade/brokers/yourbroker.py
      2. Subclass BaseBroker and implement every abstract method
      3. Register the broker name in trade/config.py BROKER_REGISTRY
    """

    @abstractmethod
    def login(self, credentials: dict) -> None:
        """Authenticate using credentials dict from .env"""
        ...

    @abstractmethod
    def get_quote(self, symbols: list[str]) -> list[Quote]:
        """Live LTP + change for a list of symbols"""
        ...

    @abstractmethod
    def get_history(
        self,
        symbol: str,
        interval: str,
        from_date: str,
        to_date: str,
    ) -> list[Candle]:
        """OHLCV candles. interval: ONE_MINUTE, FIVE_MINUTE, ONE_DAY, etc."""
        ...

    @abstractmethod
    def search_instruments(self, query: str) -> list[Instrument]:
        """Fuzzy search instruments by name or symbol"""
        ...

    @abstractmethod
    def buy(
        self,
        symbol: str,
        qty: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        product: str = "DELIVERY",
    ) -> OrderResult:
        ...

    @abstractmethod
    def sell(
        self,
        symbol: str,
        qty: int,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        product: str = "DELIVERY",
    ) -> OrderResult:
        ...

    @abstractmethod
    def get_portfolio(self) -> list[Holding]:
        """Long-term holdings"""
        ...

    @abstractmethod
    def get_positions(self) -> list[Position]:
        """Intraday / short-term open positions"""
        ...

    @abstractmethod
    def get_funds(self) -> Funds:
        """Available cash and margin"""
        ...

    @abstractmethod
    def get_orders(self) -> list[Order]:
        """Today's order book"""
        ...
