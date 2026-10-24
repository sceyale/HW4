import { Fragment, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation, useMatch } from "react-router-dom";
import { useAuth } from "../AuthContext.tsx";
import { useChat } from "../ChatContext.tsx";
import { formatPrice } from "../api.ts";
import type { PageContext, PageType, ProductCardData } from "../types.ts";

function pageType(path: string): PageType {
  if (path === "/") return "home";
  if (path === "/products") return "products";
  if (path.startsWith("/products/")) return "product";
  if (path === "/about") return "about";
  if (path === "/login") return "login";
  if (path === "/create-account") return "create-account";
  return "other";
}

const MINI_CARDS = 4;
const SUGGESTIONS = ["What hoodies do you have?", "Anything with a bulldog?", "What's your cheapest fleece?"];

// Tiny formatter for agent replies: **bold** and "- " bullet lines.
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith("**") && part.endsWith("**") ? <strong key={i}>{part.slice(2, -2)}</strong> : <Fragment key={i}>{part}</Fragment>,
  );
}

function Formatted({ text }: { text: string }) {
  const lines = text.split("\n");
  const out: ReactNode[] = [];
  let bullets: string[] = [];
  const flush = () => {
    if (bullets.length) out.push(<ul key={`u${out.length}`}>{bullets.map((b, i) => <li key={i}>{inline(b)}</li>)}</ul>);
    bullets = [];
  };
  lines.forEach((line) => {
    const m = line.match(/^\s*[-*•]\s+(.*)$/);
    if (m) return void bullets.push(m[1]);
    flush();
    if (line.trim()) out.push(<p key={`p${out.length}`}>{inline(line)}</p>);
  });
  flush();
  return <>{out}</>;
}

function MiniCard({ p }: { p: ProductCardData }) {
  return (
    <Link to={`/products/${p.product_id}`} className="mini-card">
      <img src={p.image_url} alt={p.name} loading="lazy" />
      <span className="mini-card__name">{p.name}</span>
      <span className="mini-card__price">{formatPrice(p.price)}</span>
      {p.total_stock === 0 && <span className="mini-card__out">Sold out</span>}
    </Link>
  );
}

