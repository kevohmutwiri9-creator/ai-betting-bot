from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os

app = Flask(__name__)

# Trust Vercel's headers
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Import your main app
from web_dashboard import app as main_app

# Copy routes and configuration
app.config.update(main_app.config)
app.view_functions = main_app.view_functions
app.url_map = main_app.url_map

if __name__ == "__main__":
    app.run()
