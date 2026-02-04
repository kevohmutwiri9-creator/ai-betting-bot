import os
from flask import Flask

# Heroku database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///betting_data.db')

# Fix PostgreSQL URL for SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Flask configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SECRET_KEY'] = os.getenv('SESSION_SECRET_KEY', 'dev-secret-key')

# Production settings
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
