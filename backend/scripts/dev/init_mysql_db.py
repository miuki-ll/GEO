"""Create geo_db on local MySQL if it does not exist."""
from __future__ import annotations

import os
import sys
from urllib.parse import unquote, urlparse

import pymysql

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BACKEND_DIR)

from app.core.config import settings  # noqa: E402


def _parse_mysql_url(url: str) -> dict:
    parsed = urlparse(url.replace("+pymysql", ""))
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or "root"),
        "password": unquote(parsed.password or ""),
        "database": (parsed.path or "/geo_db").lstrip("/").split("?")[0] or "geo_db",
    }


def main() -> None:
    cfg = _parse_mysql_url(settings.DATABASE_URL)
    db_name = cfg.pop("database")

    conn = pymysql.connect(**cfg)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
        print(f"MySQL database ready: {db_name}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
