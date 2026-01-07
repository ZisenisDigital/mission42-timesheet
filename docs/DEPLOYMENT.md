# Deployment Guide

Guide for deploying Mission42 Timesheet to production environments.

## Prerequisites

- Python 3.11+
- uv package manager
- PocketBase binary
- Domain name (for production)
- SSL certificate (for HTTPS)

## Environment Setup

### 1. Production Environment Variables

Create `.env.production`:

```bash
# PocketBase
POCKETBASE_URL=http://127.0.0.1:8090
PB_ADMIN_EMAIL=admin@yourdomain.com
PB_ADMIN_PASSWORD=strong-secure-password

# API Keys
WAKATIME_API_KEY=waka_your_key
GITHUB_TOKEN=ghp_your_token

# Google OAuth
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your_secret
GOOGLE_REDIRECT_URI=https://yourdomain.com/oauth/google/callback

# Encryption
ENCRYPTION_KEY=your-generated-fernet-key

# FastAPI
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
FASTAPI_DEBUG=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/mission42-timesheet/app.log
```

## Deployment Options

### Option 1: Systemd Services (Recommended for Linux)

#### 1. Create PocketBase Service

`/etc/systemd/system/pocketbase.service`:

```ini
[Unit]
Description=PocketBase Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mission42-timesheet/pocketbase
ExecStart=/opt/mission42-timesheet/pocketbase/pocketbase serve --http=127.0.0.1:8090
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 2. Create FastAPI Service

`/etc/systemd/system/mission42-api.service`:

```ini
[Unit]
Description=Mission42 Timesheet API
After=network.target pocketbase.service
Requires=pocketbase.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mission42-timesheet
Environment="PATH=/opt/mission42-timesheet/.venv/bin"
EnvironmentFile=/opt/mission42-timesheet/.env.production
ExecStart=/opt/mission42-timesheet/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

#### 3. Enable and Start Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable pocketbase mission42-api
sudo systemctl start pocketbase mission42-api
sudo systemctl status pocketbase mission42-api
```

### Option 2: Docker Compose

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  pocketbase:
    image: ghcr.io/muchobien/pocketbase:latest
    restart: unless-stopped
    ports:
      - "8090:8090"
    volumes:
      - ./pocketbase/pb_data:/pb_data
      - ./pocketbase/pb_migrations:/pb_migrations
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:8090/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  api:
    build: .
    restart: unless-stopped
    ports:
      - "8000:8000"
    depends_on:
      - pocketbase
    env_file:
      - .env.production
    volumes:
      - ./logs:/app/logs
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - api
      - pocketbase
```

`Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY app ./app
COPY scripts ./scripts

# Install dependencies
RUN uv sync --frozen

# Create logs directory
RUN mkdir -p /app/logs

# Run migrations and seeds on startup
CMD ["sh", "-c", "uv run python scripts/seed_settings.py && uv run python scripts/seed_work_packages.py && uv run python scripts/seed_project_specs.py && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

## Nginx Configuration

### Reverse Proxy with SSL

`nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream pocketbase {
        server pocketbase:8090;
    }

    upstream api {
        server api:8000;
    }

    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;

        # PocketBase admin UI
        location /_/ {
            proxy_pass http://pocketbase;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # PocketBase API
        location /api/ {
            proxy_pass http://pocketbase;
            proxy_set_header Host $host;
        }

        # FastAPI
        location / {
            proxy_pass http://api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

## Security Checklist

- [ ] Use strong admin password
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Restrict PocketBase admin UI to specific IPs
- [ ] Rotate API keys regularly
- [ ] Set secure ENCRYPTION_KEY
- [ ] Enable firewall (ufw/iptables)
- [ ] Regular backups of pb_data directory
- [ ] Monitor logs for suspicious activity
- [ ] Keep dependencies updated

## Monitoring

### Logs

```bash
# System logs
sudo journalctl -u pocketbase -f
sudo journalctl -u mission42-api -f

# Application logs
tail -f /var/log/mission42-timesheet/app.log

# Docker logs
docker-compose logs -f api
docker-compose logs -f pocketbase
```

### Health Checks

```bash
# API health
curl https://yourdomain.com/health

# Scheduler status
curl https://yourdomain.com/status/scheduler

# PocketBase health
curl http://127.0.0.1:8090/api/health
```

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# /opt/mission42-timesheet/backup.sh

BACKUP_DIR="/backups/mission42"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup PocketBase data
tar -czf "$BACKUP_DIR/pb_data_$DATE.tar.gz" /opt/mission42-timesheet/pocketbase/pb_data

# Keep only last 30 days
find "$BACKUP_DIR" -name "pb_data_*.tar.gz" -mtime +30 -delete
```

Add to crontab:

```bash
0 2 * * * /opt/mission42-timesheet/backup.sh
```

## Troubleshooting

### Service won't start

```bash
# Check service status
sudo systemctl status pocketbase
sudo systemctl status mission42-api

# Check logs
sudo journalctl -u pocketbase -n 50
sudo journalctl -u mission42-api -n 50
```

### High memory usage

```bash
# Restart services
sudo systemctl restart pocketbase mission42-api

# Check resource usage
htop
```

### Database corruption

```bash
# Stop services
sudo systemctl stop mission42-api pocketbase

# Restore from backup
tar -xzf /backups/mission42/pb_data_YYYYMMDD_HHMMSS.tar.gz -C /opt/mission42-timesheet/pocketbase/

# Start services
sudo systemctl start pocketbase mission42-api
```

## Scaling

For high-load scenarios:

1. **Horizontal Scaling**: Deploy multiple API instances behind load balancer
2. **Database**: Consider migrating from SQLite to PostgreSQL (requires PocketBase Plus)
3. **Caching**: Add Redis for session/token caching
4. **CDN**: Use CDN for static assets

## Support

For deployment issues:
- GitHub Issues: https://github.com/ZisenisDigital/mission42-timesheet/issues
- Check logs first
- Include environment details when reporting issues
