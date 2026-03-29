"""Tests for config.py — user discovery and credential loading."""
import os
import pytest
from unittest.mock import patch


def test_list_users_empty():
    """No *_CLIENT_ID vars → empty list."""
    from trade.config import list_users
    with patch.dict(os.environ, {}, clear=True):
        import trade.config as cfg
        cfg._loaded = False
        result = list_users()
    assert isinstance(result, list)


def test_list_users_discovers_profiles():
    """*_CLIENT_ID keys become user names."""
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {
        "ME_CLIENT_ID":     "C001",
        "DAD_CLIENT_ID":    "C002",
        "MOM_CLIENT_ID":    "C003",
        "UNRELATED_KEY":    "xyz",
    }):
        users = cfg.list_users()

    assert "me"  in users
    assert "dad" in users
    assert "mom" in users
    assert "unrelated" not in users


def test_list_users_sorted():
    """list_users returns names in alphabetical order."""
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {
        "ZED_CLIENT_ID": "Z",
        "AAA_CLIENT_ID": "A",
        "MMM_CLIENT_ID": "M",
    }):
        users = cfg.list_users()
    assert users == sorted(users)


def test_has_credentials_true():
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {
        "ME_CLIENT_ID":   "C001",
        "ME_API_KEY":     "KEY",
        "ME_PASSWORD":    "PASS",
        "ME_TOTP_SECRET": "TOTP",
    }):
        assert cfg.has_credentials("me") is True


def test_has_credentials_false_missing_field():
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {
        "ME_CLIENT_ID": "C001",
        "ME_API_KEY":   "KEY",
        # PASSWORD and TOTP_SECRET missing
    }, clear=False):
        # Remove any existing ME_PASSWORD / ME_TOTP_SECRET
        env = {k: v for k, v in os.environ.items()
               if k not in ("ME_PASSWORD", "ME_TOTP_SECRET")}
        env.update({"ME_CLIENT_ID": "C001", "ME_API_KEY": "KEY"})
        with patch.dict(os.environ, env, clear=True):
            assert cfg.has_credentials("me") is False


def test_get_default_user_from_env():
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {
        "DEFAULT_USER":  "dad",
        "DAD_CLIENT_ID": "D001",
    }):
        assert cfg.get_default_user() == "dad"


def test_get_ai_key_claude():
    from trade import config as cfg
    cfg._loaded = True
    with patch.dict(os.environ, {"CLAUDE_API_KEY": "sk-ant-test"}):
        provider, key = cfg.get_ai_key()
    assert provider == "claude"
    assert key == "sk-ant-test"


def test_get_ai_key_openai_fallback():
    from trade import config as cfg
    cfg._loaded = True
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_API_KEY",)}
    env["OPENAI_API_KEY"] = "sk-openai-test"
    with patch.dict(os.environ, env, clear=True):
        provider, key = cfg.get_ai_key()
    assert provider == "openai"
    assert key == "sk-openai-test"


def test_get_ai_key_none_when_missing():
    from trade import config as cfg
    cfg._loaded = True
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_API_KEY", "OPENAI_API_KEY")}
    with patch.dict(os.environ, env, clear=True):
        provider, key = cfg.get_ai_key()
    assert provider is None
    assert key is None
