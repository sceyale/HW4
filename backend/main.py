"""Campus Customs API: products, accounts and the shop chatbot.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000

The React frontend (Vite, port 5173) forwards /api and /media here (see frontend/vite.config.ts).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import agent as shop_agent
import auth
import db
import tools
from models import (
    Category,
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    PageContext,
    Product,
    ProductCard,
    RegisterRequest,
    Suggestions,
    User,
)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    auth.init_auth_tables()
    db.init_chat_tables()
    yield


app = FastAPI(title="Campus Customs API", version="0.3.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Product photos: data/products/<id>.jpg  ->  /media/products/<id>.jpg
app.mount("/media", StaticFiles(directory=db.DATA_DIR), name="media")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# ---------------------------------------------------------------- products

@app.get("/api/products", response_model=list[Product])
def products(category: str | None = None, q: str | None = None):
    """All products, or a ranked keyword search (same ranking as the agent's search tool)."""
    if q and q.strip():
        found, _, _ = tools.search_catalogue(query=q, category=category, limit=500, max_limit=500)
        return found
    return db.list_products(category=tools.resolve_category(category) if category else None)


@app.get("/api/suggest", response_model=Suggestions)
def suggest(q: str = ""):
    """Search-box type-ahead: categories, keyword ideas and top products. No AI call, so it's instant."""
    return tools.suggest(q[:60])


@app.get("/api/products/{product_id}", response_model=Product)
def product(product_id: str):
    item = db.get_product(product_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


@app.get("/api/categories", response_model=list[Category])
def categories():
    return db.list_categories()


# ---------------------------------------------------------------- accounts

# Set COOKIE_SECURE=1 when serving over HTTPS so the cookie is never sent unencrypted.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") == "1"


def _start_session(response: Response, user: dict) -> dict:
    token = auth.create_session(user["id"])
    response.set_cookie(
        auth.SESSION_COOKIE, token,
        max_age=auth.SESSION_DAYS * 24 * 3600,
        httponly=True,          # not readable by JavaScript
        samesite="lax",         # not sent on cross-site POSTs
        secure=COOKIE_SECURE,
        path="/",
    )
    return user


@app.post("/api/auth/register", response_model=User, status_code=201)
def register(body: RegisterRequest, response: Response):
    try:
        user = auth.register(body.first_name, body.last_name, body.email, body.password, body.confirm_password)
    except auth.AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _start_session(response, user)


@app.post("/api/auth/login", response_model=User)
def login(body: LoginRequest, response: Response):
    try:
        user = auth.login(body.email, body.password)
    except auth.AuthError as e:
        raise HTTPException(status_code=e.status, detail=e.message)
    return _start_session(response, user)


@app.post("/api/auth/logout", status_code=204)
def logout(response: Response, cc_session: str | None = Cookie(default=None)):
    auth.delete_session(cc_session)
    response.delete_cookie(auth.SESSION_COOKIE, path="/")


@app.get("/api/auth/me", response_model=User)
def me(cc_session: str | None = Cookie(default=None)):
    user = auth.user_for_session(cc_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    return user


# ---------------------------------------------------------------- chat (PydanticAI agent)

@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, cc_session: str | None = Cookie(default=None)):
    """One chat turn.

    Logged in: the shopper comes from the session cookie, history is loaded from chat_messages,
               and the turn is saved (message + page context + reply + cards shown).
    Guest:     the browser sends its recent turns; nothing is saved.
    """
    user = auth.user_for_session(cc_session)
    page = body.page or PageContext()
    if body.current_product_id and not page.product_id:
        page.product_id = body.current_product_id
    if user:
        history = db.load_chat_history(user["id"], limit=shop_agent.HISTORY_TURNS)
    else:
        history = [{"role": h.role, "content": h.content} for h in body.history]

    message = body.message.strip()
    try:
        result = await shop_agent.run_chat(message, user=user, page=page, history=history)
    except shop_agent.AgentUnavailable as e:
        print(f"[chat] agent unavailable: {e}")  # details stay in the server log
        raise HTTPException(status_code=503, detail="The shop assistant is unavailable right now. Please try again shortly.")

    if user:
        context = {"page": page.page, "path": page.path, "product_id": page.product_id, "category": page.category}
        db.save_chat_turn(user["id"], message, result.reply,
                          [c.model_dump() for c in result.products],
                          {k: v for k, v in context.items() if v})
        result.saved = True
    return result


@app.get("/api/chat/history", response_model=list[ChatHistoryItem])
def chat_history(cc_session: str | None = Cookie(default=None)):
    """The logged-in shopper's saved chat, with product cards rebuilt from the live catalogue."""
    user = auth.user_for_session(cc_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Log in to see your chat history")
    items = []
    for m in db.load_chat_history(user["id"]):
        cards = [ProductCard.from_product(p) for pid in m["product_ids"] if (p := db.get_product(pid))]
        items.append(ChatHistoryItem(id=m["id"], role=m["role"], content=m["content"],
                                     products=cards, created_at=m["created_at"]))
    return items


@app.delete("/api/chat/history", status_code=204)
def clear_history(cc_session: str | None = Cookie(default=None)):
    user = auth.user_for_session(cc_session)
    if user is None:
        raise HTTPException(status_code=401, detail="Not logged in")
    db.clear_chat_history(user["id"])
