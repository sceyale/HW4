import { useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext.tsx";
import SearchBox from "./SearchBox.tsx";
import Crest from "./Crest.tsx";

type NavItem = { to: string; label: string; variant?: "button" };

const MAIN_ITEMS: NavItem[] = [
  { to: "/", label: "Home" },
  { to: "/products", label: "Products" },
  { to: "/about", label: "About Us" },
];

const GUEST_ITEMS: NavItem[] = [
  { to: "/login", label: "Log In" },
  { to: "/create-account", label: "Create Account", variant: "button" },
];

export default function NavBar() {
  const [open, setOpen] = useState(false);
  const { user, loading, logout } = useAuth();
  const navigate = useNavigate();
  const items = loading || user ? MAIN_ITEMS : [...MAIN_ITEMS, ...GUEST_ITEMS];

  async function handleLogout() {
    setOpen(false);
    await logout();
    navigate("/");
  }

  return (
    <header className="nav">
      <div className="nav__inner container">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <Crest size={34} className="brand__crest" />
          <span className="brand__text">
            <span className="brand__name">Campus Customs</span>
            <span className="brand__est">New Haven · Est. 1975</span>
          </span>
        </Link>

        <div className="nav__search"><SearchBox /></div>

        <button
          className="nav__toggle"
          aria-label="Toggle navigation"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          <span />
          <span />
          <span />
        </button>

        <nav className={`nav__links ${open ? "is-open" : ""}`} aria-label="Main">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                [
                  "nav__link",
                  item.variant === "button" ? "nav__link--button" : "",
                  isActive ? "is-active" : "",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
          {user && (
            <>
              <span className="nav__greeting">Hi, {user.first_name ?? user.name}</span>
              <button className="nav__link nav__link--button" onClick={handleLogout}>Log Out</button>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
