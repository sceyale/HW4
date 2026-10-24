"""End-to-end check that the core Campus Customs shop works (Problem 9).

Start the app first (two terminals):
    cd backend  && uvicorn main:app --reload --port 8000
    cd frontend && npm run dev

Then, from backend/:
    python verify_shop.py              # everything, including 3 short chatbot calls (uses the API key)
    python verify_shop.py --no-chat    # skip the chatbot (no API cost)

Creates one test account (verify.<timestamp>@yale.edu) in the real database.
"""

from __future__ import annotations

import http.cookiejar
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://localhost:8000"
WEB = "http://localhost:5173"
DB = Path(__file__).resolve().parent.parent / "data" / "campus_customs.db"
TEST_EMAIL, TEST_PASSWORD = "test@campuscustoms.yale.edu", "password"

results: list[tuple[str, bool, str]] = []
section = ""


def check(ok, label: str, detail: str = "") -> bool:
    results.append((section, bool(ok), label))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  ({detail})" if detail else ""))
    return bool(ok)


def head(name: str) -> None:
    global section
    section = name
    print(f"\n== {name} ==")


def client():
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def call(opener, method: str, url: str, body=None, timeout: float = 60):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with opener.open(req, timeout=timeout) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
            data = json.loads(raw) if raw and "json" in ctype else raw
            return r.status, data, ctype
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return e.code, json.loads(raw), ""
        except ValueError:
            return e.code, raw, ""
    except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
        return 0, str(e), ""


def sql(q: str, *args):
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as c:
        return c.execute(q, args).fetchall()


