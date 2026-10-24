import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section className="auth">
      <div className="auth__card">
        <h1 className="auth__title">Page Not Found</h1>
        <p className="auth__sub">That page wandered off campus.</p>
        <Link to="/" className="btn btn--blue">Back to Home</Link>
      </div>
    </section>
  );
}
