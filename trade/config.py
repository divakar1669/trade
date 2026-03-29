"""
Config loader.
Reads ~/.trade/.env, auto-discovers users by scanning for *_CLIENT_ID keys.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .brokers import BROKER_REGISTRY, BaseBroker

CONFIG_DIR  = Path.home() / ".trade"
ENV_FILE    = CONFIG_DIR / ".env"
TOKENS_DIR  = CONFIG_DIR / "tokens"

_loaded = False


def _ensure_loaded():
    global _loaded
    if not _loaded:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        TOKENS_DIR.mkdir(parents=True, exist_ok=True)
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE)
        _loaded = True


def list_users() -> list[str]:
    """Return all user names discovered from .env (anything with *_CLIENT_ID)."""
    _ensure_loaded()
    users = []
    for key in os.environ:
        if key.endswith("_CLIENT_ID"):
            name = key[: -len("_CLIENT_ID")].lower()
            users.append(name)
    return sorted(users)


def get_credentials(user: str) -> dict:
    _ensure_loaded()
    prefix = user.upper()
    client_id   = os.getenv(f"{prefix}_CLIENT_ID")
    api_key     = os.getenv(f"{prefix}_API_KEY")
    password    = os.getenv(f"{prefix}_PASSWORD")
    totp_secret = os.getenv(f"{prefix}_TOTP_SECRET")
    broker_name = os.getenv(f"{prefix}_BROKER", "angelone").lower()

    missing = [k for k, v in {
        "CLIENT_ID":   client_id,
        "API_KEY":     api_key,
        "PASSWORD":    password,
        "TOTP_SECRET": totp_secret,
    }.items() if not v]

    if missing:
        raise ValueError(
            f"Missing credentials for user '{user}': "
            + ", ".join(f"{prefix}_{m}" for m in missing)
            + f"\nEdit {ENV_FILE} to add them."
        )

    return {
        "client_id":   client_id,
        "api_key":     api_key,
        "password":    password,
        "totp_secret": totp_secret,
        "broker":      broker_name,
    }


def get_default_user() -> str:
    _ensure_loaded()
    # Explicit default in .env, else first alphabetically, else "me"
    default = os.getenv("DEFAULT_USER", "").lower()
    if default:
        return default
    users = list_users()
    return users[0] if users else "me"


def get_broker(user: str) -> BaseBroker:
    """Return a logged-in broker instance for the given user."""
    creds = get_credentials(user)
    broker_name = creds["broker"]

    if broker_name not in BROKER_REGISTRY:
        raise ValueError(
            f"Unknown broker '{broker_name}' for user '{user}'. "
            f"Available: {list(BROKER_REGISTRY.keys())}"
        )

    broker = BROKER_REGISTRY[broker_name]()
    broker.login(creds)
    return broker


def has_credentials(user: str) -> bool:
    """Return True if the user has credentials configured in .env."""
    _ensure_loaded()
    prefix = user.upper()
    return bool(
        os.getenv(f"{prefix}_CLIENT_ID")
        and os.getenv(f"{prefix}_API_KEY")
        and os.getenv(f"{prefix}_PASSWORD")
        and os.getenv(f"{prefix}_TOTP_SECRET")
    )


def get_public_broker() -> BaseBroker:
    """Return a Yahoo Finance broker — no login required."""
    from .brokers.yahoo import YahooFinanceBroker
    broker = YahooFinanceBroker()
    broker.login({})
    return broker


def get_ai_key() -> tuple[Optional[str], Optional[str]]:
    """Returns (provider, api_key) or (None, None) if no key is configured."""
    _ensure_loaded()
    claude_key = os.getenv("CLAUDE_API_KEY")
    if claude_key:
        return "claude", claude_key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return "openai", openai_key
    return None, None
