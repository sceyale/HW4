"""Tools the shop agent can call. All read the catalogue through db.py (read-only).

The agent never gets access to the users table, password hashes or other shoppers' chats.
Each tool records which products it returned in ctx.deps.seen_product_ids, so the API
can make sure the agent only shows products it actually looked up.
"""

from __future__ import annotations

import re
from typing import Literal

from pydantic_ai import RunContext

import audit
import db
from models import (
    ChatRecall,
    PastMessage,
    SearchInfo,
    ShopperProfile,
    CategoryPrice,
    PriceSummary,
    ProductDetails,
    ProductSummary,
    SearchResult,
    ShopDeps,
    SizeStock,
    StockCheck,
)

LOW_STOCK = 5
MAX_RESULTS = 12          # summaries sent to the model (token budget)
MAX_PAGE_RESULTS = 30     # matches the website can show as cards (largest category: 29)

# Words shoppers use -> words that appear in the catalogue.
SYNONYMS: dict[str, list[str]] = {
    "handsome dan": ["bulldog"],
    "mascot": ["bulldog"],
    "tee": ["t-shirt"],
    "tshirt": ["t-shirt"],
    "shirt": ["t-shirt", "shirt"],
    "hoody": ["hoodie"],
    "sweater": ["sweatshirt", "sweater"],
    "quarter zip": ["quarter zip", "1/4 zip", "quarter-zip"],
    "1/4 zip": ["quarter zip", "1/4 zip", "quarter-zip"],
    "half zip": ["quarter zip"],
    "zip up": ["full zip", "zip-up", "full-zip"],
    "grey": ["gray"],
    "blue": ["blue", "navy"],
    "yale blue": ["navy"],
    "the game": ["the game", "harvard"],
}

STOPWORDS = {
    "a", "an", "the", "any", "anything", "something", "with", "on", "in", "of", "for", "and", "or",
    "do", "you", "have", "got", "u", "me", "show", "i", "im", "looking", "want", "need", "some",
    "is", "are", "it", "that", "this", "what", "whats", "your", "my", "please", "yale", "item",
    "items", "word", "words", "one", "ones", "like", "find",
}

# Loose category names the model might pass -> catalogue category.
CATEGORY_ALIASES: dict[str, str] = {
    "t-shirt": "T-Shirts", "t-shirts": "T-Shirts", "tshirt": "T-Shirts", "tee": "T-Shirts", "tees": "T-Shirts",
    "crewneck": "Crewnecks", "crewnecks": "Crewnecks", "crew": "Crewnecks", "sweatshirt": "Crewnecks",
    "hoodie": "Hoodies", "hoodies": "Hoodies",
    "long sleeve": "Long Sleeve", "long-sleeve": "Long Sleeve",
    "quarter-zip": "Quarter-Zips", "quarter-zips": "Quarter-Zips", "quarter zip": "Quarter-Zips",
    "fleece": "Fleeces & Jackets", "fleeces": "Fleeces & Jackets", "jacket": "Fleeces & Jackets",
    "jackets": "Fleeces & Jackets",
}

SortOrder = Literal["relevance", "price_low_to_high", "price_high_to_low", "name"]


# ---------------------------------------------------------------- helpers (no model involved)

def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().replace("¼", "1/4")).strip()


def resolve_category(name: str | None) -> str | None:
    if not name:
        return None
    n = _norm(name)
    known = {c["name"].lower(): c["name"] for c in db.list_categories()}
    return known.get(n) or CATEGORY_ALIASES.get(n) or CATEGORY_ALIASES.get(n.rstrip("s")) or name


def _terms(query: str) -> list[list[str]]:
    """Split a query into terms; each term is a list of acceptable spellings."""
    q = _norm(query)
    groups: list[list[str]] = []
    for phrase, alts in SYNONYMS.items():          # multi-word phrases first
        if " " in phrase and phrase in q:
            groups.append([phrase, *alts])
            q = q.replace(phrase, " ")
    for word in re.findall(r"[a-z0-9/&'-]+", q):
        word = word.strip("'")
        if not word or word in STOPWORDS:
            continue
        stem = word[:-1] if word.endswith("s") and len(word) > 3 else word
        groups.append(sorted({word, stem, *SYNONYMS.get(word, []), *SYNONYMS.get(stem, [])}))
    return groups


