"""SQLite-хранилище: заявки и выданные ключи (файл bot.db)."""

import sqlite3
from datetime import datetime

DB_PATH = "bot.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                username   TEXT,
                full_name  TEXT,
                tariff     TEXT NOT NULL,
                devices    INTEGER NOT NULL,
                amount     INTEGER NOT NULL,
                status     TEXT NOT NULL DEFAULT 'created',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS issued_keys (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                key        TEXT NOT NULL,
                tariff     TEXT NOT NULL,
                devices    INTEGER NOT NULL,
                issued_at  TEXT NOT NULL
            );
            """
        )


def _now() -> str:
    return datetime.now().strftime("%d.%m.%Y %H:%M")


def create_order(user_id: int, username: str | None, full_name: str,
                 tariff: str, devices: int, amount: int) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO orders (user_id, username, full_name, tariff, devices, amount, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, full_name, tariff, devices, amount, _now()),
        )
        return int(cur.lastrowid)


def get_order(order_id: int) -> sqlite3.Row | None:
    with _conn() as c:
        return c.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def set_order_status(order_id: int, status: str) -> None:
    with _conn() as c:
        c.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def add_issued_key(user_id: int, key: str, tariff: str, devices: int) -> None:
    with _conn() as c:
        c.execute(
            "INSERT INTO issued_keys (user_id, key, tariff, devices, issued_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (user_id, key, tariff, devices, _now()),
        )


def get_user_keys(user_id: int) -> list[sqlite3.Row]:
    with _conn() as c:
        return c.execute(
            "SELECT * FROM issued_keys WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
