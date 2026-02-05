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
WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', '')

# Football API Configuration
API_FOOTBALL_KEY = os.getenv('API_FOOTBALL_KEY', '')
FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
SPORTMONKS_TOKEN = os.getenv('SPORTMONKS_TOKEN', '')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')

# API Enable Flags
ENABLE_FOOTBALL_DATA_API = os.getenv('ENABLE_FOOTBALL_DATA_API', 'true').lower() == 'true'
ENABLE_API_FOOTBALL = os.getenv('ENABLE_API_FOOTBALL', 'true').lower() == 'true'
ENABLE_SPORTMONKS = os.getenv('ENABLE_SPORTMONKS', 'false').lower() == 'true'
ENABLE_BETIKA_API = os.getenv('ENABLE_BETIKA_API', 'true').lower() == 'true'

# Update Intervals (seconds)
MATCHES_UPDATE_INTERVAL = int(os.getenv('MATCHES_UPDATE_INTERVAL', '60'))
ODDS_UPDATE_INTERVAL = int(os.getenv('ODDS_UPDATE_INTERVAL', '30'))
LIVE_SCORES_UPDATE_INTERVAL = int(os.getenv('LIVE_SCORES_UPDATE_INTERVAL', '15'))

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

# Kelly Criterion Settings
KELLY_FRACTION = float(os.getenv('KELLY_FRACTION', '0.5'))
MAX_STAKE_PERCENT = float(os.getenv('MAX_STAKE_PERCENT', '0.1'))
MIN_STAKE = float(os.getenv('MIN_STAKE', '1.0'))

# Auto-Betting Settings
AUTO_BET_ENABLED = os.getenv('AUTO_BET_ENABLED', 'false').lower() == 'true'
MIN_VALUE_THRESHOLD = float(os.getenv('MIN_VALUE_THRESHOLD', '0.05'))
CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', '0.6'))

# Browser Automation
HEADLESS_BROWSER = os.getenv('HEADLESS_BROWSER', 'true').lower() == 'true'
AUTO_LOGIN_ENABLED = os.getenv('AUTO_LOGIN_ENABLED', 'false').lower() == 'true'

# Notifications
ENABLE_TELEGRAM_NOTIFICATIONS = os.getenv('ENABLE_TELEGRAM_NOTIFICATIONS', 'true').lower() == 'true'
NOTIFY_ON_BET_PLACED = os.getenv('NOTIFY_ON_BET_PLACED', 'true').lower() == 'true'
NOTIFY_ON_BET_RESULT = os.getenv('NOTIFY_ON_BET_RESULT', 'true').lower() == 'true'
NOTIFY_ON_VALUE_DETECTED = os.getenv('NOTIFY_ON_VALUE_DETECTED', 'true').lower() == 'true'

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Security
SESSION_SECRET_KEY = os.getenv('SESSION_SECRET_KEY', 'your-session-secret-key-here')
JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-here')
PASSWORD_SALT_ROUNDS = int(os.getenv('PASSWORD_SALT_ROUNDS', '12'))

# Development/Production - Read from environment variables
DEBUG_MODE = os.getenv('DEBUG_MODE', 'False').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
