import sqlite3
import hashlib
import os
import secrets
from datetime import datetime, date, timedelta
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "resumatch.db")


def get_db_connection():
    """Create a SQLite database connection with dictionary row access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables for users, sessions, and scan history."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            subscription_plan TEXT DEFAULT 'free',
            subscription_expires_at TEXT,
            scans_today INTEGER DEFAULT 0,
            last_scan_date TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # User Sessions Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # Scan History Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            job_title TEXT NOT NULL,
            match_percentage REAL NOT NULL,
            scanned_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Hash password using SHA-256 with salt."""
    if not salt:
        salt = secrets.token_hex(16)
    salted = (password + salt).encode('utf-8')
    pwd_hash = hashlib.sha256(salted).hexdigest()
    return pwd_hash, salt


class UserManager:
    """Manages User Registration, Authentication, Sessions, and Subscriptions."""

    @classmethod
    def register_user(cls, name: str, email: str, password: str) -> Dict[str, Any]:
        """Register a new user account."""
        email_clean = email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("An account with this email address already exists.")

        pwd_hash, salt = hash_password(password)
        now_str = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, salt, subscription_plan, scans_today, last_scan_date, created_at)
            VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
        """, (name.strip(), email_clean, pwd_hash, salt, date.today().isoformat(), now_str))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Create session token
        token, user_data = cls.create_session(user_id)
        return {"token": token, "user": user_data}

    @classmethod
    def login_user(cls, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials and generate session token."""
        email_clean = email.strip().lower()
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email_clean,))
        user_row = cursor.fetchone()
        if not user_row:
            conn.close()
            raise ValueError("Invalid email address or password.")

        pwd_hash, _ = hash_password(password, user_row["salt"])
        if pwd_hash != user_row["password_hash"]:
            conn.close()
            raise ValueError("Invalid email address or password.")

        conn.close()
        token, user_data = cls.create_session(user_row["id"])
        return {"token": token, "user": user_data}

    @classmethod
    def create_session(cls, user_id: int) -> tuple[str, Dict[str, Any]]:
        """Generate session token valid for 30 days."""
        conn = get_db_connection()
        cursor = conn.cursor()

        token = secrets.token_hex(32)
        now = datetime.now()
        expires = now + timedelta(days=30)

        cursor.execute("""
            INSERT INTO sessions (token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
        """, (token, user_id, now.isoformat(), expires.isoformat()))

        conn.commit()
        conn.close()

        user_data = cls.get_user_by_id(user_id)
        return token, user_data

    @classmethod
    def get_user_by_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Validate session token and return user dictionary."""
        if not token:
            return None
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT s.expires_at, u.* FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # Check expiration
        if datetime.fromisoformat(row["expires_at"]) < datetime.now():
            return None

        return cls.format_user_dict(dict(row))

    @classmethod
    def get_user_by_id(cls, user_id: int) -> Dict[str, Any]:
        """Fetch user by ID."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return cls.format_user_dict(dict(row)) if row else {}

    @classmethod
    def format_user_dict(cls, row: Dict[str, Any]) -> Dict[str, Any]:
        """Format user DB row into public response dictionary."""
        today_str = date.today().isoformat()
        scans_today = row.get("scans_today", 0)
        
        # Reset daily scan counter if day changed
        if row.get("last_scan_date") != today_str:
            scans_today = 0

        plan = row.get("subscription_plan", "free")
        is_pro = (plan == "pro")

        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "subscription_plan": plan,
            "is_pro": is_pro,
            "scans_today": scans_today,
            "daily_scan_limit": 999999 if is_pro else 3,
            "scans_remaining": 999999 if is_pro else max(0, 3 - scans_today),
            "created_at": row.get("created_at")
        }

    @classmethod
    def check_and_increment_scan(cls, user_id: Optional[int]) -> bool:
        """Check daily scan limits for user and increment scan count if allowed."""
        if not user_id:
            # Anonymous guests get 3 scans per session
            return True

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT subscription_plan, scans_today, last_scan_date FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return True

        today_str = date.today().isoformat()
        plan = row["subscription_plan"]
        scans_today = row["scans_today"]
        last_date = row["last_scan_date"]

        if last_date != today_str:
            scans_today = 0

        if plan != "pro" and scans_today >= 3:
            conn.close()
            return False  # Free limit reached!

        cursor.execute("""
            UPDATE users SET scans_today = ?, last_scan_date = ? WHERE id = ?
        """, (scans_today + 1, today_str, user_id))

        conn.commit()
        conn.close()
        return True

    @classmethod
    def upgrade_subscription(cls, user_id: int, plan: str = "pro") -> Dict[str, Any]:
        """Upgrade user subscription to Pro Plan (₹150/month)."""
        conn = get_db_connection()
        cursor = conn.cursor()

        expires_at = (datetime.now() + timedelta(days=30)).isoformat()
        cursor.execute("""
            UPDATE users SET subscription_plan = ?, subscription_expires_at = ? WHERE id = ?
        """, (plan, expires_at, user_id))

        conn.commit()
        conn.close()
        return cls.get_user_by_id(user_id)

    @classmethod
    def log_scan_history(cls, user_id: int, filename: str, job_title: str, match_percentage: float):
        """Record scan history entry."""
        if not user_id:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO scan_history (user_id, filename, job_title, match_percentage, scanned_at)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, filename, job_title, match_percentage, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @classmethod
    def get_user_scan_history(cls, user_id: int) -> List[Dict[str, Any]]:
        """Get scan history records for user profile."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT filename, job_title, match_percentage, scanned_at 
            FROM scan_history WHERE user_id = ? ORDER BY id DESC LIMIT 20
        """, (user_id,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

# Initialize DB tables on module load
init_db()
