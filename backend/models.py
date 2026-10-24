"""Pydantic / PydanticAI structured types for the Campus Customs API and shop agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------- catalogue (API responses)


class InventoryItem(BaseModel):
    size: str
    quantity: int


class Product(BaseModel):
    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_file_path: str
    image_url: str
    price: float
    inventory: list[InventoryItem]
    total_stock: int


class Category(BaseModel):
    name: str
    count: int
    min_price: float


class SuggestProduct(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    total_stock: int


class SuggestCategory(BaseModel):
    name: str
    count: int
    min_price: float


class Suggestions(BaseModel):
    """GET /api/suggest: type-ahead results for the search box."""
    query: str
    categories: list[SuggestCategory]
    terms: list[str] = Field(description="Keyword ideas, or popular searches when the box is empty.")
    products: list[SuggestProduct]
    total_matches: int


# ---------------------------------------------------------------- accounts


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class User(BaseModel):
    id: int
    first_name: str | None
    last_name: str | None
    name: str
    email: str
    created_at: str


# ---------------------------------------------------------------- chat API


class HistoryMessage(BaseModel):
    """A past turn sent by the browser (only used for shoppers who are not logged in)."""
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


PageType = Literal["home", "products", "product", "about", "login", "create-account", "other"]


class PageContext(BaseModel):
    """What the shopper can see when they send a message, so 'this shirt' or 'these' make sense."""
    path: str | None = Field(default=None, max_length=200, description="URL path, e.g. /products/basic-hoodie-big-yale")
    page: PageType = "other"
    product_id: str | None = Field(default=None, max_length=120, description="Item open on a single item page.")
    category: str | None = Field(default=None, max_length=60, description="Category filter on the Products page.")
    visible_product_ids: list[str] = Field(
        default_factory=list, max_length=30,
        description="Product cards on screen (chat results strip first), in order.",
    )


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    page: PageContext | None = None
    current_product_id: str | None = Field(
        default=None, max_length=120, description="Shortcut for page.product_id (older clients)."
    )
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)


class ProductCard(BaseModel):
    """A product card shown under a chat reply and in the "From your chat" strip on the page."""
    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    description: str
    colors: list[str]
    sizes_in_stock: list[str]
    total_stock: int

    @classmethod
    def from_product(cls, p: dict) -> "ProductCard":
        return cls(
            product_id=p["product_id"], name=p["name"], category=p["category"], price=p["price"],
            image_url=p["image_url"], description=p["description"], colors=p["colors"],
            sizes_in_stock=[i["size"] for i in p["inventory"] if i["quantity"] > 0],
            total_stock=p["total_stock"],
        )


class SearchInfo(BaseModel):
    """The latest catalogue search, so the page can label the cards ("Hoodies: 27 matches")."""
    query: str | None = None
    category: str | None = None
    total_matches: int = 0
    product_ids: list[str] = Field(default_factory=list, description="All matches in ranked order (up to 30).")


class ChatResponse(BaseModel):
    """What POST /api/chat sends back to the website."""
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    display: Literal["none", "selected", "search_results"] = Field(
        default="none",
        description="search_results = page shows every match from the search; selected = a few picked items.",
    )
    search: SearchInfo | None = None
    saved: bool = Field(default=False, description="True when the turn was saved to the shopper's history.")


class ChatHistoryItem(BaseModel):
    """One saved message from chat_messages, for GET /api/chat/history."""
    id: int
    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    created_at: str


# ---------------------------------------------------------------- agent: dependencies


@dataclass
class ShopDeps:
    """Passed to every tool call. Holds only safe shopper info (never the password hash).

    user_id comes from the login cookie on the server, never from the model or the browser,
    so memory tools can only ever read the logged-in shopper's own history.
    """
    user_id: int | None = None
    run_id: str = ""                                          # links tool events in the audit trail
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = None
    page: PageContext | None = None
    current_product_id: str | None = None
    seen_product_ids: set[str] = field(default_factory=set)  # every product a tool returned this run
    last_search: "SearchInfo | None" = None                   # latest search_products call (all matches)


# ---------------------------------------------------------------- agent: tool results


class ProductSummary(BaseModel):
    """Compact product info returned by search tools (keeps tokens low)."""
    product_id: str
    name: str
    category: str
    price: float
    colors: list[str] = Field(description="Colors in the design, not separate color options.")
    sizes_in_stock: list[str]
    total_stock: int
    short_description: str


class SizeStock(BaseModel):
    size: str
    quantity: int
    status: Literal["in stock", "low stock", "sold out"]


class StockCheck(BaseModel):
    """Answer to "how many are in stock?" / "do you have it in M?", straight from the inventory table."""
    product_id: str
    name: str
    price: float
    size_requested: str | None
    available: bool = Field(description="True if the requested size (or any size) has quantity > 0.")
    quantity: int = Field(description="Units of the requested size, or total units across all sizes.")
    stock_by_size: list[SizeStock]
    sizes_in_stock: list[str]
    sold_out_sizes: list[str]
    message: str = Field(description="Plain-English stock statement to base the reply on.")


class ProductDetails(BaseModel):
    product_id: str
    name: str
    category: str
    garment_type: str
    price: float
    description: str
    colors: list[str] = Field(description="Colors in the design, not separate color options.")
    tags: list[str]
    stock_by_size: list[SizeStock]
    total_stock: int
    stock_message: str = Field(description="Plain-English stock statement, e.g. 'SOLD OUT in every size'.")


class SearchResult(BaseModel):
    total_matches: int
    products: list[ProductSummary]
    note: str | None = None


class CategoryPrice(BaseModel):
    category: str
    product_count: int
    min_price: float
    max_price: float
    average_price: float
    cheapest: ProductSummary
    most_expensive: ProductSummary


class PriceSummary(BaseModel):
    scope: str
    product_count: int
    min_price: float
    max_price: float
    average_price: float
    price_points: dict[str, int] = Field(description="price -> number of products at that price")
    by_category: list[CategoryPrice]


class ShopperProfile(BaseModel):
    """Who is chatting. Only the logged-in shopper's own details."""
    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    member_since: str | None = None
    saved_messages: int = 0
    recent_products: list[str] = Field(default_factory=list, description="Names of products shown in recent chats.")


class PastMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: str
    products_shown: list[str] = Field(default_factory=list, description="'name (product_id)' for each card shown")
    viewing: str | None = Field(default=None, description="Product the shopper was viewing when they sent it.")


class ChatRecall(BaseModel):
    logged_in: bool
    total_found: int
    messages: list[PastMessage]
    note: str | None = None


# ---------------------------------------------------------------- agent: structured output


class ShopReply(BaseModel):
    """What the agent must return on every turn."""
    reply: str = Field(description="Friendly answer to the shopper, 1-5 short sentences or a short list.")
    show_search_results: bool = Field(
        default=False,
        description=(
            "True when the shopper is browsing a type of product (e.g. 'what hoodies do you have?', "
            "'show me bulldog stuff'). The website then shows EVERY match from your latest search_products "
            "call as product cards, so you don't need to list them all in product_ids."
        ),
    )
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=8,
        description="IDs of products to show on the page, most relevant first. Only IDs returned by tools.",
    )
