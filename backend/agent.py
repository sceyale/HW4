"""Campus Customs shop agent: entry point and wiring.

How the agent is loaded
-----------------------
1. load_env() walks up from backend/ and reads the first .env it finds
   (the AI Foundations root .env), so OPENAI_API_KEY is available.
2. get_agent() builds the PydanticAI Agent the first time a chat arrives, then reuses it.
   The server can therefore start (and serve products and login) even without a key.
3. The agent gets:
     - instructions : prompts/prompt.md, plus a live block with who is chatting and what is on their screen
     - tools        : tools.SHOP_TOOLS (search, details, prices, categories), all read-only
     - deps         : models.ShopDeps (safe shopper info, plus the products tools returned)
     - output_type  : models.ShopReply (reply text + product_ids to show as cards)
"""

from __future__ import annotations

import os
from pathlib import Path

import time

from pydantic_ai import Agent, RunContext, UsageLimitExceeded, capture_run_messages
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.usage import UsageLimits

import audit
import db
from models import ChatResponse, PageContext, ProductCard, ShopDeps, ShopReply
from tools import SHOP_TOOLS

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
HISTORY_TURNS = 12          # past messages sent to the model (keeps cost low)
MAX_SHOWN = 8              # cards for a specific answer
MAX_PAGE = 30              # cards for a browse search


def load_env() -> Path | None:
    """Read the nearest .env walking up from backend/ (the AI Foundations root .env).

    .env values win over old values in the terminal, so a stale exported key can't override it.
    """
    for folder in (BACKEND_DIR, *BACKEND_DIR.parents):
        path = folder / ".env"
        if path.is_file():
            for line in path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"').strip("'")
            return path
    return None


ENV_PATH = load_env()
MODEL_ID = os.getenv("CHAT_MODEL", "gpt-5.6-luna")
REASONING_EFFORT = os.getenv("CHAT_REASONING", "low")


class AgentUnavailable(Exception):
    """The agent can't run (missing key, model error). The API turns this into a friendly 503."""


def make_model():
    from openai import AsyncOpenAI
    from pydantic_ai.models.openai import OpenAIChatModel
    from pydantic_ai.providers.openai import OpenAIProvider

    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        raise AgentUnavailable(f"OPENAI_API_KEY is missing (looked in {ENV_PATH or 'no .env found'}).")
    client = AsyncOpenAI(api_key=key, max_retries=2)
    return OpenAIChatModel(MODEL_ID, provider=OpenAIProvider(openai_client=client))


def build_agent() -> Agent[ShopDeps, ShopReply]:
    agent = Agent(
        make_model(),
        deps_type=ShopDeps,
        output_type=ShopReply,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=SHOP_TOOLS,
        model_settings={"openai_reasoning_effort": REASONING_EFFORT},
        retries=2,
        name="campus_customs_shop",
    )

    @agent.instructions
    def shopper_and_page(ctx: RunContext[ShopDeps]) -> str:
        return describe_context(ctx.deps)

    return agent


PAGE_NAMES = {
    "home": "Home page", "products": "Products page (catalogue grid)", "product": "a single item page",
    "about": "About Us page", "login": "Log In page", "create-account": "Create Account page", "other": "another page",
}


def _short(pid: str) -> str | None:
    p = db.get_product(pid)
    if not p:
        return None
    stock = "SOLD OUT" if p["total_stock"] == 0 else f"{p['total_stock']} in stock"
    return f"{p['name']} (product_id: {pid}; ${p['price']:.0f}; design colors: {', '.join(p['colors'])}; {stock})"


def describe_context(d: ShopDeps) -> str:
    """The live 'who + where' block added to the instructions on every turn."""
    lines = ["## Who is chatting"]
    if d.user_id is not None:
        name = " ".join(x for x in (d.first_name, d.last_name) if x) or "unknown"
        lines += [f"- Logged-in shopper: {name}", f"- Email: {d.email}",
                  f"- Member since: {d.member_since}",
                  "- Their chats are saved. Use recall_chat_history for earlier visits."]
    else:
        lines += ["- A guest (not logged in). Nothing is saved after they leave.",
                  "- If they want you to remember things, suggest Create Account / Log In."]

    lines.append("\n## What is on their screen right now")
    page = d.page or PageContext()
    lines.append(f"- Page: {PAGE_NAMES.get(page.page, 'another page')}" + (f" ({page.path})" if page.path else ""))
    if d.current_product_id and (desc := _short(d.current_product_id)):
        lines.append(f"- Item open on the page: {desc}")
        lines.append("  -> 'this', 'it', 'this shirt/hoodie' = THIS item unless they clearly mean another.")
    if page.category:
        lines.append(f"- Category filter selected: {page.category}")
    visible = [x for pid in page.visible_product_ids[:12] if (x := _short(pid))]
    if visible:
        lines.append("- Product cards visible on the page (top first):")
        lines += [f"  {i}. {v}" for i, v in enumerate(visible, 1)]
        lines.append("  -> 'these', 'the first one', 'the gray one' refer to these cards.")
    lines.append("- If it is still unclear which item they mean, ask one short question instead of guessing.")
    return "\n".join(lines)


_agent: Agent[ShopDeps, ShopReply] | None = None


def get_agent() -> Agent[ShopDeps, ShopReply]:
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


