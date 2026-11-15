"""Direct database access used ONLY for test set-up and for verifying side effects (never to drive the UI)."""
import sqlite3
from .config import DB_FILE


def connect():
    con = sqlite3.connect(DB_FILE, timeout=15)
    con.row_factory = sqlite3.Row
    return con


def q(sql, params=()):
    con = connect()
    try:
        return [dict(r) for r in con.execute(sql, params).fetchall()]
    finally:
        con.close()


def one(sql, params=()):
    rows = q(sql, params)
    return rows[0] if rows else None


def scalar(sql, params=()):
    r = one(sql, params)
    return None if r is None else list(r.values())[0]


def run(sql, params=()):
    con = connect()
    try:
        cur = con.execute(sql, params)
        con.commit()
        return cur.lastrowid
    finally:
        con.close()


def gems(user_id):
    return scalar("SELECT gems FROM users WHERE id=?", (user_id,)) or 0


def set_gems(user_id, n):
    run("UPDATE users SET gems=? WHERE id=?", (n, user_id))


def clear_login_attempts():
    run("DELETE FROM login_attempts")
