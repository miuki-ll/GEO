"""Print tables and columns from the configured database (MySQL / SQLite)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pymysql
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[2]


def _print_sqlite(url) -> None:
    db_path = url.database
    if not db_path or db_path == ":memory:":
        print("SQLite in-memory database has no file to inspect.")
        return
    path = Path(db_path)
    if not path.is_absolute():
        path = BACKEND_DIR / path
    if not path.exists():
        print(f"Not found: {path}")
        return

    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall() if not row[0].startswith("sqlite_")]

    print(f"Database: {path}")
    print(f"Tables: {len(tables)}\n")
    for table in tables:
        cur.execute(f"PRAGMA table_info({table})")
        cols = cur.fetchall()
        print(f"=== {table} ({len(cols)} columns) ===")
        for col in cols:
            _, name, col_type, notnull, default, pk = col
            null_text = "NOT NULL" if notnull else "nullable"
            pk_text = " PK" if pk else ""
            default_text = f" default={default}" if default is not None else ""
            print(f"  {name:30} {col_type:15} {null_text}{pk_text}{default_text}")
        print()
    conn.close()


def _print_mysql(url) -> None:
    conn = pymysql.connect(
        host=url.host or "127.0.0.1",
        port=url.port or 3306,
        user=url.username or "root",
        password=url.password or "",
        database=url.database,
        charset="utf8mb4",
    )
    cur = conn.cursor()
    cur.execute("SHOW TABLES")
    tables = sorted(row[0] for row in cur.fetchall())

    print(f"Database: mysql://{url.host}:{url.port or 3306}/{url.database}")
    print(f"Tables: {len(tables)}\n")
    for table in tables:
        cur.execute(f"SHOW FULL COLUMNS FROM `{table}`")
        cols = cur.fetchall()
        print(f"=== {table} ({len(cols)} columns) ===")
        for col in cols:
            name, col_type, _, _, nullable, default, _, _, _ = col[:9]
            null_text = "nullable" if nullable == "YES" else "NOT NULL"
            default_text = f" default={default}" if default is not None else ""
            print(f"  {name:30} {col_type:20} {null_text}{default_text}")
        print()
    conn.close()


def main() -> None:
    from app.core.config import settings

    url = make_url(settings.DATABASE_URL)
    if url.get_backend_name() == "sqlite":
        _print_sqlite(url)
    elif url.get_backend_name() == "mysql":
        _print_mysql(url)
    else:
        print(f"Unsupported dialect: {url.get_backend_name()}")
        print("Use MySQL Workbench / DBeaver for PostgreSQL etc.")


if __name__ == "__main__":
    main()
