"""
Configuration Settings for AI Betting Bot
Replace these placeholder values with your actual credentials
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', '')

# Betika Affiliate Configuration
BETIKA_AFFILIATE_ID = "YOUR_AFFILIATE_ID"  # Get from Betika affiliate program
BETIKA_BASE_URL = "https://www.betika.com"

# Application URLs
DOWNLOAD_LINK = "https://yourwebsite.com/download"  # Your bot download page
LANDING_PAGE_URL = "https://yourwebsite.com"  # Your landing page

# Database Configuration
DATABASE_PATH = "betting_data.db"
AFFILIATE_DB_PATH = "affiliate_data.db"
ANALYTICS_DB_PATH = "analytics.db"
VIRAL_GROWTH_DB_PATH = "viral_growth.db"

# API Configuration
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'your-secret-api-key-here')
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'your-webhook-secret-here')

# Email Configuration (for notifications)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')

# Payment Processing (Stripe/PayPal)
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET', '')

# Analytics & Tracking
GOOGLE_ANALYTICS_ID = os.getenv('GOOGLE_ANALYTICS_ID', '')
FACEBOOK_PIXEL_ID = os.getenv('FACEBOOK_PIXEL_ID', '')

# Feature Flags
ENABLE_PREMIUM_FEATURES = True
ENABLE_ANALYTICS_TRACKING = True
ENABLE_EMAIL_NOTIFICATIONS = False  # Set to True after configuring email
ENABLE_PAYMENT_PROCESSING = False  # Set to True after configuring payment

# Rate Limiting
API_RATE_LIMIT = 100  # requests per hour
TELEGRAM_RATE_LIMIT = 30  # messages per minute

# Security
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'your-session-secret-key-here')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
PASSWORD_SALT_ROUNDS = int(os.getenv('PASSWORD_SALT_ROUNDS', '12'))

# Development/Production
DEBUG_MODE = True
ENVIRONMENT = "development"  # Change to "production" for live deployment
