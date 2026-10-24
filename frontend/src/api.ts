import type { ChatHistoryItem, ChatRequest, ChatResponse, Product, SignupData, Suggestions, User } from "./types.ts";

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(res.status === 404 ? "not-found" : `Request failed (${res.status})`);
  return res.json() as Promise<T>;
}

export const fetchProducts = (q?: string) =>
  getJson<Product[]>(q ? `/api/products?q=${encodeURIComponent(q)}` : "/api/products");

export async function fetchSuggestions(q: string, signal?: AbortSignal): Promise<Suggestions> {
  const res = await fetch(`/api/suggest?q=${encodeURIComponent(q)}`, { signal });
  if (!res.ok) throw new Error("suggest failed");
  return res.json() as Promise<Suggestions>;
}

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`);

export const formatPrice = (n: number) =>
  n.toLocaleString("en-US", { style: "currency", currency: "USD" });

// ---------- auth (session lives in an HttpOnly cookie set by the backend) ----------

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : "Something went wrong. Please try again.");
  }
  return (res.status === 204 ? undefined : await res.json()) as T;
}

export const registerUser = (data: SignupData) => postJson<User>("/api/auth/register", data);
export const loginUser = (email: string, password: string) =>
  postJson<User>("/api/auth/login", { email, password });
export const logoutUser = () => postJson<void>("/api/auth/logout");
export async function fetchMe(): Promise<User | null> {
  const res = await fetch("/api/auth/me", { credentials: "same-origin" });
  return res.ok ? ((await res.json()) as User) : null;
}

// ---------- chat (PydanticAI agent behind FastAPI) ----------
export const sendChat = (req: ChatRequest) => postJson<ChatResponse>("/api/chat", req);

export async function fetchChatHistory(): Promise<ChatHistoryItem[]> {
  const res = await fetch("/api/chat/history", { credentials: "same-origin" });
  return res.ok ? ((await res.json()) as ChatHistoryItem[]) : [];
}

export async function clearChatHistory(): Promise<void> {
  await fetch("/api/chat/history", { method: "DELETE", credentials: "same-origin" });
}
