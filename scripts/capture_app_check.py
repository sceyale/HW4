"""Take the 3 app-check screenshots automatically (no browser extension needed).

Uses Playwright to drive your installed Google Chrome (or Playwright's Chromium),
saves PNGs to output/app_check_images/, then opens output/app_check.html.

Setup (once):
    pip install playwright
    # only needed if Google Chrome isn't installed:
    python -m playwright install chromium

Run (with the backend on :8000 and the frontend on :5173 already running):
    python scripts/capture_app_check.py
    python scripts/capture_app_check.py --show      # watch it work in a visible window
"""

from __future__ import annotations

import json
import sys
import urllib.request
import webbrowser
from pathlib import Path

from playwright.sync_api import Error as PWError, Page, TimeoutError as PWTimeout, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "app_check_images"
REPORT = ROOT / "output" / "app_check.html"
WEB = "http://localhost:5173"
API = "http://localhost:8000"
VIEWPORT = {"width": 2048, "height": 1180}   # wide enough that the chat panel doesn't cover the page
TEST_EMAIL, TEST_PASSWORD = "test@campuscustoms.yale.edu", "password"
STOCK_ITEM = "baseball-left-chest-crewneck"   # has an in-stock size and a sold-out size


def ok(msg: str) -> None:
    print(f"  ✓ {msg}")


def preflight() -> None:
    for url, name, fix in [
        (f"{API}/api/health", "backend", "cd backend && uvicorn main:app --reload --port 8000"),
        (WEB, "frontend", "cd frontend && npm run dev"),
    ]:
        try:
            urllib.request.urlopen(url, timeout=5)
            ok(f"{name} is running ({url})")
        except Exception:
            sys.exit(f"✗ The {name} is not running at {url}. Start it with:\n    {fix}")


def launch(p, show: bool):
    for kwargs in ({"channel": "chrome"}, {}):           # installed Chrome first, then Playwright Chromium
        try:
            return p.chromium.launch(headless=not show, **kwargs)
        except PWError:
            continue
    sys.exit("✗ No browser found. Run:  python -m playwright install chromium")


def ask_chat(page: Page, question: str, timeout_s: int = 90) -> str:
    """Open the chat (if closed), send a question, wait for the assistant's reply, return its text."""
    if page.locator(".chat__panel").count() == 0:
        page.get_by_role("button", name="Open chat").click()
    before = page.locator(".chat__turn--assistant").count()
    box = page.get_by_label("Message")
    box.fill(question)
    box.press("Enter")
    page.wait_for_function(
        "n => document.querySelectorAll('.chat__turn--assistant').length > n && !document.querySelector('.chat__typing')",
        arg=before, timeout=timeout_s * 1000,
    )
    reply = page.locator(".chat__turn--assistant").last.inner_text()
    if page.locator(".chat__msg--error").count():
        sys.exit(f"✗ The chat returned an error: {reply}\n  Check OPENAI_API_KEY in .env and the backend terminal.")
    page.wait_for_timeout(1200)                           # let cards/images and scrolling settle
    return reply


def log_in(page: Page) -> None:
    page.goto(f"{WEB}/login")
    page.get_by_label("Email").fill(TEST_EMAIL)
    page.get_by_label("Password").fill(TEST_PASSWORD)
    page.get_by_role("button", name="Log In").click()
    page.wait_for_url("**/products", timeout=15000)
    ok("logged in as the seeded test user")


def main() -> None:
    show = "--show" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    print("Checking servers…")
    preflight()

    with sync_playwright() as p:
        browser = launch(p, show)
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1)
        # Hide the 8-second chat pop-up so it doesn't cover the screenshots.
        ctx.add_init_script("try { sessionStorage.setItem('cc_chat_nudged', '1'); } catch (e) {}")
        page = ctx.new_page()

        # ---- 3. Usability: type-ahead search suggestions -------------------------------
        print("\n3. Search suggestions (usability feature)…")
        page.goto(WEB)
        page.wait_for_load_state("networkidle")
        search = page.get_by_label("Search products")
        search.click()
        page.wait_for_timeout(400)
        assert page.locator(".search__panel").count() == 0, "dropdown should stay hidden until typing"
        ok("dropdown hidden before typing")
        search.type("hoo", delay=120)
        page.wait_for_selector(".search__opt--product img", timeout=10000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT / "usability_search.png"))
        ok(f"saved {OUT.name}/usability_search.png")
        search.press("Escape")

        # ---- 1. Chat checks inventory level --------------------------------------------
        print("\n1. Chat checks inventory…")
        log_in(page)
        page.goto(f"{WEB}/products/{STOCK_ITEM}")
        page.wait_for_selector(".sizes")
        page.locator(".detail__h", has_text="Sizes").scroll_into_view_if_needed()
        page.mouse.wheel(0, 250)
        reply = ask_chat(page, "How many of this do you have in size M? And is XS available?")
        ok(f"reply: {reply[:110]}…")
        with urllib.request.urlopen(f"{API}/api/products/{STOCK_ITEM}") as r:
            inv = {i['size']: i['quantity'] for i in json.load(r)["inventory"]}
        ok(f"database says M={inv.get('M')}, XS={inv.get('XS')}")
        page.screenshot(path=str(OUT / "inventory.png"))
        ok(f"saved {OUT.name}/inventory.png")

        # ---- 2. Dynamic search cards after a category question --------------------------
        print("\n2. Category question → product cards…")
        page.goto(WEB)
        page.wait_for_load_state("networkidle")
        reply = ask_chat(page, "What hoodies do you have?")
        page.wait_for_url("**/products**", timeout=15000)
        page.wait_for_selector(".chat-matches .product-card img", timeout=15000)
        page.locator(".chat-matches").scroll_into_view_if_needed()
        page.wait_for_timeout(1500)
        n = page.locator(".chat-matches .product-card").count()
        ok(f"{n} product cards on the page; reply: {reply[:90]}…")
        page.screenshot(path=str(OUT / "search_cards.png"))
        ok(f"saved {OUT.name}/search_cards.png")

        browser.close()

    print(f"\nDone. Opening {REPORT.relative_to(ROOT)} …")
    webbrowser.open(REPORT.as_uri())


if __name__ == "__main__":
    try:
        main()
    except PWTimeout as e:
        sys.exit(f"✗ Timed out waiting for the page: {e}\n  Try again with --show to watch what happens.")