export default function ChatWidget() {
  const { messages, sending, send, clear, matches, pageInfo, open, setOpen, pendingQuestion, takePending } = useChat();
  const { user } = useAuth();
  const { pathname } = useLocation();
  const productMatch = useMatch("/products/:productId");

  // Page context sent with every message so "this shirt" / "these" make sense to the agent.
  function currentPage(): PageContext {
    const page = pageType(pathname);
    const onProducts = page === "products";
    const visible = onProducts
      ? [...(matches?.products.map((p) => p.product_id) ?? []), ...pageInfo.visible_product_ids]
      : [];
    return {
      path: pathname,
      page,
      product_id: productMatch?.params.productId ?? null,
      category: onProducts ? pageInfo.category : null,
      visible_product_ids: Array.from(new Set(visible)).slice(0, 30),
    };
  }
  const [input, setInput] = useState("");
  const nudge = useChatNudge(pathname, open, messages.length > 1, pageInfo.category);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open, sending]);

  // "Ask our assistant about …" from the search box: send it once the panel is open.
  useEffect(() => {
    if (open && pendingQuestion && !sending) {
      const q = takePending();
      if (q) void send(q, currentPage());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, pendingQuestion]);

  async function submit(text: string) {
    const t = text.trim();
    if (!t || sending) return;
    setInput("");
    await send(t, currentPage());
  }

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    void submit(input);
  }

  return (
    <div className="chat">
      {open && (
        <div className="chat__panel" role="dialog" aria-label="Shop assistant chat">
          <div className="chat__header">
            <div>
              <p className="chat__title">Shop Assistant</p>
              <p className="chat__subtitle">
                {user ? `Chatting as ${user.name} · history saved` : "Guest · log in to save your chat"}
              </p>
            </div>
            <div className="chat__header-actions">
              {messages.length > 1 && (
                <button className="chat__clear" onClick={() => void clear()} title="Clear conversation">Clear</button>
              )}
              <button className="chat__close" aria-label="Close chat" onClick={() => setOpen(false)}>×</button>
            </div>
          </div>

          <div className="chat__messages" aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`chat__turn chat__turn--${m.role}`}>
                <div className={`chat__msg chat__msg--${m.role} ${m.error ? "chat__msg--error" : ""}`}>
                  {m.role === "assistant" ? <Formatted text={m.content} /> : m.content}
                </div>
                {m.products && m.products.length > 0 && (
                  <>
                    <div className="chat__cards">
                      {m.products.slice(0, MINI_CARDS).map((p) => <MiniCard key={p.product_id} p={p} />)}
                    </div>
                    {m.display === "search_results" && (
                      <Link to="/products#chat-matches" className="chat__see-all"
                        onClick={() => setTimeout(() => document.getElementById("chat-matches")?.scrollIntoView({ behavior: "smooth" }), 50)}>
                        See all {m.products.length} on the Products page →
                      </Link>
                    )}
                  </>
                )}
              </div>
            ))}
            {messages.length === 1 && !sending && (
              <div className="chat__suggestions">
                {SUGGESTIONS.map((s) => (
                  <button key={s} className="chip" onClick={() => void submit(s)}>{s}</button>
                ))}
              </div>
            )}
            {sending && <div className="chat__msg chat__msg--assistant chat__typing">Looking that up…</div>}
            <div ref={endRef} />
          </div>

          <form className="chat__form" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about a hoodie, size or price…"
              aria-label="Message"
              maxLength={1000}
            />
            <button type="submit" disabled={!input.trim() || sending}>Send</button>
          </form>
        </div>
      )}

      {!open && nudge.show && (
        <div className="nudge" role="status">
          <button className="nudge__close" aria-label="Dismiss" onClick={nudge.dismiss}>×</button>
          <p className="nudge__title">{nudge.title}</p>
          <p className="nudge__text">Ask me about sizes, stock or prices. I'll put matching items right on the page.</p>
          <div className="nudge__chips">
            {nudge.prompts.map((q) => (
              <button key={q} className="nudge__chip" onClick={() => { nudge.dismiss(); setOpen(true); void submit(q); }}>{q}</button>
            ))}
          </div>
        </div>
      )}

      <button
        className={`chat__launcher ${!open && nudge.show ? "is-nudging" : ""}`}
        aria-label={open ? "Close chat" : "Open chat"}
        aria-expanded={open}
        onClick={() => { nudge.dismiss(); setOpen(!open); }}
      >
        {open ? (
          <span aria-hidden="true">×</span>
        ) : (
          <svg viewBox="0 0 24 24" aria-hidden="true" className="chat__icon">
            <path d="M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-4.2 3.6c-.5.4-1.3.1-1.3-.6V16A2.5 2.5 0 0 1 4 13.5v-8Z" fill="currentColor" />
          </svg>
        )}
        {!open && <span className="chat__launcher-label">Ask us</span>}
      </button>
    </div>
  );
}


// ---------------------------------------------------------------- pop-up nudge
// If a shopper stays on a browsing page for NUDGE_DELAY without opening a product or the chat,
// the chat button pops up a friendly offer to help. Shown at most once per visit.

const NUDGE_DELAY = 8000;
const NUDGE_PAGES = new Set(["/", "/products", "/about"]);
const NUDGE_KEY = "cc_chat_nudged";

function alreadyNudged(): boolean {
  try { return sessionStorage.getItem(NUDGE_KEY) === "1"; } catch { return false; }
}
function rememberNudged(): void {
  try { sessionStorage.setItem(NUDGE_KEY, "1"); } catch { /* storage blocked: nudge may show again */ }
}

function useChatNudge(pathname: string, chatOpen: boolean, hasChatted: boolean, category: string | null) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    setShow(false);
    if (chatOpen || hasChatted || alreadyNudged() || !NUDGE_PAGES.has(pathname)) return;
    const timer = setTimeout(() => { setShow(true); rememberNudged(); }, NUDGE_DELAY);
    // Opening a product card cancels the nudge (they found something).
    const onClick = (e: MouseEvent) => {
      if ((e.target as HTMLElement).closest(".product-card, .mini-card, .search")) clearTimeout(timer);
    };
    document.addEventListener("click", onClick);
    return () => { clearTimeout(timer); document.removeEventListener("click", onClick); };
  }, [pathname, chatOpen, hasChatted]);

  const cat = category ?? (pathname === "/products" ? "the catalogue" : null);
  const title = cat ? `Need help with ${cat.toLowerCase() === "the catalogue" ? "the catalogue" : cat}?` : "Looking for something Yale?";
  const prompts = category
    ? [`What ${category.toLowerCase()} are in stock in M?`, `Cheapest ${category.toLowerCase()}?`]
    : ["What hoodies do you have?", "Anything with a bulldog?"];

  return { show, title, prompts, dismiss: () => setShow(false) };
}