def _score(p: dict, groups: list[list[str]]) -> int:
    name = _norm(p["name"])
    tags = _norm(" | ".join(p["search_tags"]))
    rest = _norm(" ".join([p["description"], p["garment_type"], p["category"], *p["colors"]]))
    score = 0
    for alts in groups:
        best = 0
        for a in alts:
            if a in name:
                best = max(best, 3)
            elif a in tags:
                best = max(best, 2)
            elif a in rest:
                best = max(best, 1)
        if best == 0:
            return 0                                  # every term must match somewhere
        score += best
    return score


def _in_stock_sizes(p: dict) -> list[str]:
    return [i["size"] for i in p["inventory"] if i["quantity"] > 0]


def _summary(p: dict) -> ProductSummary:
    desc = p["description"]
    return ProductSummary(
        product_id=p["product_id"], name=p["name"], category=p["category"], price=p["price"],
        colors=p["colors"], sizes_in_stock=_in_stock_sizes(p), total_stock=p["total_stock"],
        short_description=desc if len(desc) <= 140 else desc[:137].rsplit(" ", 1)[0] + "...",
    )


def search_catalogue(
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    size: str | None = None,
    sort: SortOrder = "relevance",
    limit: int = 8,
    max_limit: int = MAX_PAGE_RESULTS,
) -> tuple[list[dict], int, str | None]:
    """Plain-Python search used by the tool, the search box and tests. Returns (products, total, note)."""
    cat = resolve_category(category)
    products = db.list_products(category=cat) if cat else db.list_products()
    note = None
    if cat and not products:
        note = f"No category called '{category}'. Categories: " + ", ".join(c["name"] for c in db.list_categories())

    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if size:
        s = normalize_size(size)
        products = [p for p in products if s in _in_stock_sizes(p)]

    scored = [(p, 0) for p in products]
    if query and query.strip():
        groups = _terms(query)
        if groups:
            scored = [(p, sc) for p in products if (sc := _score(p, groups)) > 0]

    if sort == "price_low_to_high":
        scored.sort(key=lambda t: (t[0]["price"], -t[1], t[0]["name"]))
    elif sort == "price_high_to_low":
        scored.sort(key=lambda t: (-t[0]["price"], -t[1], t[0]["name"]))
    elif sort == "name":
        scored.sort(key=lambda t: t[0]["name"])
    else:
        scored.sort(key=lambda t: (-t[1], t[0]["total_stock"] == 0, t[0]["name"]))

    limit = max(1, min(limit, max_limit))
    return [p for p, _ in scored[:limit]], len(scored), note


SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SIZE_WORDS = {"extra small": "XS", "x-small": "XS", "small": "S", "medium": "M", "med": "M", "large": "L",
              "extra large": "XL", "x-large": "XL", "xx-large": "XXL", "2xl": "XXL", "2x": "XXL", "xxl": "XXL"}


def normalize_size(size: str | None) -> str | None:
    if not size:
        return None
    s = size.strip().lower()
    return SIZE_WORDS.get(s, s.upper())


def find_product(product_id_or_name: str) -> dict | None:
    """Exact product_id first, then the best name match (so 'Basic Hoodie Big Yale' also works)."""
    p = db.get_product(product_id_or_name.strip())
    if p:
        return p
    q = _norm(product_id_or_name)
    products = db.list_products()
    exact = [p for p in products if _norm(p["name"]) == q]
    if exact:
        return exact[0]
    hits, _, _ = search_catalogue(query=product_id_or_name, limit=1)
    return hits[0] if hits else None


def size_stock(p: dict) -> list[SizeStock]:
    return [
        SizeStock(size=i["size"], quantity=i["quantity"],
                  status="sold out" if i["quantity"] == 0 else "low stock" if i["quantity"] <= LOW_STOCK else "in stock")
        for i in p["inventory"]
    ]


