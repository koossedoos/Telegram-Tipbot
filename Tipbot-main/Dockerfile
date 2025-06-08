# Community Tipbot - Docker Configuration
# Powered By Aegisum EcoSystem

FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    wget \
    curl \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    sqlite3 \
    supervisor \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -s /bin/bash tipbot

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data data/wallets data/backups admin_dashboard/static/css admin_dashboard/static/js

# Set permissions
RUN chown -R tipbot:tipbot /app
RUN chmod +x start_bot.py setup.py scripts/*.sh

# Create supervisor configuration
RUN echo '[supervisord]' > /etc/supervisor/conf.d/tipbot.conf && \
    echo 'nodaemon=true' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'user=root' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo '' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo '[program:tipbot]' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'command=/usr/bin/python3 /app/start_bot.py' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'user=tipbot' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'stdout_logfile=/app/logs/bot.log' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'stderr_logfile=/app/logs/bot_error.log' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo '' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo '[program:dashboard]' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'command=/usr/bin/python3 /app/admin_dashboard/app.py' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'directory=/app' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'user=tipbot' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'autostart=true' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'autorestart=true' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'stdout_logfile=/app/logs/dashboard.log' >> /etc/supervisor/conf.d/tipbot.conf && \
    echo 'stderr_logfile=/app/logs/dashboard_error.log' >> /etc/supervisor/conf.d/tipbot.conf

# Create nginx configuration
RUN echo 'server {' > /etc/nginx/sites-available/tipbot && \
    echo '    listen 80;' >> /etc/nginx/sites-available/tipbot && \
    echo '    server_name _;' >> /etc/nginx/sites-available/tipbot && \
    echo '    location / {' >> /etc/nginx/sites-available/tipbot && \
    echo '        proxy_pass http://127.0.0.1:12000;' >> /etc/nginx/sites-available/tipbot && \
    echo '        proxy_set_header Host $host;' >> /etc/nginx/sites-available/tipbot && \
    echo '        proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/sites-available/tipbot && \
    echo '        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/sites-available/tipbot && \
    echo '        proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/sites-available/tipbot && \
    echo '    }' >> /etc/nginx/sites-available/tipbot && \
    echo '}' >> /etc/nginx/sites-available/tipbot && \
    ln -s /etc/nginx/sites-available/tipbot /etc/nginx/sites-enabled/ && \
    rm /etc/nginx/sites-enabled/default

# Create startup script
RUN echo '#!/bin/bash' > /app/docker-entrypoint.sh && \
    echo 'set -e' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Check if configuration exists' >> /app/docker-entrypoint.sh && \
    echo 'if [ ! -f /app/config/config.json ]; then' >> /app/docker-entrypoint.sh && \
    echo '    echo "❌ Configuration file not found!"' >> /app/docker-entrypoint.sh && \
    echo '    echo "Please mount your config.json to /app/config/config.json"' >> /app/docker-entrypoint.sh && \
    echo '    echo "Example: docker run -v /path/to/config.json:/app/config/config.json ..."' >> /app/docker-entrypoint.sh && \
    echo '    exit 1' >> /app/docker-entrypoint.sh && \
    echo 'fi' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Initialize database if needed' >> /app/docker-entrypoint.sh && \
    echo 'if [ ! -f /app/data/tipbot.db ]; then' >> /app/docker-entrypoint.sh && \
    echo '    echo "🔧 Initializing database..."' >> /app/docker-entrypoint.sh && \
    echo '    cd /app && python3 -c "from src.database import Database; Database(\"data/tipbot.db\")"' >> /app/docker-entrypoint.sh && \
    echo 'fi' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Start nginx' >> /app/docker-entrypoint.sh && \
    echo 'service nginx start' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Start supervisor' >> /app/docker-entrypoint.sh && \
    echo 'exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf' >> /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Expose ports
EXPOSE 80 12000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:12000/health || exit 1

# Set user
USER tipbot

# Start command
CMD ["/app/docker-entrypoint.sh"]