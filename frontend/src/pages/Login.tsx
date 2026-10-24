import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.tsx";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/products";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={from} replace />;

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError((err as Error).message);
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth">
      <div className="auth__card">
        <h1 className="auth__title">Welcome Back, Bulldog</h1>
        <p className="auth__sub">Log in to chat with our shop assistant and see your history.</p>
        <form onSubmit={handleSubmit} className="form" noValidate>
          <label className="form__field">
            <span>Email</span>
            <input type="email" required autoComplete="email" value={email}
              onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="form__field">
            <span>Password</span>
            <input type="password" required autoComplete="current-password" value={password}
              onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p className="form__error" role="alert">{error}</p>}
          <button type="submit" className="btn btn--blue btn--full" disabled={submitting || !email || !password}>
            {submitting ? "Logging in…" : "Log In"}
          </button>
        </form>
        <p className="auth__switch">
          New to Campus Customs? <Link to="/create-account">Create an account</Link>
        </p>
      </div>
    </section>
  );
}
