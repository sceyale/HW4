"""Customer memory + page context checks (Problem 8). Uses a temporary COPY of the database.

    python test_memory.py
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

import db

TMP = Path(tempfile.mkdtemp()) / "campus_customs.db"
shutil.copy(db.DB_PATH, TMP)
db.DB_PATH = TMP                                    # everything below uses the copy

import agent  # noqa: E402  (after the DB swap)
import tools  # noqa: E402
from models import PageContext  # noqa: E402

results: list[bool] = []


def check(ok, label: str) -> None:
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + label)


class Ctx:
    def __init__(self, deps):
        self.deps = deps


TEST = {"id": 1, "first_name": "Test", "last_name": "User", "email": "test@campuscustoms.yale.edu",
        "created_at": "2026-09-19 11:34:09", "name": "Test User"}
OTHER = {"id": 3, "first_name": "Tauhid", "last_name": "Zaman", "email": "tauhid.zaman@yale.edu",
         "created_at": "2026-09-19 11:57:56", "name": "Tauhid Zaman"}

print("-- chat history table --")
db.init_chat_tables()
cols = [r[1] for r in sqlite3.connect(TMP).execute("PRAGMA table_info(chat_messages)")]
check("context_json" in cols, f"chat_messages columns: {', '.join(cols)}")
before = db.count_chat_messages(1)
card = {"product_id": "baseball-left-chest-crewneck", "name": "Baseball Left Chest Crewneck"}
db.save_chat_turn(1, "do you have this in pink?", "Sorry, only navy and white.", [card],
                  {"page": "product", "product_id": "baseball-left-chest-crewneck"})
check(db.count_chat_messages(1) == before + 2, "a logged-in turn saves 2 rows (user + assistant)")
hist = db.load_chat_history(1)
check(hist[-2]["context"]["product_id"] == "baseball-left-chest-crewneck" and
      hist[-1]["product_ids"] == ["baseball-left-chest-crewneck"], "reload returns page context and cards shown")
check(all(h["role"] in ("user", "assistant") for h in hist), f"returning shopper reloads {len(hist)} messages, oldest first")

print("\n-- who is chatting (agent sees) --")
deps = agent.build_deps(TEST, PageContext(page="product", path="/products/baseball-left-chest-crewneck",
                                          product_id="baseball-left-chest-crewneck"))
check(deps.email == TEST["email"] and deps.first_name == "Test" and deps.user_id == 1, "deps carry id, name, email from the session")
check(not hasattr(deps, "password_hash"), "no password hash in deps")
prof = tools.get_shopper_profile(Ctx(deps))
check(prof.logged_in and prof.email == TEST["email"] and prof.saved_messages == before + 2,
      f"get_shopper_profile: {prof.first_name} {prof.last_name}, {prof.email}, {prof.saved_messages} saved msgs")
guest = tools.get_shopper_profile(Ctx(agent.build_deps(None, None)))
check(not guest.logged_in and guest.email is None, "guest profile reveals nothing")

print("\n-- recall past chats (own history only) --")
r = tools.recall_chat_history(Ctx(deps), query="pink")
check(r.total_found >= 1 and r.messages[0].role in ("user", "assistant"), f"recall 'pink' finds {r.total_found} of Test User's messages")
mine = {m.content for m in tools.recall_chat_history(Ctx(deps), limit=20).messages}
theirs = {h["content"] for h in db.load_chat_history(3)}
check(not (mine & theirs - {""}), "Test User's recall never includes Tauhid's messages")
check(not tools.recall_chat_history(Ctx(agent.build_deps(None, None))).logged_in, "guests: recall says chats aren't saved")

print("\n-- page context: 'do you have this shirt in pink?' --")
text = agent.describe_context(deps)
check("Item open on the page: Baseball Left Chest Crewneck" in text and "navy, white" in text,
      "item page: agent is told the open item and its design colors")
check("test@campuscustoms.yale.edu" in text and "Test User" in text, "agent is told who is chatting (name + email)")
pdeps = agent.build_deps(None, PageContext(page="products", path="/products", category="Hoodies",
                                          visible_product_ids=["basic-hoodie-big-yale", "fake-id", "crew-left-chest-hoodie"]))
ptext = agent.describe_context(pdeps)
check("Category filter selected: Hoodies" in ptext and "1. Basic Hoodie Big Yale" in ptext, "products page: filter + visible cards listed")
check("fake-id" not in ptext and "fake-id" not in pdeps.seen_product_ids, "made-up ids from the browser are dropped")
check("guest" in ptext.lower(), "guest is identified as a guest")
fake = agent.build_deps(None, PageContext(page="product", product_id="not-a-real-item"))
check(fake.current_product_id is None, "unknown product_id on the page is ignored")

print("\n-- history sent to the model keeps the page context --")
msgs = agent.to_model_history(hist[-2:])
check("[Shopper was viewing: baseball-left-chest-crewneck]" in msgs[0].parts[0].content, "past 'this' is resolvable later")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
