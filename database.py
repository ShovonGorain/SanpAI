import os
import sqlite3
import mysql.connector
from datetime import datetime
from werkzeug.security import generate_password_hash
import subprocess

USE_SQLITE = os.environ.get('USE_SQLITE', 'false').lower() == 'true'

class Database:
    def init_app(self, app):
        self.connection = None
        self.db_type = 'sqlite' if USE_SQLITE else 'mysql'

        if self.db_type == 'mysql':
            self.host = os.environ.get('DB_HOST', 'localhost')
            self.user = os.environ.get('DB_USER', 'root')
            self.password = os.environ.get('DB_PASSWORD', '')
            self.database = os.environ.get('DB_NAME', 'sanpai_db')
        else:
            self.database = 'sanpai.db'

        if self.connect():
            self.init_db()

    @property
    def param_style(self):
        return '?' if self.db_type == 'sqlite' else '%s'

    def connect(self):
        """Establish database connection."""
        try:
            if self.db_type == 'sqlite':
                self.connection = sqlite3.connect(self.database, check_same_thread=False)
                self.connection.row_factory = self.dict_factory
            else:
                self.connection = mysql.connector.connect(
                    host=self.host, user=self.user, password=self.password, database=self.database,
                    auth_plugin='mysql_native_password'
                )
            print(f"✅ Connected to {self.db_type.capitalize()} database")
            return True
        except (sqlite3.Error, mysql.connector.Error) as e:
            print(f"❌ Error connecting to {self.db_type.capitalize()}: {e}")
            if self.db_type == 'mysql' and 'Unknown database' in str(e):
                return self.create_mysql_database()
            return False

    def create_mysql_database(self):
        """Create MySQL database if it doesn't exist."""
        try:
            conn = mysql.connector.connect(host=self.host, user=self.user, password=self.password)
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            cursor.close()
            conn.close()
            print(f"✅ Database '{self.database}' created.")
            return self.connect()
        except mysql.connector.Error as e:
            print(f"❌ Error creating MySQL database: {e}")
            return False

    @staticmethod
    def dict_factory(cursor, row):
        """Convert SQLite results to dicts."""
        d = {}
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_connection(self):
        """Get database connection, reconnect if necessary."""
        try:
            if self.db_type == 'mysql' and (not self.connection or not self.connection.is_connected()):
                self.connect()
            elif self.db_type == 'sqlite' and not self.connection:
                 self.connect()
        except (sqlite3.Error, mysql.connector.Error) as e:
            print(f"❌ Error checking connection: {e}")
            self.connect()
        return self.connection

    def execute(self, query, params=(), multi=False):
        """Execute a query and handle reconnections."""
        conn = self.get_connection()
        # In python3, mysql-connector-python wants dictionary=True for dict results
        cursor = conn.cursor(dictionary=True) if self.db_type == 'mysql' else conn.cursor()
        try:
            cursor.execute(query.replace('?', self.param_style), params)
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            return cursor
        except (sqlite3.Error, mysql.connector.Error) as e:
            print(f"❌ Query failed: {e}. Reconnecting...")
            self.connect() # Reconnect
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True) if self.db_type == 'mysql' else conn.cursor()
            cursor.execute(query.replace('?', self.param_style), params)
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                conn.commit()
            return cursor

    def init_db(self):
        """Initialize all database tables."""

        # Table schemas (using generic types)
        tables = {
            "users": [
                "id INTEGER PRIMARY KEY" + (" AUTO_INCREMENT" if self.db_type == 'mysql' else " AUTOINCREMENT"),
                "name TEXT NOT NULL",
                "email TEXT UNIQUE NOT NULL",
                "password_hash TEXT NOT NULL",
                "is_admin BOOLEAN DEFAULT 0",
                "is_paid BOOLEAN DEFAULT 0",
                "login_attempts INTEGER DEFAULT 0",
                "last_attempt TIMESTAMP NULL",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ],
            "videos": [
                "id INTEGER PRIMARY KEY" + (" AUTO_INCREMENT" if self.db_type == 'mysql' else " AUTOINCREMENT"),
                "user_id INTEGER NOT NULL",
                "title TEXT NOT NULL",
                "video_url TEXT NOT NULL",
                "music_style TEXT",
                "music_file TEXT",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "thumbnail_url TEXT",
                "duration REAL",
                "resolution TEXT",
                "size REAL",
                "views INTEGER DEFAULT 0",
                "FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE"
            ],
            "settings": [
                "key_name TEXT PRIMARY KEY",
                "key_value TEXT NOT NULL"
            ],
            "recent_activity": [
                "id INTEGER PRIMARY KEY" + (" AUTO_INCREMENT" if self.db_type == 'mysql' else " AUTOINCREMENT"),
                "activity_type TEXT NOT NULL",
                "message TEXT NOT NULL",
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ]
        }

        for table_name, schema in tables.items():
            query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(schema)})"
            self.execute(query)

        # Create default admin user
        admin_pass_hash = generate_password_hash('admin123')
        if self.db_type == 'sqlite':
            insert_sql = "INSERT OR IGNORE INTO users (name, email, password_hash, is_admin, is_paid) VALUES (?, ?, ?, ?, ?)"
        else:
            insert_sql = "INSERT IGNORE INTO users (name, email, password_hash, is_admin, is_paid) VALUES (%s, %s, %s, %s, %s)"

        self.execute(insert_sql, ('Admin', 'admin@sanpai.com', admin_pass_hash, 1, 1))

        # Add new columns to videos table if they don't exist
        video_columns = {
            'thumbnail_url': 'TEXT',
            'duration': 'REAL',
            'resolution': 'TEXT',
            'size': 'REAL',
            'views': 'INTEGER DEFAULT 0'
        }

        cursor = self.execute("PRAGMA table_info(videos)")
        existing_columns = [col['name'] for col in cursor.fetchall()]

        for col_name, col_type in video_columns.items():
            if col_name not in existing_columns:
                self.execute(f"ALTER TABLE videos ADD COLUMN {col_name} {col_type}")

        # Add indexes for performance
        self.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos (user_id)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos (created_at)")
        self.execute("CREATE INDEX IF NOT EXISTS idx_videos_views ON videos (views)")

        print("✅ Database initialized successfully")

    def add_user(self, name, email, password_hash, is_admin=False, is_paid=False):
        sql = "INSERT INTO users (name, email, password_hash, is_admin, is_paid) VALUES (?, ?, ?, ?, ?)"
        self.execute(sql, (name, email, password_hash, 1 if is_admin else 0, 1 if is_paid else 0))
        return True

    def get_user_by_email(self, email):
        cursor = self.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()

    def get_user_by_id(self, user_id):
        cursor = self.execute("SELECT id, name, email, is_admin, is_paid, created_at FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    def get_all_users(self, page=1, per_page=10, search_query=None):
        params = []
        count_query = "SELECT COUNT(*) as total FROM users"
        base_query = "SELECT id, name, email, is_admin, is_paid, created_at FROM users"

        if search_query:
            search_term = f"%{search_query}%"
            count_query += " WHERE name LIKE ? OR email LIKE ?"
            base_query += " WHERE name LIKE ? OR email LIKE ?"
            params.extend([search_term, search_term])

        total_users = self.execute(count_query, params).fetchone()['total']

        offset = (page - 1) * per_page
        base_query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        users = self.execute(base_query, params).fetchall()

        return {'users': users, 'total': total_users, 'page': page, 'per_page': per_page}

    def delete_user(self, user_id):
        self.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return True

    def update_user_password(self, user_id, password_hash):
        self.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id))
        return True

    def update_user_info(self, user_id, name, email):
        self.execute("UPDATE users SET name = ?, email = ? WHERE id = ?", (name, email, user_id))
        return True

    def increment_login_attempts(self, email):
        self.execute("UPDATE users SET login_attempts = login_attempts + 1, last_attempt = CURRENT_TIMESTAMP WHERE email = ?", (email,))
        return True

    def reset_login_attempts(self, email):
        self.execute("UPDATE users SET login_attempts = 0, last_attempt = NULL WHERE email = ?", (email,))
        return True

    def get_login_attempts(self, email):
        cursor = self.execute("SELECT login_attempts FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        return result['login_attempts'] if result else 0

    def get_videos_by_user(self, user_id):
        cursor = self.execute("SELECT * FROM videos WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()

    def update_payment_status(self, user_id, is_paid):
        self.execute("UPDATE users SET is_paid = ? WHERE id = ?", (1 if is_paid else 0, user_id))
        return True

    def add_video(self, user_id, video_url, thumbnail_url, title, **kwargs):
        sql = """
            INSERT INTO videos (user_id, video_url, thumbnail_url, title, music_file, duration, resolution, size)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_id, video_url, thumbnail_url, title, kwargs.get('music_file'),
                  kwargs.get('duration'), kwargs.get('resolution'), kwargs.get('size'))
        self.execute(sql, params)
        return True

    def get_all_videos(self, page=1, per_page=10, filter_by='recent'):
        count_query = "SELECT COUNT(*) as total FROM videos"
        base_query = "SELECT v.*, u.name as user_name FROM videos v JOIN users u ON v.user_id = u.id"

        if filter_by == 'popular':
            order_by = " ORDER BY v.views DESC"
        else: # recent
            order_by = " ORDER BY v.created_at DESC"

        total = self.execute(count_query).fetchone()['total']

        offset = (page - 1) * per_page
        paged_query = base_query + order_by + " LIMIT ? OFFSET ?"
        videos = self.execute(paged_query, (per_page, offset)).fetchall()

        return {'videos': videos, 'total': total, 'page': page, 'per_page': per_page}

    def delete_video(self, video_id):
        self.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        return True

    def increment_video_views(self, video_id):
        self.execute("UPDATE videos SET views = views + 1 WHERE id = ?", (video_id,))
        return True

    def get_setting(self, key_name):
        cursor = self.execute("SELECT key_value FROM settings WHERE key_name = ?", (key_name,))
        result = cursor.fetchone()
        return result['key_value'] if result else None

    def update_setting(self, key_name, key_value):
        if self.db_type == 'sqlite':
            sql = "INSERT INTO settings (key_name, key_value) VALUES (?, ?) ON CONFLICT(key_name) DO UPDATE SET key_value = excluded.key_value"
        else:
            sql = "INSERT INTO settings (key_name, key_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE key_value = VALUES(key_value)"
        self.execute(sql, (key_name, key_value))
        return True

    def optimize_database(self):
        if self.db_type == 'sqlite':
            self.execute("VACUUM")
            return True
        else: # mysql
            cursor = self.execute("SHOW TABLES")
            tables = [row[0] for row in cursor.fetchall()]
            for table in tables:
                self.execute(f"OPTIMIZE TABLE {table}")
            return True

    def backup_database(self):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if self.db_type == 'sqlite':
            backup_path = f"backup_{timestamp}.db"
            backup_conn = sqlite3.connect(backup_path)
            with backup_conn:
                self.connection.backup(backup_conn)
            backup_conn.close()
            return backup_path
        else: # mysql
            backup_path = f"backup_{timestamp}.sql"
            try:
                with open(backup_path, 'w') as f:
                    env = os.environ.copy()
                    env['MYSQL_PWD'] = self.password
                    subprocess.run(
                        ['mysqldump', '-u', self.user, self.database],
                        stdout=f, check=True, env=env
                    )
                return backup_path
            except Exception as e:
                print(f"❌ Error backing up MySQL database: {e}")
                return None

    def clear_all_data(self):
        self.execute("DELETE FROM videos")
        self.execute("DELETE FROM users WHERE is_admin = 0")
        return True

    def get_recent_activity(self):
        cursor = self.execute("SELECT * FROM recent_activity ORDER BY created_at DESC LIMIT 5")
        return cursor.fetchall()

    def add_activity(self, activity_type, message):
        sql = "INSERT INTO recent_activity (activity_type, message) VALUES (?, ?)"
        self.execute(sql, (activity_type, message))
        return True

# Global DB instance and functions for backward compatibility with app.py
db = Database()

def get_user_by_email(email): return db.get_user_by_email(email)
def get_user_by_id(user_id): return db.get_user_by_id(user_id)
def add_user(name, email, pass_hash, is_admin=False):
    return db.add_user(name, email, pass_hash, is_admin)
def get_all_users(page=1, per_page=10, search_query=None):
    return db.get_all_users(page, per_page, search_query)
def delete_user(user_id): return db.delete_user(user_id)
def update_user_password(user_id, pass_hash): return db.update_user_password(user_id, pass_hash)
def update_user_info(user_id, name, email): return db.update_user_info(user_id, name, email)
def add_video(user_id, video_url, thumb_url, title, **kwargs):
    return db.add_video(user_id, video_url, thumb_url, title, **kwargs)
def get_all_videos(page=1, per_page=10, filter_by='recent'):
    return db.get_all_videos(page, per_page, filter_by)
def delete_video(video_id): return db.delete_video(video_id)
def increment_video_views(video_id): return db.increment_video_views(video_id)
def get_setting(key): return db.get_setting(key)
def update_setting(key, value): return db.update_setting(key, value)
def backup_database(): return db.backup_database()
def optimize_database(): return db.optimize_database()
def clear_all_data(): return db.clear_all_data()
def get_recent_activity(): return db.get_recent_activity()
def add_activity(act_type, msg): return db.add_activity(act_type, msg)
def increment_login_attempts(email): return db.increment_login_attempts(email)
def reset_login_attempts(email): return db.reset_login_attempts(email)
def get_login_attempts(email): return db.get_login_attempts(email)
def get_videos_by_user(user_id): return db.get_videos_by_user(user_id)
def update_payment_status(user_id, is_paid): return db.update_payment_status(user_id, is_paid)
# ... add other functions if needed ...
def init_db(): pass # No longer needed but keep for compatibility