def stock_message(p: dict, size: str | None = None) -> str:
    """One clear sentence about stock, built only from the inventory table."""
    name = p["name"]
    if size:
        row = next((i for i in p["inventory"] if i["size"] == size), None)
        if row is None:
            return f"{name} is not made in size {size}. Sizes offered: {', '.join(i['size'] for i in p['inventory'])}."
        if row["quantity"] == 0:
            others = [i["size"] for i in p["inventory"] if i["quantity"] > 0]
            alt = f" Still available in: {', '.join(others)}." if others else " It is sold out in every size."
            return f"OUT OF STOCK: {name} is sold out in size {size}.{alt}"
        low = " (low stock)" if row["quantity"] <= LOW_STOCK else ""
        return f"IN STOCK: {row['quantity']} of {name} in size {size}{low}."
    if p["total_stock"] == 0:
        return f"OUT OF STOCK: {name} is sold out in every size."
    out = [i["size"] for i in p["inventory"] if i["quantity"] == 0]
    msg = f"IN STOCK: {p['total_stock']} units of {name} across sizes " + ", ".join(
        f"{i['size']}={i['quantity']}" for i in p["inventory"]) + "."
    if out:
        msg += f" Sold out in: {', '.join(out)}."
    return msg


# ---------------------------------------------------------------- agent tools

def search_products(
    ctx: RunContext[ShopDeps],
    query: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    size: str | None = None,
    sort: SortOrder = "relevance",
    limit: int = 8,
) -> SearchResult:
    """Search the Campus Customs catalogue.

    Args:
        query: Keywords such as "bulldog", "navy hoodie", "hockey", "Saybrook", "Handsome Dan". Leave empty to browse.
        category: One of T-Shirts, Crewnecks, Hoodies, Long Sleeve, Quarter-Zips, Fleeces & Jackets.
        min_price: Lowest price in USD.
        max_price: Highest price in USD.
        size: Only return products with this size in stock (XS, S, M, L, XL, XXL).
        sort: relevance, price_low_to_high, price_high_to_low or name.
        limit: Number of products to return (1-12).
    """
    # Fetch every match (up to 30) for the page; send only `limit` summaries to the model.
    everything, total, note = search_catalogue(query, category, min_price, max_price, size, sort, MAX_PAGE_RESULTS)
    products = everything[: max(1, min(limit, MAX_RESULTS))]
    all_ids = [p["product_id"] for p in everything]
    ctx.deps.seen_product_ids.update(all_ids)
    ctx.deps.last_search = SearchInfo(query=query, category=resolve_category(category),
                                      total_matches=total, product_ids=all_ids)
    if total == 0 and not note:
        note = "No matching products. Tell the shopper we don't carry that and suggest the closest alternatives."
    return SearchResult(total_matches=total, products=[_summary(p) for p in products], note=note)


def get_product_details(ctx: RunContext[ShopDeps], product_id: str) -> ProductDetails | str:
    """Full details for one product: description, price, colors in the design, and stock for every size.

    Args:
        product_id: The product_id from search_products (or the product the shopper is viewing).
    """
    p = find_product(product_id)
    if p is None:
        return f"No product matching '{product_id}' in the database. Use search_products to find the right id."
    ctx.deps.seen_product_ids.add(p["product_id"])
    return ProductDetails(
        product_id=p["product_id"], name=p["name"], category=p["category"], garment_type=p["garment_type"],
        price=p["price"], description=p["description"], colors=p["colors"], tags=p["search_tags"],
        stock_by_size=size_stock(p), total_stock=p["total_stock"], stock_message=stock_message(p),
    )


