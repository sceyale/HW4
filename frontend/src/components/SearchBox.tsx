import { useEffect, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { fetchSuggestions, formatPrice } from "../api.ts";
import { useChat } from "../ChatContext.tsx";
import type { Suggestions } from "../types.ts";

type Option =
  | { kind: "search"; label: string; q: string }
  | { kind: "category"; label: string; name: string; meta: string }
  | { kind: "term"; label: string; q: string }
  | { kind: "product"; label: string; id: string; image: string; meta: string; soldOut: boolean }
  | { kind: "ask"; label: string; q: string };

function toOptions(text: string, s: Suggestions | null): Option[] {
  const q = text.trim();
  const opts: Option[] = [];
  if (q.length >= 2) opts.push({ kind: "search", label: `Search for “${q}”`, q });
  for (const c of s?.categories ?? [])
    opts.push({ kind: "category", label: c.name, name: c.name, meta: `${c.count} styles · from ${formatPrice(c.min_price)}` });
  for (const t of s?.terms ?? []) opts.push({ kind: "term", label: t, q: t });
  for (const p of s?.products ?? [])
    opts.push({ kind: "product", label: p.name, id: p.product_id, image: p.image_url,
      meta: `${p.category} · ${formatPrice(p.price)}`, soldOut: p.total_stock === 0 });
  if (q.length >= 2) opts.push({ kind: "ask", label: `Ask our assistant about “${q}”`, q });
  return opts;
}

export default function SearchBox({ variant = "nav" }: { variant?: "nav" | "hero" }) {
  const navigate = useNavigate();
  const { ask } = useChat();
  const [text, setText] = useState("");
  const [data, setData] = useState<Suggestions | null>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const boxRef = useRef<HTMLDivElement>(null);

  const typing = text.trim().length > 0;

  // Debounced type-ahead (150 ms) only while the shopper is typing; older requests are cancelled.
  useEffect(() => {
    if (!open || !typing) { setData(null); return; }
    const ctrl = new AbortController();
    const t = setTimeout(() => {
      fetchSuggestions(text.trim(), ctrl.signal).then(setData).catch(() => undefined);
    }, 150);
    return () => { clearTimeout(t); ctrl.abort(); };
  }, [text, open, typing]);

  useEffect(() => {
    const close = (e: MouseEvent) => { if (!boxRef.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const options = toOptions(text, data);

  function choose(o: Option) {
    setOpen(false);
    setActive(-1);
    if (o.kind === "product") return navigate(`/products/${o.id}`);
    if (o.kind === "category") return navigate(`/products?category=${encodeURIComponent(o.name)}`);
    if (o.kind === "ask") { setText(""); return ask(o.q); }
    setText(o.q);
    navigate(`/products?q=${encodeURIComponent(o.q)}`);
  }

  function onKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "ArrowDown" && typing) { e.preventDefault(); setOpen(true); setActive((a) => Math.min(a + 1, options.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((a) => Math.max(a - 1, -1)); }
    else if (e.key === "Escape") { setOpen(false); setActive(-1); }
    else if (e.key === "Enter") {
      e.preventDefault();
      if (active >= 0 && options[active]) choose(options[active]);
      else if (text.trim()) choose({ kind: "search", label: "", q: text.trim() });
    }
  }

  return (
    <div className={`search search--${variant}`} ref={boxRef}>
      <svg className="search__icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2.2" />
        <path d="M20 20l-3.5-3.5" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" />
      </svg>
      <input
        className="search__input"
        type="search"
        value={text}
        placeholder={variant === "hero" ? "Search hoodies, bulldogs, The Game…" : "Search hoodies, crewnecks, bulldogs…"}
        aria-label="Search products"
        aria-autocomplete="list"
        aria-expanded={open}
        onFocus={() => setOpen(true)}   // panel still waits for typing
        onChange={(e) => { setText(e.target.value); setOpen(true); setActive(-1); }}
        onKeyDown={onKey}
      />
      {open && typing && options.length > 0 && (
        <div className="search__panel" role="listbox">
          {options.map((o, i) => (
            <button
              key={`${o.kind}-${o.label}-${i}`}
              role="option"
              aria-selected={i === active}
              className={`search__opt search__opt--${o.kind} ${i === active ? "is-active" : ""}`}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => { e.preventDefault(); choose(o); }}
            >
              {o.kind === "product" && <img src={o.image} alt="" />}
              <span className="search__opt-text">
                <span className="search__opt-label">{o.label}</span>
                {(o.kind === "category" || o.kind === "product") && <span className="search__opt-meta">{o.meta}</span>}
              </span>
              {o.kind === "category" && <span className="search__tag">Category</span>}
              {o.kind === "product" && o.soldOut && <span className="search__tag search__tag--out">Sold out</span>}
              {o.kind === "ask" && <span className="search__tag search__tag--ai">Ask</span>}
            </button>
          ))}
          {data && data.total_matches === 0 && text.trim().length >= 2 && (
            <p className="search__empty">No products match. Try another word, or ask our assistant.</p>
          )}
        </div>
      )}
    </div>
  );
}
