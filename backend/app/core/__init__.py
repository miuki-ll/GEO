from app.core.config import settings
from app.core.db import Base, engine, get_db, SessionLocal
from app.core.logging_config import get_logger

__all__ = [
    "settings",
    "Base",
    "engine",
    "get_db",
    "SessionLocal",
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_token",
    "get_logger",
]


def __getattr__(name: str):
    if name in ("verify_password", "get_password_hash", "create_access_token", "decode_token"):
        from app.core.security import (
            verify_password,
            get_password_hash,
            create_access_token,
            decode_token,
        )
        return {
            "verify_password": verify_password,
            "get_password_hash": get_password_hash,
            "create_access_token": create_access_token,
            "decode_token": decode_token,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