def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str | None = None) -> StockCheck | str:
    """How many of a product are in stock, overall or for one size, read live from the inventory table.
    Use for "is it in stock?", "how many are left?", "do you have it in medium?".

    Args:
        product_id: The product_id (or exact product name) to check.
        size: Optional size: XS, S, M, L, XL or XXL (words like "medium" or "extra large" also work).
    """
    p = find_product(product_id)
    if p is None:
        return f"No product matching '{product_id}' in the database. Use search_products first."
    ctx.deps.seen_product_ids.add(p["product_id"])
    s = normalize_size(size)
    row = next((i for i in p["inventory"] if i["size"] == s), None) if s else None
    qty = (row["quantity"] if row else 0) if s else p["total_stock"]
    return StockCheck(
        product_id=p["product_id"], name=p["name"], price=p["price"], size_requested=s,
        available=qty > 0, quantity=qty, stock_by_size=size_stock(p),
        sizes_in_stock=[i["size"] for i in p["inventory"] if i["quantity"] > 0],
        sold_out_sizes=[i["size"] for i in p["inventory"] if i["quantity"] == 0],
        message=stock_message(p, s),
    )


def price_summary(ctx: RunContext[ShopDeps], category: str | None = None) -> PriceSummary:
    """Price facts: lowest, highest and average price, price points, and the cheapest and most
    expensive product in each category. Use for "how much", "cheapest", "price range" questions.

    Args:
        category: Limit to one category (e.g. "Hoodies", "Fleeces & Jackets"). Leave empty for the whole shop.
    """
    cat = resolve_category(category)
    products = db.list_products(category=cat) if cat else db.list_products()
    if not products:
        products, cat = db.list_products(), None
    prices = [p["price"] for p in products]
    points: dict[str, int] = {}
    for x in sorted(prices):
        points[f"{x:.2f}"] = points.get(f"{x:.2f}", 0) + 1

    by_cat: list[CategoryPrice] = []
    for name in sorted({p["category"] for p in products}):
        group = [p for p in products if p["category"] == name]
        cheap = min(group, key=lambda p: (p["price"], p["name"]))
        dear = max(group, key=lambda p: (p["price"], p["name"]))
        ctx.deps.seen_product_ids.update({cheap["product_id"], dear["product_id"]})
        gp = [p["price"] for p in group]
        by_cat.append(CategoryPrice(
            category=name, product_count=len(group), min_price=min(gp), max_price=max(gp),
            average_price=round(sum(gp) / len(gp), 2), cheapest=_summary(cheap), most_expensive=_summary(dear),
        ))
    by_cat.sort(key=lambda c: c.min_price)
    return PriceSummary(
        scope=cat or "whole shop", product_count=len(products), min_price=min(prices), max_price=max(prices),
        average_price=round(sum(prices) / len(prices), 2), price_points=points, by_category=by_cat,
    )


def list_categories(ctx: RunContext[ShopDeps]) -> list[dict]:
    """All product categories with product counts and starting prices."""
    return db.list_categories()


# ---------------------------------------------------------------- search-box suggestions (no model)

POPULAR_SEARCHES = ["Hoodies", "Bulldog", "Crewnecks", "T-Shirts", "Quarter-Zips", "Fleece", "Hockey", "The Game"]


def suggest(q: str, limit: int = 6) -> dict:
    """Type-ahead for the search box: matching categories, keyword ideas and top products.
    Pure database lookup, so it is instant and costs nothing."""
    q = _norm(q or "")
    if len(q) < 2:
        return {"query": q, "categories": [], "terms": POPULAR_SEARCHES[:6], "products": [], "total_matches": 0}

    cats = [c for c in db.list_categories()
            if q in c["name"].lower() or c["name"].lower().startswith(q[:4])
            or (resolve_category(q) or "").lower() == c["name"].lower()]

    # Keyword ideas: tags / name words that start with (or contain) what was typed.
    seen: dict[str, int] = {}
    for p in db.list_products():
        for t in p["search_tags"] + [p["name"]]:
            tl = t.lower()
            if tl.startswith(q) or f" {q}" in f" {tl}":
                key = t.strip()
                if key.lower() != q and len(key) <= 32:
                    seen[key] = seen.get(key, 0) + 1
    terms = sorted(seen, key=lambda k: (-seen[k], len(k)))
    dedup: list[str] = []
    for t in terms:
        if t.lower() not in {d.lower() for d in dedup}:
            dedup.append(t)
        if len(dedup) >= 4:
            break

    products, total, _ = search_catalogue(query=q, limit=limit)
    return {
        "query": q,
        "categories": [{"name": c["name"], "count": c["count"], "min_price": c["min_price"]} for c in cats[:3]],
        "terms": dedup,
        "products": [{"product_id": p["product_id"], "name": p["name"], "category": p["category"],
                      "price": p["price"], "image_url": p["image_url"], "total_stock": p["total_stock"]}
                     for p in products],
        "total_matches": total,
    }


