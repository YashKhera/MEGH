"""MEGH auth — real server-side accounts (SQLite + PBKDF2 + bearer tokens).

No third-party deps: hashlib / secrets / sqlite3 from the standard library.
Passwords are never stored — only salt + PBKDF2-HMAC-SHA256 hash.
Clients send `Authorization: Bearer <token>`; /auth/me verifies role server-side.

DB lives at data/metadata/megh_users.db (gitignored).
"""
from __future__ import annotations
import hashlib
import secrets
import sqlite3
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "metadata" / "megh_users.db"
TOKEN_TTL = 30 * 24 * 3600  # 30 days
ROLES = ("viewer", "analyst", "researcher")

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

def _db() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    con.execute("""CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
        salt TEXT NOT NULL, pw_hash TEXT NOT NULL,
        role TEXT NOT NULL, created REAL NOT NULL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS tokens(
        token TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
        expires REAL NOT NULL)""")
    return con

def _hash(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()

class SignupIn(BaseModel):
    name: str
    password: str
    role: str = "viewer"

class LoginIn(BaseModel):
    name: str
    password: str

def _public_user(row) -> dict:
    return {"id": row[0], "name": row[1], "role": row[2]}

@router.post("/signup")
def signup(inp: SignupIn):
    name = inp.name.strip()
    if not (2 <= len(name) <= 40):
        raise HTTPException(400, "name must be 2-40 characters")
    if len(inp.password) < 6:
        raise HTTPException(400, "password must be at least 6 characters")
    if inp.role not in ROLES:
        raise HTTPException(400, f"role must be one of {ROLES}")
    salt = secrets.token_hex(16)
    con = _db()
    try:
        cur = con.execute("INSERT INTO users(name, salt, pw_hash, role, created) VALUES(?,?,?,?,?)",
                          (name, salt, _hash(inp.password, salt), inp.role, time.time()))
        con.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "that name is already taken")
    token = secrets.token_urlsafe(32)
    con.execute("INSERT INTO tokens(token, user_id, expires) VALUES(?,?,?)",
                (token, cur.lastrowid, time.time() + TOKEN_TTL))
    con.commit()
    row = con.execute("SELECT id, name, role FROM users WHERE id=?", (cur.lastrowid,)).fetchone()
    con.close()
    return {"token": token, "user": _public_user(row)}

@router.post("/login")
def login(inp: LoginIn):
    con = _db()
    row = con.execute("SELECT id, name, role, salt, pw_hash FROM users WHERE name=?",
                      (inp.name.strip(),)).fetchone()
    if not row or _hash(inp.password, row[3]) != row[4]:
        con.close()
        raise HTTPException(401, "wrong name or password")
    token = secrets.token_urlsafe(32)
    con.execute("INSERT INTO tokens(token, user_id, expires) VALUES(?,?,?)",
                (token, row[0], time.time() + TOKEN_TTL))
    con.commit()
    con.close()
    return {"token": token, "user": {"id": row[0], "name": row[1], "role": row[2]}}

def current_user(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if not creds:
        raise HTTPException(401, "login required")
    con = _db()
    t = con.execute("SELECT user_id, expires FROM tokens WHERE token=?", (creds.credentials,)).fetchone()
    if not t or t[1] < time.time():
        con.close()
        raise HTTPException(401, "session expired — please log in again")
    row = con.execute("SELECT id, name, role FROM users WHERE id=?", (t[0],)).fetchone()
    con.close()
    if not row:
        raise HTTPException(401, "account not found")
    return _public_user(row)

@router.get("/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}

@router.post("/logout")
def logout(creds: HTTPAuthorizationCredentials | None = Depends(_bearer)):
    if creds:
        con = _db()
        con.execute("DELETE FROM tokens WHERE token=?", (creds.credentials,))
        con.commit()
        con.close()
    return {"ok": True}