def main() -> int:
    chat = "--no-chat" not in sys.argv
    c = client()

    head("1. Backend is running")
    s, d, _ = call(c, "GET", f"{API}/api/health", timeout=5)
    if not check(s == 200 and isinstance(d, dict) and d.get("status") == "ok", "GET /api/health", f"status {s}"):
        print("\n  Start it from backend/:  uvicorn main:app --reload --port 8000")
        return summary()

    head("2. Products and prices come from the database")
    s, products, _ = call(c, "GET", f"{API}/api/products")
    n_db = sql("SELECT COUNT(*) FROM catalogue")[0][0]
    check(s == 200 and len(products) == n_db, "GET /api/products returns every catalogue item", f"{len(products)} of {n_db}")
    prices = dict(sql("SELECT product_id, price FROM catalogue"))
    check(all(p["price"] == prices[p["product_id"]] for p in products), "every price matches the catalogue table")
    stock = dict(sql("SELECT product_id, SUM(quantity) FROM inventory GROUP BY product_id"))
    check(all(p["total_stock"] == stock[p["product_id"]] for p in products), "every total_stock matches SUM(inventory)")
    check(all(p["name"] and p["description"] and p["image_url"] for p in products), "every product has name, description, image")
    s, cats, _ = call(c, "GET", f"{API}/api/categories")
    check(s == 200 and sum(x["count"] for x in cats) == n_db, "categories cover all products", ", ".join(x["name"] for x in cats))
    s, hood, _ = call(c, "GET", f"{API}/api/products?category=Hoodies")
    check(s == 200 and hood and all(p["category"] == "Hoodies" for p in hood), "category filter works", f"{len(hood)} hoodies")

    head("2b. Search box (Problem 9)")
    s, sg, _ = call(c, "GET", f"{API}/api/suggest?q=")
    check(s == 200 and sg["terms"], "empty search box shows popular searches", ", ".join(sg.get("terms", [])[:4]) if s == 200 else "")
    t0 = time.time()
    s, sg, _ = call(c, "GET", f"{API}/api/suggest?q=hoo")
    ms = (time.time() - t0) * 1000
    check(s == 200 and any(x["name"] == "Hoodies" for x in sg["categories"]) and sg["products"],
          "typing 'hoo' suggests Hoodies + products", f"{ms:.0f} ms")
    check(ms < 500, "suggestions are fast enough for type-ahead (< 500 ms)", f"{ms:.0f} ms")
    s, res, _ = call(c, "GET", f"{API}/api/products?q=bulldog")
    check(s == 200 and res and all("bulldog" in (p["name"] + p["description"] + " ".join(p["search_tags"])).lower() for p in res),
          "Enter in the search box: /api/products?q=bulldog returns ranked bulldog items", f"{len(res) if s == 200 else 0}")

    head("3. Single item page data")
    pid = "basic-hoodie-big-yale"
    s, p, _ = call(c, "GET", f"{API}/api/products/{pid}")
    sizes = [i["size"] for i in p["inventory"]] if s == 200 else []
    check(s == 200 and sizes == ["XS", "S", "M", "L", "XL", "XXL"], "product detail has stock for XS to XXL", ", ".join(sizes))
    s, _, _ = call(c, "GET", f"{API}/api/products/not-a-real-product")
    check(s == 404, "unknown product returns 404")
    missing = [x["product_id"] for x in products if call(c, "GET", API + x["image_url"], timeout=10)[2] != "image/jpeg"]
    check(not missing, "all product images load (image/jpeg)", f"{len(products) - len(missing)} of {len(products)}"
          + (f"; missing: {', '.join(missing[:3])}" if missing else ""))

    head("4. Website (Vite) and its link to the API")
    s, html, _ = call(client(), "GET", WEB + "/", timeout=5)
    if check(s == 200 and b'id="root"' in (html if isinstance(html, bytes) else b""), "frontend serves index.html on :5173",
             "" if s == 200 else "start it from frontend/: npm run dev"):
        s, d, _ = call(client(), "GET", f"{WEB}/api/products/{pid}")
        check(s == 200 and isinstance(d, dict) and d.get("product_id") == pid, "Vite proxy forwards /api to FastAPI")
        s, _, ctype = call(client(), "GET", f"{WEB}/media/products/{pid}.jpg")
        check(s == 200 and ctype == "image/jpeg", "Vite proxy forwards /media images")
        for route in ("/products", f"/products/{pid}", "/about", "/login", "/create-account"):
            s, _, _ = call(client(), "GET", WEB + route, timeout=5)
            check(s == 200, f"page route {route} loads")

    head("5. Accounts: log in, create account, log out")
    u = client()
    s, me, _ = call(u, "POST", f"{API}/api/auth/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
    check(s == 200 and me.get("email") == TEST_EMAIL, "seeded test user logs in", f"status {s}")
    check(s == 200 and "password_hash" not in me, "login response never includes the password hash")
    s, me, _ = call(u, "GET", f"{API}/api/auth/me")
    check(s == 200 and me.get("first_name") == "Test", "session cookie keeps the shopper logged in (/me)")
    s, _, _ = call(client(), "POST", f"{API}/api/auth/login", {"email": TEST_EMAIL, "password": "wrong-password"})
    check(s == 401, "wrong password is rejected (401)")
    email, pw = f"verify.{int(time.time())}@yale.edu", "BoolaBoola1975"
    n = client()
    s, _, _ = call(n, "POST", f"{API}/api/auth/register",
                   {"first_name": "Verify", "last_name": "Bulldog", "email": email, "password": pw, "confirm_password": pw[:-1]})
    check(s == 400, "create account rejects mismatched confirm password")
    s, nu, _ = call(n, "POST", f"{API}/api/auth/register",
                    {"first_name": "Verify", "last_name": "Bulldog", "email": email, "password": pw, "confirm_password": pw})
    check(s == 201, "create account works", email)
    row = sql("SELECT password_hash FROM users WHERE email = ?", email)
    check(row and row[0][0].startswith("pbkdf2_sha256$") and pw not in row[0][0], "new user saved with a hashed password")
    s, _, _ = call(n, "POST", f"{API}/api/auth/register",
                   {"first_name": "Verify", "last_name": "Bulldog", "email": email, "password": pw, "confirm_password": pw})
    check(s == 409, "duplicate email is rejected (409)")
    s, _, _ = call(n, "POST", f"{API}/api/auth/logout")
    s2, _, _ = call(n, "GET", f"{API}/api/auth/me")
    check(s == 204 and s2 == 401, "log out ends the session")
    s, _, _ = call(client(), "POST", f"{API}/api/auth/login", {"email": email, "password": pw})
    check(s == 200, "the brand-new account can log back in")

    if chat:
        head("6. Shop assistant (PydanticAI agent)")
        g = client()
        t0 = time.time()
        s, r, _ = call(g, "POST", f"{API}/api/chat", {"message": "What hoodies do you have?",
                                                     "page": {"path": "/", "page": "home", "visible_product_ids": []}}, timeout=90)
        if s == 503:
            check(False, "chat is available", "503: check OPENAI_API_KEY in the root .env and the server log")
        else:
            secs = time.time() - t0
            cats_shown = {p["category"] for p in r.get("products", [])} if s == 200 else set()
            check(s == 200 and r.get("reply"), "guest chat gets a reply", f"{secs:.1f}s")
            check(s == 200 and r.get("display") == "search_results" and cats_shown == {"Hoodies"},
                  "'What hoodies do you have?' -> page shows hoodie cards", f"{len(r.get('products', []))} cards, display={r.get('display')}")
            check(s == 200 and all(p["product_id"] in prices for p in r.get("products", [])), "every card is a real catalogue product")

            out_pid, out_size = sql("SELECT product_id, size FROM inventory WHERE quantity = 0 ORDER BY product_id LIMIT 1")[0]
            out_name = sql("SELECT name FROM catalogue WHERE product_id = ?", out_pid)[0][0]
            s, r, _ = call(u, "POST", f"{API}/api/chat", {"message": f"Do you have this in size {out_size}?",
                           "page": {"path": f"/products/{out_pid}", "page": "product", "product_id": out_pid,
                                    "visible_product_ids": []}}, timeout=90)
            reply = (r.get("reply") or "").lower() if s == 200 else ""
            check(s == 200 and ("sold out" in reply or "out of stock" in reply),
                  "sold-out size is stated clearly (page context: 'this')", f"{out_name} {out_size}: {reply[:90]}")
            check(s == 200 and r.get("saved") is True, "logged-in turn is saved to chat_messages")

            s, r, _ = call(u, "POST", f"{API}/api/chat", {"message": "do you have this shirt in pink?",
                           "page": {"path": "/products/baseball-left-chest-crewneck", "page": "product",
                                    "product_id": "baseball-left-chest-crewneck", "visible_product_ids": []}}, timeout=90)
            reply = (r.get("reply") or "").lower() if s == 200 else ""
            check(s == 200 and "pink" in reply and ("navy" in reply or "don't" in reply or "do not" in reply or "only" in reply),
                  "'this shirt in pink?' answered about the open item", reply[:90])

            s, hist, _ = call(u, "GET", f"{API}/api/chat/history")
            check(s == 200 and len(hist) >= 4 and hist[-1]["role"] == "assistant", "history reloads for the returning shopper",
                  f"{len(hist) if s == 200 else 0} messages")
    else:
        print("\n== 6. Shop assistant == skipped (--no-chat)")

    return summary()


def summary() -> int:
    passed = sum(ok for _, ok, _ in results)
    print(f"\n{'=' * 60}\n{passed}/{len(results)} checks passed")
    for sec, ok, label in results:
        if not ok:
            print(f"  FAIL  [{sec}] {label}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
