import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import ProductCard from "../components/ProductCard.tsx";
import { fetchProducts } from "../api.ts";
import { useChat } from "../ChatContext.tsx";
import type { Product } from "../types.ts";

const ALL = "All";

export default function Products() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useSearchParams();
  const q = params.get("q")?.trim() ?? "";
  const category = params.get("category") ?? ALL;
  const setCategory = (c: string) => {
    const next = new URLSearchParams(params);
    if (c === ALL) next.delete("category"); else next.set("category", c);
    setParams(next);
  };
  const clearSearch = () => {
    const next = new URLSearchParams(params);
    next.delete("q");
    setParams(next);
  };
  const { matches, clearMatches, setPageInfo } = useChat();
  const matchesRef = useRef<HTMLDivElement>(null);

  // Scroll to the chat results whenever a new answer updates them.
  useEffect(() => {
    if (matches) matchesRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [matches?.version]);

  // ?q= runs the ranked search (same ranking the assistant uses); otherwise the full catalogue.
  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchProducts(q || undefined)
      .then(setProducts)
      .catch(() => setError("We couldn't load the catalogue. Make sure the backend is running on port 8000."))
      .finally(() => setLoading(false));
  }, [q]);

  const categories = useMemo(
    () => [ALL, ...Array.from(new Set(products.map((p) => p.category))).sort()],
    [products],
  );
  const shown = category === ALL ? products : products.filter((p) => p.category === category);

  // Tell the chat what is on screen (filter + first cards), and clear it when leaving the page.
  useEffect(() => {
    setPageInfo({
      category: category === ALL ? null : category,
      visible_product_ids: shown.slice(0, 12).map((p) => p.product_id),
    });
  }, [category, products, setPageInfo]);
  useEffect(() => () => setPageInfo({ category: null, visible_product_ids: [] }), [setPageInfo]);

  return (
    <>
      <section className="page-header">
        <div className="container">
          <p className="eyebrow">Shop</p>
          <h1 className="page-header__title">Products</h1>
          <p className="page-header__lede">More than 100 Yale styles, sized XS through XXL.</p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          {matches && matches.products.length > 0 && (
            <div className="chat-matches" ref={matchesRef} id="chat-matches">
              <div className="chat-matches__head">
                <div>
                  <p className="eyebrow eyebrow--blue">From your chat</p>
                  <h2 className="chat-matches__title">
                    {matches.label}
                    <span className="chat-matches__count">
                      {matches.isSearch
                        ? ` · ${matches.total} ${matches.total === 1 ? "match" : "matches"}` +
                          (matches.total > matches.products.length ? ` (showing ${matches.products.length})` : "")
                        : ` · ${matches.products.length} ${matches.products.length === 1 ? "item" : "items"}`}
                    </span>
                  </h2>
                </div>
                <button className="chip" onClick={clearMatches}>Clear</button>
              </div>
              <div className="product-grid">
                {matches.products.map((p) => <ProductCard key={p.product_id} product={p} />)}
              </div>
            </div>
          )}

          {loading && <p className="status">Loading the catalogue…</p>}
          {error && <p className="notice notice--error">{error}</p>}

          {!loading && !error && (
            <>
              <div className="filters" role="tablist" aria-label="Filter by category">
                {categories.map((c) => (
                  <button
                    key={c}
                    role="tab"
                    aria-selected={c === category}
                    className={`chip ${c === category ? "is-active" : ""}`}
                    onClick={() => setCategory(c)}
                  >
                    {c}
                  </button>
                ))}
              </div>
              <div className="results-bar">
                <p className="status">
                  {q ? <>{shown.length} results for <strong>“{q}”</strong></> : <>{shown.length} products</>}
                  {category !== ALL && <> in <strong>{category}</strong></>}
                </p>
                {q && <button className="chip" onClick={clearSearch}>Clear search ×</button>}
              </div>
              {shown.length === 0 && (
                <div className="empty">
                  <p className="empty__title">No products match{q ? ` “${q}”` : ""}.</p>
                  <p>Try a broader word like “hoodie” or “bulldog”, or ask our shop assistant for ideas.</p>
                </div>
              )}
              <div className="product-grid">
                {shown.map((p) => (
                  <ProductCard key={p.product_id} product={p} />
                ))}
              </div>
            </>
          )}
        </div>
      </section>
    </>
  );
}
