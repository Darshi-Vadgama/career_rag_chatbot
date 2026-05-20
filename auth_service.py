# app/services/auth_service.py

import redis
import bcrypt
import jwt
import uuid
import psycopg2
import psycopg2.extras

from datetime import datetime, timedelta
from fastapi import HTTPException


# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY     = "your-super-secret-key-change-this"
ALGORITHM      = "HS256"
ACCESS_EXPIRE  = 30
REFRESH_EXPIRE = 7 * 24 * 60

r = redis.Redis(host="redis", port=6379, db=1, decode_responses=True)

DB_CONFIG = {
    "host":     "postgres",
    "port":     5432,
    "dbname":   "career_db",
    "user":     "career_user",
    "password": "career_pass",
}


# ── DB connection ─────────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(**DB_CONFIG)


# ── Create tables on startup ──────────────────────────────────────────────────

def init_db():
    conn = get_db()
    cur  = conn.cursor()

    # users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            username   VARCHAR(100) UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # chats table — one row per chat session
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id    UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title      TEXT NOT NULL DEFAULT 'New Chat',
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # messages table — one row per message
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            chat_id    UUID NOT NULL REFERENCES chats(id) ON DELETE CASCADE,
            role       VARCHAR(20) NOT NULL,
            content    TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    payload = {
        "sub":  user_id,
        "type": "access",
        "exp":  datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE),
        "iat":  datetime.utcnow(),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    token = str(uuid.uuid4())
    r.setex(f"refresh:{user_id}:{token}", timedelta(minutes=REFRESH_EXPIRE), "valid")
    return token


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid access token")


# ── Auth ──────────────────────────────────────────────────────────────────────

def register_user(username: str, password: str) -> dict:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id, username",
            (username, hash_password(password))
        )
        user = cur.fetchone()
        conn.commit()

        user_id       = str(user["id"])
        access_token  = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "username":      username,
            "user_id":       user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()


def login_user(username: str, password: str) -> dict:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute("SELECT id, username, password FROM users WHERE username = %s", (username,))
        user = cur.fetchone()

        if not user or not verify_password(password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid username or password")

        user_id       = str(user["id"])
        access_token  = create_access_token(user_id)
        refresh_token = create_refresh_token(user_id)

        return {
            "access_token":  access_token,
            "refresh_token": refresh_token,
            "token_type":    "bearer",
            "username":      username,
            "user_id":       user_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cur.close()
        conn.close()


def refresh_tokens(user_id: str, refresh_token: str) -> dict:
    key = f"refresh:{user_id}:{refresh_token}"
    if not r.exists(key):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    r.delete(key)

    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT username FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    username      = row["username"] if row else user_id
    access_token  = create_access_token(user_id)
    new_refresh   = create_refresh_token(user_id)

    return {
        "access_token":  access_token,
        "refresh_token": new_refresh,
        "token_type":    "bearer",
        "username":      username,
        "user_id":       user_id,
    }


def logout_user(user_id: str, refresh_token: str):
    r.delete(f"refresh:{user_id}:{refresh_token}")


# ── Chat session helpers ──────────────────────────────────────────────────────

def create_chat(user_id: str, title: str = "New Chat") -> dict:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "INSERT INTO chats (user_id, title) VALUES (%s, %s) RETURNING id, title, created_at",
            (user_id, title)
        )
        chat = cur.fetchone()
        conn.commit()
        return {
            "id":         str(chat["id"]),
            "title":      chat["title"],
            "created_at": str(chat["created_at"]),
        }
    finally:
        cur.close()
        conn.close()


def get_user_chats(user_id: str) -> list:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT id, title, created_at FROM chats WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        chats = cur.fetchall()
        return [
            {
                "id":         str(c["id"]),
                "title":      c["title"],
                "created_at": str(c["created_at"]),
            }
            for c in chats
        ]
    finally:
        cur.close()
        conn.close()


def get_chat_messages(chat_id: str) -> list:
    conn = get_db()
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        cur.execute(
            "SELECT role, content, created_at FROM messages WHERE chat_id = %s ORDER BY created_at ASC",
            (chat_id,)
        )
        msgs = cur.fetchall()
        return [{"role": m["role"], "content": m["content"]} for m in msgs]
    finally:
        cur.close()
        conn.close()


def save_message(chat_id: str, role: str, content: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO messages (chat_id, role, content) VALUES (%s, %s, %s)",
            (chat_id, role, content)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def update_chat_title(chat_id: str, title: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute(
            "UPDATE chats SET title = %s WHERE id = %s",
            (title[:60], chat_id)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()


def delete_chat(chat_id: str):
    conn = get_db()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM chats WHERE id = %s", (chat_id,))
        conn.commit()
    finally:
        cur.close()
        conn.close()