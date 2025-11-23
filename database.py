import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Database:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = ''
        self.database = 'sanpai_db'
        self.connection = None
        self.connect()
        self.init_db()

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            if self.connection.is_connected():
                print("✅ Connected to MySQL database")
        except Error as e:
            print(f"❌ Error connecting to MySQL: {e}")
            self.create_database()

    def create_database(self):
        """Create database and tables if they don't exist"""
        try:
            conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            conn.close()
            
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.init_db()
        except Error as e:
            print(f"❌ Error creating database: {e}")

    def init_db(self):
        """Initialize database tables"""
        try:
            cursor = self.connection.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_paid BOOLEAN DEFAULT FALSE,
                    login_attempts INT DEFAULT 0,
                    last_attempt TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Videos table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS videos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    video_url VARCHAR(500) NOT NULL,
                    music_style VARCHAR(100),
                    music_file VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Create default admin user if not exists
            admin_password_hash = generate_password_hash('admin123')
            print(f"🔑 Creating admin user with hash: {admin_password_hash[:50]}...")
            
            cursor.execute('''
                INSERT IGNORE INTO users (name, email, password_hash, is_admin, is_paid) 
                VALUES (%s, %s, %s, %s, %s)
            ''', ('Admin', 'admin@sanpai.com', admin_password_hash, True, True))
            
            self.connection.commit()
            cursor.close()
            print("✅ Database initialized successfully")
            
        except Error as e:
            print(f"❌ Error initializing database: {e}")

    def get_connection(self):
        """Get database connection"""
        if not self.connection or not self.connection.is_connected():
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
            "INSERT INTO users (name, email, password_hash, is_admin, is_paid) VALUES (%s, %s, %s, %s, %s)",
            (name, email, password_hash, is_admin, is_paid)
        )
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Error adding user: {e}")
        return False

def get_user_by_email(email):
    """Get user by email"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    except Error as e:
        print(f"❌ Error getting user: {e}")
        return None

def get_all_users():
    """Get all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, email, is_admin, is_paid, created_at FROM users ORDER BY created_at DESC")
        users = cursor.fetchall()
        cursor.close()
        return users
    except Error as e:
        print(f"❌ Error getting users: {e}")
        return []

def increment_login_attempts(email):
    """Increment login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET login_attempts = login_attempts + 1, last_attempt = %s WHERE email = %s",
            (datetime.now(), email)
        )
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Error incrementing login attempts: {e}")
        return False

def reset_login_attempts(email):
    """Reset login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET login_attempts = 0, last_attempt = NULL WHERE email = %s",
            (email,)
        )
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Error resetting login attempts: {e}")
        return False

def get_login_attempts(email):
    """Get login attempts for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT login_attempts FROM users WHERE email = %s", (email,))
        result = cursor.fetchone()
        cursor.close()
        return result[0] if result else 0
    except Error as e:
        print(f"❌ Error getting login attempts: {e}")
        return 0

def update_payment_status(user_id, is_paid):
    """Update user payment status"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET is_paid = %s WHERE id = %s",
            (bool(is_paid), user_id)
        )
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Error updating payment status: {e}")
        return False

# Video functions
def add_video(user_id, video_url, music_style, title, music_file=None):
    """Add a new video to the database"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO videos (user_id, video_url, music_style, title, music_file) VALUES (%s, %s, %s, %s, %s)",
            (user_id, video_url, music_style, title, music_file)
        )
        conn.commit()
        cursor.close()
        return True
    except Error as e:
        print(f"❌ Error adding video: {e}")
        return False

def get_videos_by_user(user_id):
    """Get all videos for a user"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM videos WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        videos = cursor.fetchall()
        cursor.close()
        return videos
    except Error as e:
        print(f"❌ Error getting user videos: {e}")
        return []

def get_all_videos():
    """Get all videos from all users"""
    try:
        conn = db.get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT v.*, u.name as user_name, u.email as user_email 
            FROM videos v 
            JOIN users u ON v.user_id = u.id 
            ORDER BY v.created_at DESC
        ''')
        videos = cursor.fetchall()
        cursor.close()
        return videos
    except Error as e:
        print(f"❌ Error getting all videos: {e}")
        return []

def init_db():
    """Initialize database (for backward compatibility)"""
    return db.init_db()