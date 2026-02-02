"""
User Authentication System for AI Betting Bot
Handles login, registration, and session management
"""

import sqlite3
import hashlib
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from config import SESSION_SECRET_KEY, JWT_SECRET_KEY

class AuthManager:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize user database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_premium BOOLEAN DEFAULT FALSE,
                created_at TEXT,
                last_login TEXT,
                api_key TEXT UNIQUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT,
                expires_at TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_api_key(self, user_id):
        """Generate unique API key for user"""
        return f"ak_{user_id}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:16]}"
    
    def register_user(self, username, email, password):
        """Register new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
            if cursor.fetchone():
                return {"success": False, "error": "User already exists"}
            
            # Create new user
            password_hash = self.hash_password(password)
            api_key = self.generate_api_key(username)
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at, api_key)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, password_hash, created_at, api_key))
            
            conn.commit()
            conn.close()
            
            return {"success": True, "api_key": api_key}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def authenticate_user(self, username, password):
        """Authenticate user and return JWT token"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            cursor.execute('''
                SELECT id, username, email, is_premium FROM users 
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            
            user = cursor.fetchone()
            conn.close()
            
            if not user:
                return {"success": False, "error": "Invalid credentials"}
            
            # Generate JWT token
            payload = {
                'user_id': user[0],
                'username': user[1],
                'email': user[2],
                'is_premium': bool(user[3]),
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
            
            # Update last login
            self.update_last_login(user[0])
            
            return {
                "success": True,
                "token": token,
                "user": {
                    "id": user[0],
                    "username": user[1],
                    "email": user[2],
                    "is_premium": bool(user[3])
                }
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def update_last_login(self, user_id):
        """Update user's last login time"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET last_login = ? WHERE id = ?
            ''', (datetime.now().isoformat(), user_id))
            conn.commit()
            conn.close()
        except:
            pass
    
    def verify_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            return {"success": True, "user": payload}
        except jwt.ExpiredSignatureError:
            return {"success": False, "error": "Token expired"}
        except jwt.InvalidTokenError:
            return {"success": False, "error": "Invalid token"}
    
    def upgrade_to_premium(self, user_id):
        """Upgrade user to premium"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE users SET is_premium = TRUE WHERE id = ?
            ''', (user_id,))
            conn.commit()
            conn.close()
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

# Flask decorators for authentication
auth_manager = AuthManager()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "error": "No token provided"}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        result = auth_manager.verify_token(token)
        if not result['success']:
            return jsonify(result), 401
        
        g.current_user = result['user']
        return f(*args, **kwargs)
    return decorated_function

def require_premium(f):
    """Decorator to require premium subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"success": False, "error": "No token provided"}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        result = auth_manager.verify_token(token)
        if not result['success']:
            return jsonify(result), 401
        
        if not result['user'].get('is_premium', False):
            return jsonify({"success": False, "error": "Premium subscription required"}), 402
        
        g.current_user = result['user']
        return f(*args, **kwargs)
    return decorated_function
