
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self):
        self.database = 'sanpai.db'
        self.connection = None
        self.connect()
        self.init_db()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.database, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print("✅ Connected to SQLite database")
        except sqlite3.Error as e:
            print(f"❌ Error connecting to SQLite: {e}")

    def init_db(self):
        """Initialize database tables"""
        try:
            cursor = self.connection.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_paid BOOLEAN DEFAULT FALSE,
                    login_attempts INTEGER DEFAULT 0,
                    last_attempt TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    thumbnail_url TEXT,
                    music_style TEXT,
                    music_file TEXT,
                    duration REAL,
                    resolution TEXT,
                    size REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Create default admin user if not exists
            admin_password_hash = generate_password_hash('admin123')
            print(f"🔑 Creating admin user with hash: {admin_password_hash[:50]}...")
            
            cursor.execute(
                "INSERT OR IGNORE INTO users (name, email, password_hash, is_admin, is_paid) VALUES (?, ?, ?, ?, ?)",
                ('Admin', 'admin@sanpai.com', admin_password_hash, True, True)
            )
            
            self.connection.commit()
            cursor.close()
            print("✅ Database initialized successfully")
            
        except sqlite3.Error as e:
            print(f"❌ Error initializing database: {e}")

    def get_connection(self):
        """Get database connection"""
        if not self.connection:
            self.connect()
        return self.connection

# Create global database instance
db = Database()

# User functions
def add_user(name, email, password_hash, is_admin=False, is_paid=False):
    """Add a new user to the database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, is_admin, is_paid) VALUES (?, ?, ?, ?, ?)",
            (name, email, password_hash, is_admin, is_paid)
        )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error adding user: {e}")
        return False

def get_user_by_email(email):
    """Get user by email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except sqlite3.Error as e:
        print(f"❌ Error getting user: {e}")
        return None

def get_all_users():
    """Get all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, is_admin, is_paid, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        cursor.close()
        return users
    except sqlite3.Error as e:
        print(f"❌ Error getting users: {e}")
        return []

def increment_login_attempts(email):
    """Increment login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET login_attempts = login_attempts + 1, last_attempt = ? WHERE email = ?",
            (datetime.now(), email)
        )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error incrementing login attempts: {e}")
        return False

def reset_login_attempts(email):
    """Reset login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET login_attempts = 0, last_attempt = NULL WHERE email = ?",
            (email,)
        )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error resetting login attempts: {e}")
        return False

def get_login_attempts(email):
    """Get login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT login_attempts FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    except sqlite3.Error as e:
        print(f"❌ Error getting login attempts: {e}")
        return 0

def update_payment_status(user_id, is_paid):
    """Update user payment status"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_paid = ? WHERE id = ?",
            (bool(is_paid), user_id)
        )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error updating payment status: {e}")
        return False

# Video functions
def add_video(user_id, video_url, thumbnail_url, music_style, title, music_file=None, duration=None, resolution=None, size=None):
    """Add a new video to the database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO videos (user_id, video_url, thumbnail_url, music_style, title, music_file, duration, resolution, size) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, video_url, thumbnail_url, music_style, title, music_file, duration, resolution, size)
        )
        conn.commit()
        cursor.close()
        return True
    except sqlite3.Error as e:
        print(f"❌ Error adding video: {e}")
        return False

def get_videos_by_user(user_id):
    """Get all videos for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM videos WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        videos = cursor.fetchall()
        cursor.close()
        return videos
    except sqlite3.Error as e:
        print(f"❌ Error getting user videos: {e}")
        return []

def get_all_videos():
    """Get all videos from all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT v.*, u.name as user_name, u.email as user_email 
            FROM videos v 
            JOIN users u ON v.user_id = u.id 
            ORDER BY v.created_at DESC
        ''')
        videos = cursor.fetchall()
        cursor.close()
        return videos
    except sqlite3.Error as e:
        print(f"❌ Error getting all videos: {e}")
        return []

def init_db():
    """Initialize database (for backward compatibility)"""
    return db.init_db()
