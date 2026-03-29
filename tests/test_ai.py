"""Tests for ai.py — ParsedCommand building and no-key fallback."""
import pytest
from unittest.mock import patch
from trade.ai import _build, parse, ParsedCommand


class TestBuildParsedCommand:
    def test_basic_buy(self):
        cmd = _build({"action": "buy", "symbol": "ITC", "qty": 10})
        assert cmd.action == "buy"
        assert cmd.symbol == "ITC"
        assert cmd.qty == 10
        assert cmd.order_type == "MARKET"

    def test_limit_order(self):
        cmd = _build({"action": "buy", "symbol": "ITC", "qty": 5,
                      "order_type": "LIMIT", "limit_price": 450.0})
        assert cmd.order_type == "LIMIT"
        assert cmd.limit_price == 450.0

    def test_with_user(self):
        cmd = _build({"action": "sell", "symbol": "RELIANCE", "qty": 3, "user": "dad"})
        assert cmd.user == "dad"

    def test_defaults(self):
        cmd = _build({"action": "portfolio"})
        assert cmd.symbol is None
        assert cmd.qty is None
        assert cmd.user is None
        assert cmd.period == "1m"
        assert cmd.interval == "1d"

    def test_symbols_list(self):
        cmd = _build({"action": "price", "symbols": ["ITC", "RELIANCE"]})
        assert cmd.symbols == ["ITC", "RELIANCE"]

    def test_answer_action(self):
        cmd = _build({"action": "answer", "answer": "Your portfolio is up 5%"})
        assert cmd.action == "answer"
        assert cmd.answer == "Your portfolio is up 5%"


class TestParseNoKey:
    def test_returns_answer_when_no_ai_key(self):
        """parse() must return a friendly message, never raise, when no key."""
        import trade.config as cfg
        cfg._loaded = True
        import os
        env = {k: v for k, v in os.environ.items()
               if k not in ("CLAUDE_API_KEY", "OPENAI_API_KEY")}
        with patch.dict(os.environ, env, clear=True):
            cmd = parse("buy ITC 10")
        assert cmd.action == "answer"
        assert cmd.answer is not None
        assert len(cmd.answer) > 0
