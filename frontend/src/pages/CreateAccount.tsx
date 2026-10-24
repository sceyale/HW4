import { useState, type ChangeEvent, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.tsx";
import type { SignupData } from "../types.ts";

// Fields match the users table: first_name, last_name, email, password (stored only as a hash).
const EMPTY: SignupData = { first_name: "", last_name: "", email: "", password: "", confirm_password: "" };
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

function validate(f: SignupData): string | null {
  if (!f.first_name.trim() || !f.last_name.trim()) return "Please enter your first and last name.";
  if (!EMAIL_RE.test(f.email.trim())) return "Please enter a valid email address.";
  if (f.password.length < 8) return "Password must be at least 8 characters.";
  if (f.password.length > 128) return "Password must be 128 characters or fewer.";
  if (f.password !== f.confirm_password) return "Passwords do not match.";
  return null;
}

export default function CreateAccount() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<SignupData>(EMPTY);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/products" replace />;

  const update = (field: keyof SignupData) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }));

  const mismatch = form.confirm_password.length > 0 && form.password !== form.confirm_password;

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const problem = validate(form);
    if (problem) return setError(problem);
    setError(null);
    setSubmitting(true);
    try {
      await register(form);           // backend hashes the password and logs the user in
      navigate("/products", { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="auth">
      <div className="auth__card">
        <h1 className="auth__title">Join the Campus Customs Family</h1>
        <p className="auth__sub">Create an account to chat about products and save your conversations.</p>
        <form onSubmit={handleSubmit} className="form" noValidate>
          <div className="form__row">
            <label className="form__field">
              <span>First name</span>
              <input required autoComplete="given-name" value={form.first_name} onChange={update("first_name")} />
            </label>
            <label className="form__field">
              <span>Last name</span>
              <input required autoComplete="family-name" value={form.last_name} onChange={update("last_name")} />
            </label>
          </div>
          <label className="form__field">
            <span>Email</span>
            <input type="email" required autoComplete="email" value={form.email} onChange={update("email")} />
          </label>
          <label className="form__field">
            <span>Password</span>
            <input type="password" required minLength={8} autoComplete="new-password"
              value={form.password} onChange={update("password")} />
            <small className="form__hint">At least 8 characters.</small>
          </label>
          <label className="form__field">
            <span>Confirm password</span>
            <input type="password" required autoComplete="new-password" aria-invalid={mismatch}
              value={form.confirm_password} onChange={update("confirm_password")} />
            {mismatch && <small className="form__hint form__hint--error">Passwords do not match.</small>}
          </label>
          {error && <p className="form__error" role="alert">{error}</p>}
          <button type="submit" className="btn btn--blue btn--full" disabled={submitting}>
            {submitting ? "Creating account…" : "Create Account"}
          </button>
        </form>
        <p className="auth__switch">
          Already have an account? <Link to="/login">Log in</Link>
        </p>
      </div>
    </section>
  );
}
