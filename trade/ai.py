"""
Natural language → structured trade command via Claude (or OpenAI fallback).
Uses tool/function calling so the output is always structured JSON.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Optional

from .config import get_ai_key

# ------------------------------------------------------------------
# Structured command returned by the AI layer
# ------------------------------------------------------------------

@dataclass
class ParsedCommand:
    action: str                          # buy|sell|price|portfolio|positions|funds|orders|history|search|answer
    symbol: Optional[str]    = None
    symbols: list[str]       = None      # for multi-symbol price
    qty: Optional[int]       = None
    user: Optional[str]      = None
    order_type: str          = "MARKET"
    limit_price: Optional[float] = None
    period: str              = "1m"      # for history
    interval: str            = "1d"      # for history
    answer: Optional[str]    = None      # for analytical questions

    def __post_init__(self):
        if self.symbols is None:
            self.symbols = []


# ------------------------------------------------------------------
# Tool / function schema (same shape for both Claude and OpenAI)
# ------------------------------------------------------------------

_TOOL_SCHEMA = {
    "name": "trade_command",
    "description": (
        "Parse a natural language trading request into a structured command. "
        "For analytical questions (e.g. 'how is my portfolio doing'), set action='answer' "
        "and put the response in the 'answer' field."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["buy", "sell", "price", "portfolio", "positions",
                         "funds", "orders", "history", "search", "answer"],
            },
            "symbol":      {"type": "string",  "description": "NSE symbol e.g. ITC, HDFCBANK"},
            "symbols":     {"type": "array",   "items": {"type": "string"}},
            "qty":         {"type": "integer"},
            "user":        {"type": "string",  "description": "Profile name: me, dad, mom, spouse …"},
            "order_type":  {"type": "string",  "enum": ["MARKET", "LIMIT"], "default": "MARKET"},
            "limit_price": {"type": "number"},
            "period":      {"type": "string",  "description": "1w | 1m | 3m | 6m | 1y"},
            "interval":    {"type": "string",  "description": "1m | 5m | 15m | 1h | 1d"},
            "answer":      {"type": "string"},
        },
        "required": ["action"],
    },
}

# OpenAI uses a slightly different schema wrapper
_OPENAI_TOOL = {
    "type": "function",
    "function": {
        "name": _TOOL_SCHEMA["name"],
        "description": _TOOL_SCHEMA["description"],
        "parameters": _TOOL_SCHEMA["input_schema"],
    },
}

_SYSTEM_PROMPT = """\
You are an assistant that parses natural-language stock trading requests into structured commands.

Rules:
- Resolve company names to their NSE symbols (e.g. "Spandana Sphoorty" → "SPANDANASPH", "HDFC Bank" → "HDFCBANK").
- If no user is mentioned, leave user unset (the caller will use the default).
- For analytical questions (portfolio performance, which stocks are in loss, etc.) set action='answer'.
- Always call the trade_command tool — never respond in plain text.
"""


def parse(text: str, context: Optional[dict] = None) -> ParsedCommand:
    """
    Convert a natural language string into a ParsedCommand.
    Returns an 'answer' command with a help message if no AI key is configured.
    """
    provider, api_key = get_ai_key()

    if not provider:
        return ParsedCommand(
            action="answer",
            answer=(
                "No AI key configured — natural language is disabled.\n"
                "  Add CLAUDE_API_KEY or OPENAI_API_KEY to ~/.trade-cli/.env\n"
                "  Or use structured commands — type ? for the list."
            ),
        )

    messages = [{"role": "user", "content": text}]
    if context:
        messages.insert(0, {
            "role": "user",
            "content": f"Current context (use for analysis):\n{json.dumps(context, default=str)}",
        })

    if provider == "claude":
        return _parse_claude(api_key, messages)
    else:
        return _parse_openai(api_key, messages)


def _parse_claude(api_key: str, messages: list[dict]) -> ParsedCommand:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "any"},
        messages=messages,
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == "trade_command":
            return _build(block.input)
    raise RuntimeError("Claude did not call the trade_command tool")


def _parse_openai(api_key: str, messages: list[dict]) -> ParsedCommand:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": _SYSTEM_PROMPT}] + messages,
        tools=[_OPENAI_TOOL],
        tool_choice={"type": "function", "function": {"name": "trade_command"}},
    )
    call = resp.choices[0].message.tool_calls[0]
    return _build(json.loads(call.function.arguments))


def _build(data: dict) -> ParsedCommand:
    return ParsedCommand(
        action=data["action"],
        symbol=data.get("symbol"),
        symbols=data.get("symbols", []),
        qty=data.get("qty"),
        user=data.get("user"),
        order_type=data.get("order_type", "MARKET"),
        limit_price=data.get("limit_price"),
        period=data.get("period", "1m"),
        interval=data.get("interval", "1d"),
        answer=data.get("answer"),
    )
