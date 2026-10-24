import { Link } from "react-router-dom";
import type { Product, ProductCardData } from "../types.ts";

type CardProduct = Pick<Product & ProductCardData, "product_id" | "name" | "category" | "description" | "price" | "image_url" | "total_stock">;
import { formatPrice } from "../api.ts";

// The whole card (image included) is one link to the single item page.
export default function ProductCard({ product }: { product: CardProduct }) {
  const soldOut = product.total_stock === 0;
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card__img">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {soldOut && <span className="badge badge--soldout">Sold out</span>}
      </div>
      <div className="product-card__body">
        <p className="product-card__cat">{product.category}</p>
        <h3 className="product-card__name">{product.name}</h3>
        <p className="product-card__desc">{product.description}</p>
        <p className="product-card__price">{formatPrice(product.price)}</p>
      </div>
    </Link>
  );
}
