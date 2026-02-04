web: gunicorn --bind 0.0.0.0:$PORT web_dashboard:app
worker: python main.py --telegram $TELEGRAM_BOT_TOKEN $TELEGRAM_BOT_USERNAME
