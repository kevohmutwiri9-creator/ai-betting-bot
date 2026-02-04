# AI Betting Bot Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=web_dashboard.py
ENV FLASK_ENV=production
ENV PORT=10000

# Create non-root user for security
RUN useradd -m -u 1000 bettinguser && chown -R bettinguser:bettinguser /app
USER bettinguser

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/ || exit 1

# Default command
CMD gunicorn --bind 0.0.0.0:10000 web_dashboard:app
