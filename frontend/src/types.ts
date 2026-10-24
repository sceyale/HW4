// Mirrors the Product model returned by the FastAPI backend (backend/main.py).
export type InventoryItem = { size: string; quantity: number };

export type Product = {
  product_id: string;
  name: string;
  garment_type: string;
  category: string;
  description: string;
  colors: string[];
  search_tags: string[];
  image_file_path: string;
  image_url: string;
  price: number;
  inventory: InventoryItem[];
  total_stock: number;
};

// Mirrors models.ProductCard: a product shown with a chat reply.
export type ProductCardData = {
  product_id: string;
  name: string;
  category: string;
  price: number;
  image_url: string;
  description: string;
  colors: string[];
  sizes_in_stock: string[];
  total_stock: number;
};

export type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  products?: ProductCardData[];
  display?: ChatResponse["display"];
  error?: boolean;
};

// Mirrors models.ChatRequest / ChatResponse / ChatHistoryItem.
// Mirrors models.PageContext: what the shopper can see when they send a message.
export type PageType = "home" | "products" | "product" | "about" | "login" | "create-account" | "other";
export type PageContext = {
  path: string;
  page: PageType;
  product_id: string | null;
  category: string | null;
  visible_product_ids: string[];
};

export type ChatRequest = {
  message: string;
  page?: PageContext;
  current_product_id?: string | null;
  history?: { role: "user" | "assistant"; content: string }[];
};

export type SearchInfo = {
  query: string | null;
  category: string | null;
  total_matches: number;
  product_ids: string[];
};

export type ChatResponse = {
  reply: string;
  products: ProductCardData[];
  display: "none" | "selected" | "search_results";   // search_results -> page shows every match
  search: SearchInfo | null;
  saved: boolean;
};

// The cards the page currently shows from the chat.
export type ChatMatches = {
  products: ProductCardData[];
  label: string;          // e.g. "Hoodies" or "\"bulldog\""
  total: number;          // total matches in the catalogue (may exceed cards shown)
  isSearch: boolean;
  version: number;        // bumps on every update so the page can scroll to it
};

export type ChatHistoryItem = {
  id: number;
  role: "user" | "assistant";
  content: string;
  products: ProductCardData[];
  created_at: string;
};

export type User = {
  id: number;
  first_name: string | null;
  last_name: string | null;
  name: string;
  email: string;
  created_at: string;
};

export type SignupData = {
  first_name: string;
  last_name: string;
  email: string;
  password: string;
  confirm_password: string;
};

// Mirrors models.Suggestions (GET /api/suggest).
export type Suggestions = {
  query: string;
  categories: { name: string; count: number; min_price: number }[];
  terms: string[];
  products: { product_id: string; name: string; category: string; price: number; image_url: string; total_stock: number }[];
  total_matches: number;
};
