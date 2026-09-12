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

    # Password Reset OTPs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS password_otps (
            gmail TEXT PRIMARY KEY,
            otp_code TEXT NOT NULL,
            expires_at TEXT NOT NULL
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
        """Register a new user account with required Gmail address."""
        email_clean = email.strip().lower()
        if not email_clean.endswith("@gmail.com"):
            raise ValueError("Registration requires a valid Gmail address ending with @gmail.com")

        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email = ?", (email_clean,))
        if cursor.fetchone():
            conn.close()
            raise ValueError("An account with this Gmail address already exists.")

        pwd_hash, salt = hash_password(password)
        now_str = datetime.now().isoformat()

        cursor.execute("""
            INSERT INTO users (name, email, password_hash, salt, subscription_plan, scans_today, last_scan_date, created_at)
            VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
        """, (name.strip(), email_clean, pwd_hash, salt, date.today().isoformat(), now_str))

        user_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Trigger Welcome Email via SMTP in background thread
        import threading
        try:
            from backend.email_service import send_welcome_email
            threading.Thread(target=send_welcome_email, args=(email_clean, name.strip()), daemon=True).start()
        except Exception:
            pass

        # Create session token
        token, user_data = cls.create_session(user_id)
        return {"token": token, "user": user_data}

    @classmethod
    def find_username_by_gmail(cls, gmail: str) -> Dict[str, Any]:
        """Retrieve candidate username by verifying registered Gmail address."""
        gmail_clean = gmail.strip().lower()
        if not gmail_clean.endswith("@gmail.com"):
            raise ValueError("Please enter a valid Gmail address ending with @gmail.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email FROM users WHERE email = ?", (gmail_clean,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            cand_name = gmail_clean.split("@")[0].replace(".", " ").replace("_", " ").title()
            return {"id": 0, "name": cand_name, "email": gmail_clean}

        return {"id": row["id"], "name": row["name"], "email": row["email"]}

    @classmethod
    def reset_password_by_gmail(cls, gmail: str, new_password: str) -> Dict[str, Any]:
        """Reset user password via Gmail verification."""
        gmail_clean = gmail.strip().lower()
        if not gmail_clean.endswith("@gmail.com"):
            raise ValueError("Please enter a valid Gmail address ending with @gmail.com")

        if not new_password or len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long.")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (gmail_clean,))
        row = cursor.fetchone()

        pwd_hash, salt = hash_password(new_password)

        if not row:
            cand_name = gmail_clean.split("@")[0].replace(".", " ").replace("_", " ").title()
            now_str = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, salt, subscription_plan, scans_today, last_scan_date, created_at)
                VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
            """, (cand_name, gmail_clean, pwd_hash, salt, date.today().isoformat(), now_str))
        else:
            cand_name = row["name"]
            cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, row["id"]))

        conn.commit()
        conn.close()

        # Trigger Welcome & Confirmation Emails in background threads
        import threading
        try:
            from backend.email_service import send_welcome_email, send_password_reset_confirmation_email
            threading.Thread(target=send_welcome_email, args=(gmail_clean, cand_name), daemon=True).start()
            threading.Thread(target=send_password_reset_confirmation_email, args=(gmail_clean, cand_name), daemon=True).start()
        except Exception:
            pass

        return {
            "success": True, 
            "message": f"🎉 Password reset successful for '{cand_name}'! Confirmation sent to your Gmail. You can now log in.", 
            "name": cand_name
        }

    @classmethod
    def request_password_otp(cls, gmail: str) -> Dict[str, Any]:
        """Generate and store a random 6-digit OTP code for password reset."""
        import random
        gmail_clean = gmail.strip().lower()
        if not gmail_clean.endswith("@gmail.com"):
            raise ValueError("Please enter a valid Gmail address ending with @gmail.com")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM users WHERE email = ?", (gmail_clean,))
        row = cursor.fetchone()

        if not row:
            cand_name = gmail_clean.split("@")[0].replace(".", " ").replace("_", " ").title()
            pwd_hash, salt = hash_password("TempPassword123!")
            now_str = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, salt, subscription_plan, scans_today, last_scan_date, created_at)
                VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
            """, (cand_name, gmail_clean, pwd_hash, salt, date.today().isoformat(), now_str))
            conn.commit()
        else:
            cand_name = row["name"]

        otp_code = str(random.randint(100000, 999999))
        expires_at = (datetime.now() + timedelta(minutes=10)).isoformat()

        cursor.execute("""
            INSERT INTO password_otps (gmail, otp_code, expires_at)
            VALUES (?, ?, ?)
            ON CONFLICT(gmail) DO UPDATE SET otp_code=excluded.otp_code, expires_at=excluded.expires_at
        """, (gmail_clean, otp_code, expires_at))

        conn.commit()
        conn.close()

        # Dispatch real email via SMTP to customer email
        try:
            from backend.email_service import send_otp_email
            email_sent = send_otp_email(gmail_clean, otp_code, cand_name)
        except Exception as err:
            logger.error(f"Failed to send OTP to {gmail_clean}: {err}")
            email_sent = False

        status_msg = f"🔑 6-Digit OTP Verification Code sent to '{gmail_clean}' from mohammedarhan9829@gmail.com! Please check your Gmail Inbox."

        return {
            "success": True,
            "message": status_msg,
            "gmail": gmail_clean,
            "name": cand_name,
            "email_sent": email_sent
        }

    @classmethod
    def verify_otp_and_reset_password(cls, gmail: str, otp_code: str, new_password: str) -> Dict[str, Any]:
        """Verify 6-digit OTP code and reset user password."""
        gmail_clean = gmail.strip().lower()
        otp_clean = otp_code.strip()

        if not gmail_clean.endswith("@gmail.com"):
            raise ValueError("Please enter a valid Gmail address ending with @gmail.com")

        if not otp_clean or len(otp_clean) != 6:
            raise ValueError("Please enter a valid 6-digit OTP verification code.")

        if not new_password or len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters long.")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT otp_code, expires_at FROM password_otps WHERE gmail = ?", (gmail_clean,))
        otp_row = cursor.fetchone()

        if not otp_row or otp_row["otp_code"] != otp_clean:
            conn.close()
            raise ValueError("Incorrect 6-Digit OTP code. Please check and try again.")

        if datetime.fromisoformat(otp_row["expires_at"]) < datetime.now():
            conn.close()
            raise ValueError("OTP verification code has expired (valid for 10 min). Please request a new OTP.")

        cursor.execute("SELECT id, name FROM users WHERE email = ?", (gmail_clean,))
        user_row = cursor.fetchone()

        pwd_hash, salt = hash_password(new_password)

        if not user_row:
            cand_name = gmail_clean.split("@")[0].replace(".", " ").replace("_", " ").title()
            now_str = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, salt, subscription_plan, scans_today, last_scan_date, created_at)
                VALUES (?, ?, ?, ?, 'free', 0, ?, ?)
            """, (cand_name, gmail_clean, pwd_hash, salt, date.today().isoformat(), now_str))
        else:
            cand_name = user_row["name"]
            cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (pwd_hash, salt, user_row["id"]))

        cursor.execute("DELETE FROM password_otps WHERE gmail = ?", (gmail_clean,))
        conn.commit()
        conn.close()

        # Trigger Confirmation Email in background thread
        import threading
        try:
            from backend.email_service import send_password_reset_confirmation_email
            threading.Thread(target=send_password_reset_confirmation_email, args=(gmail_clean, cand_name), daemon=True).start()
        except Exception:
            pass

        return {
            "success": True,
            "message": f"🎉 Password successfully reset for '{cand_name}'! Confirmation email sent to {gmail_clean}.",
            "name": cand_name
        }

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
            raise ValueError("Invalid Gmail address or password.")

        pwd_hash, _ = hash_password(password, user_row["salt"])
        if pwd_hash != user_row["password_hash"]:
            conn.close()
            raise ValueError("Invalid Gmail address or password.")

        conn.close()
        token, user_data = cls.create_session(user_row["id"])

        # Trigger Login Notification Email in background thread to candidate & mohammedarhan9829@gmail.com
        import threading
        try:
            from backend.email_service import send_login_notification_email
            threading.Thread(target=send_login_notification_email, args=(user_row["email"], user_row["name"]), daemon=True).start()
        except Exception:
            pass

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

        plan = "unlimited"
        is_pro = True

        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "subscription_plan": plan,
            "is_pro": True,
            "scans_today": scans_today,
            "daily_scan_limit": 999999,
            "scans_remaining": 999999,
            "created_at": row.get("created_at")
        }

    @classmethod
    def check_and_increment_scan(cls, user_id: Optional[int]) -> bool:
        """All scans are 100% free and unlimited for all users."""
        if not user_id:
            return True

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT scans_today, last_scan_date FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return True

        today_str = date.today().isoformat()
        scans_today = row["scans_today"]
        last_date = row["last_scan_date"]

        if last_date != today_str:
            scans_today = 0

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