def to_model_history(turns: list[dict]) -> list[ModelMessage]:
    """Saved/browser turns -> PydanticAI messages. Shown products are noted so follow-ups work."""
    messages: list[ModelMessage] = []
    for t in turns[-HISTORY_TURNS:]:
        if t["role"] == "user":
            text = t["content"]
            viewing = (t.get("context") or {}).get("product_id")
            if viewing:
                text += f"\n\n[Shopper was viewing: {viewing}]"
            messages.append(ModelRequest(parts=[UserPromptPart(content=text)]))
        else:
            text = t["content"]
            shown = t.get("product_ids") or []
            if shown:
                text += "\n\n[Products shown on the page: " + ", ".join(shown) + "]"
            messages.append(ModelResponse(parts=[TextPart(content=text)]))
    return messages


def build_deps(user: dict | None, page: PageContext | None) -> ShopDeps:
    """Shopper fields come from the server-side session (never the browser); page from the request."""
    page = page or PageContext()
    pid = page.product_id if page.product_id and db.get_product(page.product_id) else None
    page.visible_product_ids = [x for x in dict.fromkeys(page.visible_product_ids) if db.get_product(x)][:30]
    deps = ShopDeps(page=page, current_product_id=pid)
    if user:
        deps.user_id, deps.first_name, deps.last_name = user["id"], user.get("first_name"), user.get("last_name")
        deps.email, deps.member_since = user.get("email"), user.get("created_at")
    # Items already on screen may be shown again without a new search.
    deps.seen_product_ids.update(page.visible_product_ids)
    if pid:
        deps.seen_product_ids.add(pid)
    return deps


async def run_chat(
    message: str,
    *,
    user: dict | None = None,
    page: PageContext | None = None,
    history: list[dict] | None = None,
) -> ChatResponse:
    """Run one chat turn and return the reply plus product cards for the page."""
    history = history or []
    deps = build_deps(user, page)
    deps.run_id = audit.new_run_id()
    for t in history[-HISTORY_TURNS:]:
        deps.seen_product_ids.update(t.get("product_ids") or [])

    model_history = to_model_history(history)
    started = time.perf_counter()
    pg = deps.page or PageContext()
    audit.append_events([{
        "time": audit.now(), "run_id": deps.run_id, "event": "run_start",
        "who": f"user:{deps.user_id}" if deps.user_id else "guest",
        "message": audit.short(message, 200), "page": pg.page, "product_id": deps.current_product_id,
        "history_turns": len(model_history), "model": MODEL_ID,
    }])

    stop_reason, error, out = "final_result", None, None
    with capture_run_messages() as run_messages:
        try:
            result = await get_agent().run(
                message,
                deps=deps,
                message_history=model_history,
                usage_limits=UsageLimits(request_limit=6),
            )
            out = result.output
        except UsageLimitExceeded as e:
            stop_reason, error = "usage_limit", str(e)
        except (ModelHTTPError, ModelAPIError) as e:
            stop_reason, error = "model_error", str(e)
        except Exception as e:  # noqa: BLE001  (logged, then re-raised)
            stop_reason, error = "error", f"{type(e).__name__}: {e}"
            _finish_audit(deps, run_messages, len(model_history), started, stop_reason, error, None)
            raise
    response = _to_response(out, deps) if out is not None else None
    _finish_audit(deps, run_messages, len(model_history), started, stop_reason, error, response)

    if stop_reason == "usage_limit":
        return ChatResponse(reply="Sorry, that one took me too long. Could you ask it a little more simply?")
    if stop_reason == "model_error":
        raise AgentUnavailable(f"Model error: {error}")
    return response  # type: ignore[return-value]


def _finish_audit(deps: ShopDeps, run_messages: list, n_history: int, started: float,
                  stop_reason: str, error: str | None, response: ChatResponse | None) -> None:
    """Write this run's model/tool events and a run_end summary to the audit trail."""
    new_msgs = run_messages[n_history:] if len(run_messages) >= n_history else run_messages
    events, counts = audit.events_from_messages(deps.run_id, new_msgs)
    events.append({
        "time": audit.now(), "run_id": deps.run_id, "event": "run_end",
        "stop_reason": stop_reason, "error": audit.short(error, 200) if error else None,
        "duration_ms": round((time.perf_counter() - started) * 1000),
        **counts,
        "display": response.display if response else None,
        "products_shown": [c.product_id for c in response.products][:12] if response else [],
        "reply": audit.short(response.reply, 200) if response else None,
    })
    try:
        audit.append_events(events)
    except OSError as e:  # never break a chat because the log can't be written
        print(f"[audit] could not write audit trail: {e}")


def _to_response(out: ShopReply, deps: ShopDeps) -> ChatResponse:
    search = deps.last_search
    if out.show_search_results and search and search.product_ids:
        # Browsing ("what hoodies do you have?"): show every match from the latest search.
        ids, display, limit = search.product_ids, "search_results", MAX_PAGE
    else:
        # A specific answer: show only the items the agent picked.
        ids, display, limit = out.product_ids, "selected", MAX_SHOWN

    cards: list[ProductCard] = []
    for pid in dict.fromkeys(ids):                          # keep order, drop duplicates
        if pid in deps.seen_product_ids and (p := db.get_product(pid)):  # only real, looked-up products
            cards.append(ProductCard.from_product(p))
        if len(cards) >= limit:
            break
    return ChatResponse(
        reply=out.reply.strip(),
        products=cards,
        display=display if cards else "none",
        search=search if display == "search_results" and cards else None,
    )
