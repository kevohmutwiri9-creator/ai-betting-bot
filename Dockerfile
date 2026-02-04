# AI Betting Bot Docker Configuration
FROM python:3.9-slim

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
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=web_dashboard.py
ENV FLASK_ENV=production

# Create non-root user for security
RUN useradd -m -u 1000 bettinguser && chown -R bettinguser:bettinguser /app
USER bettinguser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Default command
CMD ["python", "main.py", "--web"]
