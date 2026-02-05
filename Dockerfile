# AI Betting Bot Docker Configuration
# Multi-stage build for optimized image size

# Stage 1: Builder
FROM python:3.11-slim-bookworm AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /build

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.11-slim-bookworm AS production

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=web_dashboard.py
ENV FLASK_ENV=production
ENV PORT=10000
ENV PYTHONUNBUFFERED=1

# Create non-root user for security
RUN useradd -m -u 1000 bettinguser && chown -R bettinguser:bettinguser /app
USER bettinguser

# Expose port
EXPOSE 10000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Run with gunicorn for production
CMD ["gunicorn", "--chdir", "/app", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120", "web_dashboard:app"]
