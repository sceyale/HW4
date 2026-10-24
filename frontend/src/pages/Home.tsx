import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Crest from "../components/Crest.tsx";
import PhotoSlot from "../components/PhotoSlot.tsx";
import ProductCard from "../components/ProductCard.tsx";
import { fetchProducts, formatPrice } from "../api.ts";
import { CAMPUS_SCENES, HERO_SLIDES, STUDENT_REEL } from "../campusPhotos.ts";
import { useChat } from "../ChatContext.tsx";
import type { Product } from "../types.ts";

type Cat = { name: string; count: number; min_price: number };
const SLIDE_MS = 6500;

const MOMENTS = [
  { year: "1701", text: "Yale is founded as the Collegiate School." },
  { year: "1875", text: "Yale and Harvard play the first edition of The Game." },
  { year: "1889", text: "Handsome Dan becomes the first live college mascot in America." },
  { year: "1975", text: "Campus Customs opens its doors in New Haven." },
];

function HeroSlideshow() {
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % HERO_SLIDES.length), SLIDE_MS);
    return () => clearInterval(t);
  }, []);
  const s = HERO_SLIDES[i];
  return (
    <>
      <div className="hero2__slides" aria-hidden="true">
        {HERO_SLIDES.map((p, n) => (
          <div key={p.file} className={`hero2__slide ${n === i ? "is-active" : ""}`}>
            <PhotoSlot photo={p} eager={n === 0} showCaption={false} />
          </div>
        ))}
      </div>
      <div className="hero2__caption">
        <span className="hero2__place">{s.place}</span>
        <span>{s.caption}</span>
        <span className="hero2__dots">
          {HERO_SLIDES.map((p, n) => (
            <button key={p.file} aria-label={`Show ${p.place}`} className={n === i ? "is-active" : ""} onClick={() => setI(n)} />
          ))}
        </span>
      </div>
    </>
  );
}

export default function Home() {
  const [cats, setCats] = useState<Cat[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const { ask } = useChat();

  useEffect(() => {
    fetch("/api/categories").then((r) => (r.ok ? r.json() : [])).then(setCats).catch(() => setCats([]));
    fetchProducts().then(setProducts).catch(() => setProducts([]));
  }, []);

  // Customer favorites: the best-stocked item in each category (real catalogue data).
  const favorites = useMemo(() => {
    const best = new Map<string, Product>();
    for (const p of products) {
      const cur = best.get(p.category);
      if (!cur || p.total_stock > cur.total_stock) best.set(p.category, p);
    }
    return Array.from(best.values()).slice(0, 4);
  }, [products]);

  return (
    <>
      {/* ---------- Hero: cross-fading campus scenes ---------- */}
      <section className="hero2">
        <HeroSlideshow />
        <div className="hero2__veil" aria-hidden="true" />
        <div className="container hero2__inner">
          <Crest size={64} className="hero2__crest" />
          <p className="hero2__eyebrow">Est. 1975 <span>✦</span> New Haven, Connecticut</p>
          <h1 className="hero2__title">
            Wear the Blue.<br />
            <em>Carry the Tradition.</em>
          </h1>
          <p className="hero2__lede">
            Three centuries of Yale heritage, outfitted by one New Haven family for fifty years.
            Hoodies, crewnecks, tees and fleeces in the classic Yale blue.
          </p>
          <div className="hero2__actions">
            <Link to="/products" className="btn btn--gold">Shop the collection</Link>
            <button className="btn btn--ghost" onClick={() => ask("What are your most popular items?")}>
              Ask our shop assistant
            </button>
          </div>
        </div>
        <a href="#discover" className="hero2__scroll" aria-label="Scroll to explore">
          <span>Explore</span>
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6" fill="none" stroke="currentColor" strokeWidth="1.6" /></svg>
        </a>
      </section>

      {/* ---------- Ribbon ---------- */}
      <div className="ribbon" id="discover">
        <div className="container ribbon__inner">
          <span>Family-run since 1975</span><i>✦</i>
          <span>100+ Yale styles</span><i>✦</i>
          <span>Sizes XS – XXL</span><i>✦</i>
          <span>Lux et Veritas</span>
        </div>
      </div>

      {/* ---------- Categories ---------- */}
      <section className="section">
        <div className="container">
          <header className="heading">
            <p className="heading__eyebrow">The Collection</p>
            <h2 className="heading__title">Shop by category</h2>
            <span className="heading__rule" aria-hidden="true" />
          </header>
          <div className="tiles">
            {cats.map((c, n) => (
              <Link key={c.name} to={`/products?category=${encodeURIComponent(c.name)}`} className={`tile tile--${n % 3}`}>
                <span className="tile__count">{c.count} styles</span>
                <span className="tile__name">{c.name}</span>
                <span className="tile__price">from {formatPrice(c.min_price)}</span>
                <span className="tile__arrow" aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Beauty of campus ---------- */}
      <section className="section section--ivory">
        <div className="container">
          <header className="heading">
            <p className="heading__eyebrow">New Haven</p>
            <h2 className="heading__title">The beauty of campus</h2>
            <span className="heading__rule" aria-hidden="true" />
            <p className="heading__lede">Gothic towers, ivy courtyards and elm-lined lawns: the places our customers call home.</p>
          </header>
          <div className="mosaic">
            {CAMPUS_SCENES.map((p, n) => (
              <PhotoSlot key={p.file} photo={p} className={`mosaic__item mosaic__item--${n}`} />
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Moving reel: student life ---------- */}
      <section className="section reel-section">
        <div className="container">
          <header className="heading heading--light">
            <p className="heading__eyebrow">Life in Blue</p>
            <h2 className="heading__title">Bright college years</h2>
            <span className="heading__rule" aria-hidden="true" />
          </header>
        </div>
        <div className="reel" aria-label="Student life photo reel">
          <div className="reel__track">
            {[...STUDENT_REEL, ...STUDENT_REEL].map((p, n) => (
              <PhotoSlot key={`${p.file}-${n}`} photo={p} className="reel__item" />
            ))}
          </div>
        </div>
      </section>

      {/* ---------- Favorites ---------- */}
      {favorites.length > 0 && (
        <section className="section">
          <div className="container">
            <header className="heading">
              <p className="heading__eyebrow">Customer favorites</p>
              <h2 className="heading__title">Best of the season</h2>
              <span className="heading__rule" aria-hidden="true" />
            </header>
            <div className="product-grid">
              {favorites.map((p) => <ProductCard key={p.product_id} product={p} />)}
            </div>
            <p className="center"><Link to="/products" className="btn btn--navy">View all products</Link></p>
          </div>
        </section>
      )}

      {/* ---------- Heritage ---------- */}
      <section className="section section--ivory">
        <div className="container">
          <header className="heading">
            <p className="heading__eyebrow">Three centuries of tradition</p>
            <h2 className="heading__title">Built on Bulldog history</h2>
            <span className="heading__rule" aria-hidden="true" />
          </header>
          <ol className="moments">
            {MOMENTS.map((m) => (
              <li key={m.year} className="moment">
                <span className="moment__year">{m.year}</span>
                <span>{m.text}</span>
              </li>
            ))}
          </ol>
          <p className="center"><Link to="/about" className="link-arrow">Read our story →</Link></p>
        </div>
      </section>

      <section className="cta">
        <div className="container cta__inner">
          <Crest size={56} />
          <h2 className="cta__title">Boola Boola.</h2>
          <p>Gear for game day, reunion weekend, or a crisp New Haven morning.</p>
          <Link to="/create-account" className="btn btn--gold">Join the Campus Customs family</Link>
        </div>
      </section>
    </>
  );
}
