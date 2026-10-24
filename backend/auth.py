"""Accounts, password hashing and login sessions (standard library only).

Password storage (same format as the seed database)
---------------------------------------------------
    pbkdf2_sha256$<salt>$<hash>
    PBKDF2-HMAC-SHA256, 120,000 iterations, salt used as UTF-8 text, hash as hex

Rules followed at login:
  1. Never "unhash" the stored value. Hashing is one-way; we only re-hash and compare.
  2. Read the salt out of the stored string. A new salt is made only at signup.
  3. Hash the typed password with that same salt, then compare with
     hmac.compare_digest (constant time).
  4. Signup and login share ONE function, _hash(), and one set of settings
     (ALGORITHM, ITERATIONS, salt encoding), so the right password always matches.

Sessions
--------
On login we create a random token, put it in an HttpOnly cookie (JavaScript can't
read it), and store only the SHA-256 of the token in the sessions table.
"""

from __future__ import annotations

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from db import DB_PATH

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 120_000   # matches the seed database spec (pbkdf2_sha256$salt$hash)
SESSION_DAYS = 7
SESSION_COOKIE = "cc_session"

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD, MAX_PASSWORD = 8, 128

# Simple brute-force protection: 5 failed logins per email per 15 minutes.
MAX_FAILURES, FAILURE_WINDOW = 5, 15 * 60
_failures: dict[str, list[float]] = {}


class AuthError(Exception):
    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.message, self.status = message, status


# ---------- password hashing ----------
# The ONLY place the hash settings live. Signup and login both go through _hash().

def _hash(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), ITERATIONS).hex()


def hash_password(password: str) -> str:
    """Signup: create a NEW random salt, hash, and build the stored string."""
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${salt}${_hash(password, salt)}"


def verify_password(password: str, stored: str) -> bool:
    """Login: reuse the salt from the stored string; never create a new one."""
    parts = stored.split("$")
    if len(parts) != 3 or parts[0] != ALGORITHM:
        return False
    _, salt, stored_hash = parts                          # rule 2: read the salt back out
    typed_hash = _hash(password, salt)                    # rule 3: same salt, same settings
    return hmac.compare_digest(typed_hash, stored_hash)   # rule 3: constant-time compare


# A real hash to check against when the email doesn't exist, so a wrong email
# takes as long as a wrong password (doesn't reveal which emails have accounts).
_DUMMY_HASH = hash_password(secrets.token_hex(16))


# ---------- database ----------

def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_auth_tables() -> None:
    with _connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                   token_hash TEXT PRIMARY KEY,
                   user_id INTEGER NOT NULL,
                   created_at TEXT NOT NULL DEFAULT (datetime('now')),
                   expires_at TEXT NOT NULL,
                   FOREIGN KEY (user_id) REFERENCES users(id)
               )"""
        )


def _public_user(row: sqlite3.Row) -> dict[str, Any]:
    # Never return password_hash to the client.
    return {
        "id": row["id"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
    }


# ---------- register / login / sessions ----------

def validate_signup(first: str, last: str, email: str, password: str, confirm: str) -> tuple[str, str, str]:
    first, last, email = first.strip(), last.strip(), email.strip().lower()
    if not first or not last:
        raise AuthError("First and last name are required.")
    if len(first) > 60 or len(last) > 60:
        raise AuthError("Names must be 60 characters or fewer.")
    if not EMAIL_RE.match(email) or len(email) > 254:
        raise AuthError("Please enter a valid email address.")
    if not (MIN_PASSWORD <= len(password) <= MAX_PASSWORD):
        raise AuthError(f"Password must be {MIN_PASSWORD}-{MAX_PASSWORD} characters.")
    if password != confirm:
        raise AuthError("Passwords do not match.")
    return first, last, email


def register(first: str, last: str, email: str, password: str, confirm: str) -> dict[str, Any]:
    first, last, email = validate_signup(first, last, email, password, confirm)
    with _connect() as conn:
        try:
            cur = conn.execute(
                "INSERT INTO users (name, email, password_hash, first_name, last_name) VALUES (?, ?, ?, ?, ?)",
                (f"{first} {last}", email, hash_password(password), first, last),
            )
        except sqlite3.IntegrityError:
            raise AuthError("An account with this email already exists.", 409)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        return _public_user(row)


def _too_many_failures(email: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(email, []) if now - t < FAILURE_WINDOW]
    _failures[email] = recent
    return len(recent) >= MAX_FAILURES


def login(email: str, password: str) -> dict[str, Any]:
    email = email.strip().lower()
    if _too_many_failures(email):
        raise AuthError("Too many failed attempts. Please wait 15 minutes and try again.", 429)
    with _connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH)
        if not row or not ok:
            _failures.setdefault(email, []).append(time.time())
            raise AuthError("Invalid email or password.", 401)  # same message either way
        _failures.pop(email, None)
        return _public_user(row)


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
    return token


def user_for_session(token: str | None) -> dict[str, Any] | None:
    if not token:
        return None
    with _connect() as conn:
        row = conn.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
            (_token_hash(token),),
        ).fetchone()
        return _public_user(row) if row else None


def delete_session(token: str | None) -> None:
    if token:
        with _connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
