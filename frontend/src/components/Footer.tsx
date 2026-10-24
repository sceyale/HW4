import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer__inner">
        <div>
          <p className="footer__brand">Campus Customs</p>
          <p className="footer__muted">Family-run Yale apparel · New Haven, Connecticut · Since 1975</p>
        </div>
        <nav className="footer__links" aria-label="Footer">
          <Link to="/products">Products</Link>
          <Link to="/about">About Us</Link>
          <Link to="/login">Log In</Link>
          <Link to="/create-account">Create Account</Link>
        </nav>
      </div>
      <p className="footer__fine container">
        © {new Date().getFullYear()} Campus Customs. Independent retailer of Yale apparel.
      </p>
    </footer>
  );
}
