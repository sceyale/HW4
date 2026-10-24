import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchProduct, formatPrice } from "../api.ts";
import type { InventoryItem, Product } from "../types.ts";

const LOW_STOCK = 5;

function stockLabel(item: InventoryItem) {
  if (item.quantity === 0) return { text: "Sold out", cls: "size--out" };
  if (item.quantity <= LOW_STOCK) return { text: `Only ${item.quantity} left`, cls: "size--low" };
  return { text: "In stock", cls: "size--in" };
}

export default function ProductDetail() {
  const { productId = "" } = useParams();
  const [product, setProduct] = useState<Product | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setProduct(null);
    setError(null);
    fetchProduct(productId)
      .then(setProduct)
      .catch((e: Error) =>
        setError(e.message === "not-found" ? "We couldn't find that product." : "We couldn't load this product. Is the backend running?"),
      );
  }, [productId]);

  if (error) {
    return (
      <section className="section container">
        <p className="notice notice--error">{error}</p>
        <Link to="/products" className="link-arrow">← Back to all products</Link>
      </section>
    );
  }
  if (!product) return <section className="section container"><p className="status">Loading…</p></section>;

  const available = product.inventory.filter((i) => i.quantity > 0).map((i) => i.size);

  return (
    <section className="section">
      <div className="container">
        <Link to="/products" className="link-arrow">← Back to all products</Link>

        <div className="detail">
          <div className="detail__img">
            <img src={product.image_url} alt={product.name} />
          </div>

          <div className="detail__info">
            <p className="eyebrow eyebrow--blue">{product.category}</p>
            <h1 className="detail__name">{product.name}</h1>
            <p className="detail__price">{formatPrice(product.price)}</p>

            <h2 className="detail__h">Description</h2>
            <p>{product.description}</p>

            <dl className="detail__facts">
              <div><dt>Style</dt><dd>{product.garment_type}</dd></div>
              <div><dt>Colors in design</dt><dd>{product.colors.join(", ")}</dd></div>
              <div>
                <dt>Availability</dt>
                <dd>{product.total_stock > 0 ? `${product.total_stock} in stock · sizes ${available.join(", ")}` : "Currently sold out"}</dd>
              </div>
            </dl>

            <h2 className="detail__h">Sizes &amp; Stock</h2>
            <ul className="sizes">
              {product.inventory.map((item) => {
                const s = stockLabel(item);
                return (
                  <li key={item.size} className={`size ${s.cls}`}>
                    <span className="size__name">{item.size}</span>
                    <span className="size__stock">{s.text}</span>
                  </li>
                );
              })}
            </ul>

            {product.search_tags.length > 0 && (
              <div className="tags">
                {product.search_tags.map((t) => <span key={t} className="tag">{t}</span>)}
              </div>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}
