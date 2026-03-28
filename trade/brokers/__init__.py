from .base import (
    BaseBroker, Candle, Funds, Holding,
    Instrument, Order, OrderResult, Position, Quote,
)
from .angelone import AngelOneBroker
from .yahoo import YahooFinanceBroker

# ---------------------------------------------------------------
# BROKER REGISTRY
# To add a new broker:
#   1. Create trade/brokers/yourbroker.py implementing BaseBroker
#   2. Import it here and add to BROKER_REGISTRY
# ---------------------------------------------------------------
BROKER_REGISTRY: dict[str, type[BaseBroker]] = {
    "angelone": AngelOneBroker,
    "yahoo":    YahooFinanceBroker,   # public, no login needed
    # "zerodha": ZerodhaBroker,
    # "upstox":  UpstoxBroker,
}

__all__ = [
    "BaseBroker", "AngelOneBroker", "YahooFinanceBroker", "BROKER_REGISTRY",
    "Quote", "Candle", "Instrument", "Holding",
    "Position", "Funds", "Order", "OrderResult",
]
