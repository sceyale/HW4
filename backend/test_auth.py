"""Check that signup and login use matching hash settings.

Offline (default): runs auth.py against a temporary COPY of the database.
    python test_auth.py

Live: talks to the running app at http://localhost:8000 (creates a real account).
    python test_auth.py --live
"""

from __future__ import annotations

import hashlib
import hmac
import http.cookiejar
import json
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

TEST_EMAIL, TEST_PASSWORD = "test@campuscustoms.yale.edu", "password"
NEW_PASSWORD = "BoolaBoola1975"
results: list[tuple[bool, str]] = []


def check(ok: bool, label: str) -> None:
    results.append((ok, label))
    print(("PASS " if ok else "FAIL ") + label)


def independent_verify(password: str, stored: str) -> bool:
    """Re-implement the spec from scratch, so the test doesn't just trust auth.py."""
    algo, salt, digest = stored.split("$")
    mine = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return algo == "pbkdf2_sha256" and hmac.compare_digest(mine, digest)


def offline() -> None:
    import sqlite3
    import auth
    import db

    tmp = Path(tempfile.mkdtemp()) / "campus_customs.db"
    shutil.copy(db.DB_PATH, tmp)
    auth.DB_PATH = tmp                      # point auth at the copy
    auth.init_auth_tables()
    conn = sqlite3.connect(tmp)
    seeded_hash = conn.execute("SELECT password_hash FROM users WHERE email=?", (TEST_EMAIL,)).fetchone()[0]

    print("\n-- Seeded test user --")
    check(independent_verify(TEST_PASSWORD, seeded_hash), "seed hash matches the spec (PBKDF2-SHA256, 120k, salt from string)")
    check(auth.login(TEST_EMAIL, TEST_PASSWORD)["email"] == TEST_EMAIL, "login with correct password")
    try:
        auth.login(TEST_EMAIL, "wrong-password"); check(False, "wrong password rejected")
    except auth.AuthError as e:
        check(e.status == 401, "wrong password rejected (401)")
    after = conn.execute("SELECT password_hash FROM users WHERE email=?", (TEST_EMAIL,)).fetchone()[0]
    check(after == seeded_hash, "login did not change the stored hash (no new salt at login)")

    print("\n-- Brand-new account --")
    email = f"new.bulldog.{int(time.time())}@yale.edu"
    auth.register("New", "Bulldog", email, NEW_PASSWORD, NEW_PASSWORD)
    stored = conn.execute("SELECT password_hash FROM users WHERE email=?", (email,)).fetchone()[0]
    check(NEW_PASSWORD not in stored, "plain password is not stored")
    check(len(stored.split("$")) == 3 and stored.startswith("pbkdf2_sha256$"), f"stored in seed format: {stored[:40]}...")
    check(independent_verify(NEW_PASSWORD, stored), "new hash matches the spec, so signup and login settings are the same")
    check(auth.login(email, NEW_PASSWORD)["email"] == email, "login with the new account")
    try:
        auth.login(email, NEW_PASSWORD + "x"); check(False, "wrong password rejected")
    except auth.AuthError as e:
        check(e.status == 401, "wrong password rejected (401)")
    other = auth.hash_password(NEW_PASSWORD)
    check(other.split("$")[1] != stored.split("$")[1], "same password at signup gets a different random salt")


def live(base: str = "http://localhost:8000") -> None:
    def client():
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(opener, method, path, body=None):
        req = urllib.request.Request(base + path, method=method,
                                     data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Content-Type": "application/json"})
        try:
            with opener.open(req) as r:
                raw = r.read()
                return r.status, json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"null")

    print("\n-- Seeded test user (live) --")
    c = client()
    s, u = call(c, "POST", "/api/auth/login", {"email": TEST_EMAIL, "password": TEST_PASSWORD})
    check(s == 200, f"login -> {s}")
    s, me = call(c, "GET", "/api/auth/me")
    check(s == 200 and me["email"] == TEST_EMAIL, f"/me shows {me and me.get('email')}")
    check("password_hash" not in (u or {}), "response never includes password_hash")
    s, _ = call(client(), "POST", "/api/auth/login", {"email": TEST_EMAIL, "password": "wrong-password"})
    check(s == 401, f"wrong password -> {s}")

    print("\n-- Brand-new account (live) --")
    email = f"new.bulldog.{int(time.time())}@yale.edu"
    c = client()
    s, _ = call(c, "POST", "/api/auth/register", {"first_name": "New", "last_name": "Bulldog", "email": email,
                                                  "password": NEW_PASSWORD, "confirm_password": NEW_PASSWORD})
    check(s == 201, f"create account {email} -> {s}")
    s, _ = call(c, "POST", "/api/auth/logout")
    check(s == 204, f"log out -> {s}")
    c = client()
    s, _ = call(c, "POST", "/api/auth/login", {"email": email, "password": NEW_PASSWORD})
    check(s == 200, f"log back in with the new account -> {s}")
    s, me = call(c, "GET", "/api/auth/me")
    check(s == 200 and me["first_name"] == "New", "/me shows the new account")


if __name__ == "__main__":
    live() if "--live" in sys.argv else offline()
    passed = sum(ok for ok, _ in results)
    print(f"\n{passed}/{len(results)} checks passed")
    sys.exit(0 if passed == len(results) else 1)
