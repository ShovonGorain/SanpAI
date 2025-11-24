import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self):
        self.db_name = 'sanpai.db'
        self.init_db()

    def get_connection(self):
        """Establish database connection"""
        try:
            conn = sqlite3.connect(self.db_name, check_same_thread=False)
            # Enable dictionary access for rows
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ Error connecting to SQLite: {e}")
            return None

    def init_db(self):
        """Initialize database tables"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    is_admin BOOLEAN DEFAULT 0,
                    is_paid BOOLEAN DEFAULT 0,
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
                    music_style TEXT,
                    music_file TEXT,
                    thumbnail_url TEXT,
                    duration TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Add columns if they don't exist (migration for SQLite)
            # SQLite doesn't have "DESCRIBE", so we check PRAGMA table_info
            cursor.execute("PRAGMA table_info(videos)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'thumbnail_url' not in columns:
                print("Updating videos table: adding thumbnail_url")
                cursor.execute("ALTER TABLE videos ADD COLUMN thumbnail_url TEXT")

            if 'duration' not in columns:
                print("Updating videos table: adding duration")
                cursor.execute("ALTER TABLE videos ADD COLUMN duration TEXT")

            # Create default admin user if not exists
            cursor.execute("SELECT * FROM users WHERE email = ?", ('admin@sanpai.com',))
            if not cursor.fetchone():
                admin_password_hash = generate_password_hash('admin123')
                print(f"🔑 Creating admin user with hash: {admin_password_hash[:50]}...")
                cursor.execute('''
                    INSERT INTO users (name, email, password_hash, is_admin, is_paid)
                    VALUES (?, ?, ?, ?, ?)
                ''', ('Admin', 'admin@sanpai.com', admin_password_hash, True, True))
            
            conn.commit()
            conn.close()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")

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
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error adding user: {e}")
        return False

def get_user_by_email(email):
    """Get user by email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()

        if row:
            # Convert Row object to dict
            return dict(row)
        return None
    except Exception as e:
        print(f"❌ Error getting user: {e}")
        return None

def get_all_users():
    """Get all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, email, is_admin, is_paid, created_at FROM users ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
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
        conn.close()
        return True
    except Exception as e:
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
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error resetting login attempts: {e}")
        return False

def get_login_attempts(email):
    """Get login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT login_attempts FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        return result['login_attempts'] if result else 0
    except Exception as e:
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
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Error updating payment status: {e}")
        return False

# Video functions
def add_video(user_id, video_url, music_style, title, music_file=None, thumbnail_url=None, duration=None):
    """Add a new video to the database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO videos (user_id, video_url, music_style, title, music_file, thumbnail_url, duration) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, video_url, music_style, title, music_file, thumbnail_url, duration)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
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
        rows = cursor.fetchall()
        conn.close()

        # Convert created_at string to datetime object if needed, usually SQLite returns string
        videos = []
        for row in rows:
            video = dict(row)
            if isinstance(video['created_at'], str):
                try:
                    video['created_at'] = datetime.strptime(video['created_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    # If parsing fails or format differs, keep as is or try another format
                    try:
                         video['created_at'] = datetime.strptime(video['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            videos.append(video)
        return videos
    except Exception as e:
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
        rows = cursor.fetchall()
        conn.close()

        videos = []
        for row in rows:
            video = dict(row)
            if isinstance(video['created_at'], str):
                try:
                    video['created_at'] = datetime.strptime(video['created_at'], '%Y-%m-%d %H:%M:%S')
                except:
                    try:
                         video['created_at'] = datetime.strptime(video['created_at'].split('.')[0], '%Y-%m-%d %H:%M:%S')
                    except:
                        pass
            videos.append(video)
        return videos
    except Exception as e:
        print(f"❌ Error getting all videos: {e}")
        return []

def init_db():
    """Initialize database (for backward compatibility)"""
    return db.init_db()
