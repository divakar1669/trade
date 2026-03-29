"""Tests for the CLI smart router — structured command parsing."""
import pytest
from trade.cli import _flag, _parse_order, _parse_history


class TestFlagExtractor:
    def test_finds_flag_value(self):
        assert _flag(["buy", "ITC", "--user", "dad"], "--user") == "dad"

    def test_finds_short_flag(self):
        assert _flag(["buy", "ITC", "-u", "mom"], "-u", "--user") == "mom"

    def test_returns_none_when_missing(self):
        assert _flag(["buy", "ITC", "10"], "--user") is None

    def test_returns_none_when_flag_is_last_token(self):
        assert _flag(["buy", "--user"], "--user") is None


class TestParseOrder:
    def test_basic_buy(self):
        cmd = _parse_order("buy", ["buy", "ITC", "10"])
        assert cmd.action == "buy"
        assert cmd.symbol == "ITC"
        assert cmd.qty == 10
        assert cmd.order_type == "MARKET"
        assert cmd.limit_price is None
        assert cmd.user is None

    def test_sell_with_user(self):
        cmd = _parse_order("sell", ["sell", "RELIANCE", "5", "--user", "dad"])
        assert cmd.action == "sell"
        assert cmd.symbol == "RELIANCE"
        assert cmd.qty == 5
        assert cmd.user == "dad"

    def test_limit_order(self):
        cmd = _parse_order("buy", ["buy", "ITC", "10", "--limit", "450"])
        assert cmd.order_type == "LIMIT"
        assert cmd.limit_price == 450.0

    def test_short_limit_flag(self):
        cmd = _parse_order("buy", ["buy", "ITC", "5", "-l", "300"])
        assert cmd.order_type == "LIMIT"
        assert cmd.limit_price == 300.0

    def test_missing_qty(self):
        cmd = _parse_order("buy", ["buy", "ITC"])
        assert cmd.qty is None

    def test_missing_symbol(self):
        cmd = _parse_order("buy", ["buy"])
        assert cmd.symbol == ""


class TestParseHistory:
    def test_defaults(self):
        cmd = _parse_history(["history", "ITC"])
        assert cmd.action == "history"
        assert cmd.symbol == "ITC"
        assert cmd.period == "1m"
        assert cmd.interval == "1d"

    def test_custom_period(self):
        cmd = _parse_history(["history", "RELIANCE", "--period", "6m"])
        assert cmd.period == "6m"

    def test_custom_interval(self):
        cmd = _parse_history(["history", "INFY", "--interval", "15m"])
        assert cmd.interval == "15m"

    def test_both_options(self):
        cmd = _parse_history(["history", "TCS", "--period", "1y", "--interval", "1h"])
        assert cmd.period == "1y"
        assert cmd.interval == "1h"