# ---------------------------------------------------------------- customer memory tools
# Both read ctx.deps.user_id, which the server sets from the login cookie. The model can't pass
# a user id, so it can only ever see the logged-in shopper's own profile and chats.

def _product_label(pid: str) -> str:
    p = db.get_product(pid)
    return f"{p['name']} ({pid})" if p else pid


def get_shopper_profile(ctx: RunContext[ShopDeps]) -> ShopperProfile:
    """Who is chatting: the logged-in shopper's name, email, member-since date, how many messages
    they have saved, and products shown to them recently. Guests get logged_in=false."""
    d = ctx.deps
    if d.user_id is None:
        return ShopperProfile(logged_in=False)
    rows = db.load_chat_history(d.user_id, limit=40)
    recent: list[str] = []
    for r in reversed(rows):
        for pid in r["product_ids"]:
            p = db.get_product(pid)
            if p and p["name"] not in recent:
                recent.append(p["name"])
    return ShopperProfile(
        logged_in=True, first_name=d.first_name, last_name=d.last_name, email=d.email,
        member_since=d.member_since, saved_messages=db.count_chat_messages(d.user_id), recent_products=recent[:10],
    )


def recall_chat_history(ctx: RunContext[ShopDeps], query: str | None = None, limit: int = 10) -> ChatRecall:
    """Look back through THIS shopper's saved chats from earlier visits, e.g. "what was that hoodie
    you showed me last time?" or "did I ask about fleeces before?". Newest first.

    Args:
        query: Optional word to look for in past messages or products shown (e.g. "hoodie", "bulldog").
        limit: How many messages to return (1-20).
    """
    d = ctx.deps
    if d.user_id is None:
        return ChatRecall(logged_in=False, total_found=0, messages=[],
                          note="Guest chats are not saved. Suggest logging in so chats are remembered next time.")
    rows, total = db.search_chat_history(d.user_id, query, max(1, min(limit, 20)))
    msgs = []
    for r in rows:
        ctx.deps.seen_product_ids.update(r["product_ids"])
        viewing = (r.get("context") or {}).get("product_id")
        msgs.append(PastMessage(
            role=r["role"] if r["role"] in ("user", "assistant") else "assistant",
            content=r["content"][:600], created_at=r["created_at"],
            products_shown=[_product_label(pid) for pid in r["product_ids"][:8]],
            viewing=_product_label(viewing) if viewing else None,
        ))
    return ChatRecall(logged_in=True, total_found=total, messages=msgs,
                      note=None if msgs else "No saved messages match. Say so honestly.")


# ---------------------------------------------------------------- usability feedback

def log_usability_feedback(ctx: RunContext[ShopDeps], feedback: str, adjustment: str) -> str:
    """Record that the shopper asked for a better experience, and the adjustment you are making.
    Call this whenever the shopper says something is confusing, too long, hard to find or hard to read,
    or asks you to change how you answer. The note goes to the audit trail for the Campus Customs team.

    Args:
        feedback: What the shopper found difficult, in a few words (e.g. "answers too long").
        adjustment: What you are changing for them now (e.g. "shorter answers, max 3 items").
    """
    audit.append_events([{
        "time": audit.now(), "run_id": ctx.deps.run_id, "event": "ux_feedback",
        "who": f"user:{ctx.deps.user_id}" if ctx.deps.user_id else "guest",
        "page": ctx.deps.page.page if ctx.deps.page else None,
        "feedback": audit.short(feedback, 200), "adjustment": audit.short(adjustment, 200),
    }])
    return "Noted for the Campus Customs team. Apply the adjustment for the rest of this conversation."


SHOP_TOOLS = [
    search_products, get_product_details, check_stock, price_summary, list_categories,
    get_shopper_profile, recall_chat_history, log_usability_feedback,
]
