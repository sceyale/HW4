"""Read-only data access for the Campus Customs SQLite database."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"

# The catalogue uses 22 garment_type labels for ~7 real categories.
# Order matters: the first keyword that matches wins.
CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Fleeces & Jackets", ("fleece", "jacket")),
    ("Quarter-Zips", ("quarter-zip",)),
    ("Hoodies", ("hood",)),
    ("Long Sleeve", ("long-sleeve",)),
    ("T-Shirts", ("t-shirt",)),
    ("Crewnecks", ("crewneck", "mockneck")),
]

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def category_for(garment_type: str) -> str:
    g = garment_type.lower()
    for category, keywords in CATEGORY_RULES:
        if any(k in g for k in keywords):
            return category
    return "Other"


def connect() -> sqlite3.Connection:
    # mode=ro: the shop pages never write to the catalogue.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_product(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "category": category_for(row["garment_type"]),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "image_file_path": row["image_file_path"],
        "image_url": f"/media/{row['image_file_path']}",
        "price": row["price"],
    }


def _inventory(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not product_ids:
        return {}
    marks = ",".join("?" * len(product_ids))
    rows = conn.execute(
        f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})",
        product_ids,
    ).fetchall()
    out: dict[str, list[dict[str, Any]]] = {pid: [] for pid in product_ids}
    for r in rows:
        out[r["product_id"]].append({"size": r["size"], "quantity": r["quantity"]})
    for items in out.values():
        items.sort(key=lambda i: SIZE_ORDER.index(i["size"]) if i["size"] in SIZE_ORDER else 99)
    return out


def _with_inventory(conn: sqlite3.Connection, products: list[dict[str, Any]]) -> list[dict[str, Any]]:
    inv = _inventory(conn, [p["product_id"] for p in products])
    for p in products:
        p["inventory"] = inv.get(p["product_id"], [])
        p["total_stock"] = sum(i["quantity"] for i in p["inventory"])
    return products


def list_products(category: str | None = None, q: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        products = [_row_to_product(r) for r in rows]
        if category:
            products = [p for p in products if p["category"].lower() == category.lower()]
        if q:
            needle = q.lower()
            products = [
                p for p in products
                if needle in " ".join([p["name"], p["description"], p["garment_type"],
                                       *p["colors"], *p["search_tags"]]).lower()
            ]
        return _with_inventory(conn, products)


def get_product(product_id: str) -> dict[str, Any] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        return _with_inventory(conn, [_row_to_product(row)])[0]


def list_categories() -> list[dict[str, Any]]:
    counts: dict[str, dict[str, Any]] = {}
    for p in list_products():
        c = counts.setdefault(p["category"], {"name": p["category"], "count": 0, "min_price": p["price"]})
        c["count"] += 1
        c["min_price"] = min(c["min_price"], p["price"])
    return sorted(counts.values(), key=lambda c: c["min_price"])


# ---------------------------------------------------------------- chat history (chat_messages)
#
# Logged-in shoppers' chats are stored here and reloaded when they come back.
# Columns: id, user_id, role, content, products_json, created_at  (+ context_json, added below)

def _write_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_chat_tables() -> None:
    """Make sure chat_messages exists and has context_json (the page the shopper was on)."""
    with _write_conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS chat_messages (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   user_id INTEGER NOT NULL,
                   role TEXT NOT NULL,
                   content TEXT NOT NULL,
                   products_json TEXT,
                   created_at TEXT NOT NULL DEFAULT (datetime('now')),
                   FOREIGN KEY (user_id) REFERENCES users(id)
               )"""
        )
        cols = {r["name"] for r in conn.execute("PRAGMA table_info(chat_messages)")}
        if "context_json" not in cols:
            conn.execute("ALTER TABLE chat_messages ADD COLUMN context_json TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages (user_id, id)")


def save_chat_turn(user_id: int, user_text: str, reply: str, products: list[dict],
                   context: dict | None = None) -> None:
    """Save the shopper's message (with page context) and the reply (with the cards shown)."""
    with _write_conn() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, context_json) VALUES (?, 'user', ?, ?)",
            (user_id, user_text, json.dumps(context) if context else None),
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, json.dumps(products) if products else None),
        )


def _history_row(r: sqlite3.Row) -> dict[str, Any]:
    ids: list[str] = []
    if r["products_json"]:
        try:
            ids = [p["product_id"] for p in json.loads(r["products_json"]) if "product_id" in p]
        except (ValueError, TypeError):
            ids = []
    context = None
    if "context_json" in r.keys() and r["context_json"]:
        try:
            context = json.loads(r["context_json"])
        except (ValueError, TypeError):
            context = None
    return {"id": r["id"], "role": r["role"], "content": r["content"], "product_ids": ids,
            "context": context, "created_at": r["created_at"]}


def load_chat_history(user_id: int, limit: int = 50) -> list[dict[str, Any]]:
    """Most recent messages for ONE shopper, oldest first."""
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?", (user_id, limit)
        ).fetchall()
    return [_history_row(r) for r in reversed(rows)]


def search_chat_history(user_id: int, query: str | None = None, limit: int = 10) -> tuple[list[dict[str, Any]], int]:
    """Search ONE shopper's past messages (content or products shown). Returns (newest-first rows, total)."""
    sql, args = "FROM chat_messages WHERE user_id = ?", [user_id]
    if query and query.strip():
        like = f"%{query.strip().lower()}%"
        sql += " AND (LOWER(content) LIKE ? OR LOWER(COALESCE(products_json, '')) LIKE ?)"
        args += [like, like]
    with connect() as conn:
        total = conn.execute(f"SELECT COUNT(*) {sql}", args).fetchone()[0]
        rows = conn.execute(f"SELECT * {sql} ORDER BY id DESC LIMIT ?", [*args, limit]).fetchall()
    return [_history_row(r) for r in rows], total


def count_chat_messages(user_id: int) -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]


def clear_chat_history(user_id: int) -> None:
    with _write_conn() as conn:
        conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,))
