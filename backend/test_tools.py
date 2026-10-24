"""Check the agent tools return real data from campus_customs.db (no model or API key needed).

    python test_tools.py
"""

from __future__ import annotations

import sqlite3
import sys

import db
import tools
from models import ShopDeps

results: list[bool] = []


def check(ok: bool, label: str) -> None:
    results.append(bool(ok))
    print(("PASS " if ok else "FAIL ") + label)


class Ctx:  # minimal stand-in for RunContext: tools only use ctx.deps
    def __init__(self) -> None:
        self.deps = ShopDeps()


def raw(sql: str, *args):
    with sqlite3.connect(f"file:{db.DB_PATH}?mode=ro", uri=True) as c:
        return c.execute(sql, args).fetchall()


ctx = Ctx()

print("-- product info comes from the database --")
d = tools.get_product_details(ctx, "basic-hoodie-big-yale")
price, desc = raw("SELECT price, description FROM catalogue WHERE product_id=?", "basic-hoodie-big-yale")[0]
check(d.price == price and d.description == desc, f"details price ${d.price} and description match the catalogue row")
total = raw("SELECT SUM(quantity) FROM inventory WHERE product_id=?", "basic-hoodie-big-yale")[0][0]
check(d.total_stock == total, f"total stock {d.total_stock} matches SUM(inventory.quantity)")
check(tools.get_product_details(ctx, "Basic Hoodie Big Yale").product_id == "basic-hoodie-big-yale", "lookup by product name works")
check(isinstance(tools.get_product_details(ctx, "pink-yale-shorts"), str), "unknown product returns 'not in database' (nothing invented)")

print("\n-- stock by size --")
pid, size, qty = raw("SELECT product_id, size, quantity FROM inventory WHERE quantity > 5 LIMIT 1")[0]
s = tools.check_stock(ctx, pid, size)
check(s.available and s.quantity == qty and s.message.startswith("IN STOCK"), f"{pid} size {size}: {s.message}")
pid0, size0 = raw("SELECT product_id, size FROM inventory WHERE quantity = 0 LIMIT 1")[0]
s0 = tools.check_stock(ctx, pid0, size0)
check(not s0.available and s0.quantity == 0 and "OUT OF STOCK" in s0.message, f"sold-out size stated clearly: {s0.message}")
sm = tools.check_stock(ctx, pid0, "medium" if size0 == "M" else {"XS":"extra small","S":"small","L":"large","XL":"extra large","XXL":"2xl"}[size0])
check(sm.size_requested == size0, f"size words are understood ('{sm.size_requested}')")
sa = tools.check_stock(ctx, pid0)
check(sa.quantity == raw("SELECT SUM(quantity) FROM inventory WHERE product_id=?", pid0)[0][0] and size0 in sa.sold_out_sizes,
      "no size given -> total stock and sold-out sizes listed")

print("\n-- search and prices --")
r = tools.search_products(ctx, query="Handsome Dan")
def _text(pid: str) -> str:
    full = db.get_product(pid)
    return " ".join([full["name"], full["description"], *full["search_tags"]]).lower()


check(r.total_matches > 0 and all("bulldog" in _text(p.product_id) for p in r.products),
      f"'Handsome Dan' finds bulldog items ({r.total_matches})")
r = tools.search_products(ctx, query="gym shorts")
check(r.total_matches == 0 and r.note, "items we don't carry return 0 matches with a note")
r = tools.search_products(ctx, category="fleece", sort="price_low_to_high", limit=1)
cheapest_fleece = raw("SELECT MIN(price) FROM catalogue WHERE garment_type LIKE '%fleece%' OR garment_type LIKE '%jacket%'")[0][0]
check(r.products[0].price == cheapest_fleece, f"cheapest fleece is ${r.products[0].price} (not a $72 quarter-zip)")
ps = tools.price_summary(ctx)
mn, mx = raw("SELECT MIN(price), MAX(price) FROM catalogue")[0]
check(ps.min_price == mn and ps.max_price == mx, f"shop price range ${ps.min_price}-${ps.max_price}")
r = tools.search_products(ctx, category="Hoodies", size="XL")
check(all("XL" in p.sizes_in_stock for p in r.products), "size filter only returns items with that size in stock")
check(len(ctx.deps.seen_product_ids) > 0, f"tools recorded {len(ctx.deps.seen_product_ids)} looked-up product ids")

print("\n-- chat search that updates the page (Problem 7) --")
c2 = Ctx()
r = tools.search_products(c2, query="hoodies", limit=5)
n_hood = raw("SELECT COUNT(*) FROM catalogue WHERE garment_type LIKE '%hood%'")[0][0]
check(len(r.products) == 5, "model gets only `limit` summaries (5), saving tokens")
ls = c2.deps.last_search
check(ls is not None and ls.total_matches >= n_hood and len(ls.product_ids) == min(ls.total_matches, 30),
      f"last_search keeps every match for the page: {len(ls.product_ids)} of {ls.total_matches} hoodies")
check(set(ls.product_ids) <= c2.deps.seen_product_ids, "all page matches are marked as looked-up (allowed as cards)")
check(all(db.get_product(pid) for pid in ls.product_ids), "every page card id exists in the catalogue")

print("\n-- search-box suggestions (Problem 9) --")
e = tools.suggest("")
check(e["terms"] and not e["products"], f"empty box shows popular searches: {', '.join(e['terms'][:4])}")
h = tools.suggest("hoo")
check([x["name"] for x in h["categories"]] == ["Hoodies"] and h["products"], "'hoo' suggests the Hoodies category + products")
check(all(db.get_product(p["product_id"]) and p["price"] == db.get_product(p["product_id"])["price"] for p in h["products"]),
      "suggested products and prices come from the catalogue")
check(tools.suggest("fle")["categories"][0]["name"] == "Fleeces & Jackets", "'fle' suggests Fleeces & Jackets")
hd = tools.suggest("handsome dan")
check(hd["total_matches"] > 0 and all("bulldog" in _text(p["product_id"]) for p in hd["products"]), "'handsome dan' suggests bulldog items")
check(tools.suggest("pink")["total_matches"] == 0, "'pink' has no matches (UI offers to ask the assistant)")
full, total, _ = tools.search_catalogue(query="bulldog", limit=500, max_limit=500)
check(len(full) == total, f"search page returns every match, not just 30 ({total})")

print(f"\n{sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
