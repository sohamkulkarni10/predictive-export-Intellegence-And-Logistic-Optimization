"""
Simple login helpers for the Export AI dashboard.
Demo users only — change passwords before any real deployment.
"""

from __future__ import annotations

import hashlib
import secrets
from typing import Any

# username -> password (demo)
USERS = {
    "exporter": "india@11",
    "admin": "admin@123",
    "demo": "demo@123",
}

_tokens: dict[str, str] = {}


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def login(username: str, password: str) -> dict[str, Any] | None:
    user = (username or "").strip().lower()
    pwd = password or ""
    if user not in USERS or USERS[user] != pwd:
        return None
    token = secrets.token_urlsafe(24)
    _tokens[token] = user
    return {"token": token, "username": user, "display_name": user.title()}


def verify_token(token: str | None) -> str | None:
    if not token:
        return None
    return _tokens.get(token)


def logout(token: str | None) -> None:
    if token and token in _tokens:
        del _tokens[token]
