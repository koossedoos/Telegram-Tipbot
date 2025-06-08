# Community Tipbot - Deployment Guide

Complete deployment guide for the Community Tipbot on various platforms.

## 🚀 Quick Deployment Options

### Option 1: Docker (Recommended)
```bash
# Clone repository
git clone https://github.com/your-username/community-tipbot.git
cd community-tipbot

# Configure
cp config/config.example.json config/config.json
nano config/config.json  # Edit with your settings

# Deploy with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f tipbot
```

### Option 2: Manual Installation
```bash
# Clone and setup
git clone https://github.com/your-username/community-tipbot.git
cd community-tipbot

# Run setup script
python3 setup.py

# Install wallets
./scripts/install_wallets.sh

# Start bot
./start.sh
```

### Option 3: One-Line Installer
```bash
curl -sSL https://raw.githubusercontent.com/your-username/community-tipbot/main/scripts/quick-install.sh | bash
```

## 🐳 Docker Deployment (Detailed)

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Step 1: Prepare Configuration
```bash
# Create project directory
mkdir community-tipbot-deploy
cd community-tipbot-deploy

# Download docker-compose.yml
wget https://raw.githubusercontent.com/your-username/community-tipbot/main/docker-compose.yml

# Create config directory
mkdir config

# Download and edit configuration
wget -O config/config.json https://raw.githubusercontent.com/your-username/community-tipbot/main/config/config.example.json
nano config/config.json
```

### Step 2: Configure Bot
Edit `config/config.json`:
```json
{
  "bot": {
    "token": "YOUR_BOT_TOKEN_FROM_BOTFATHER",
    "admin_users": [YOUR_TELEGRAM_USER_ID]
  }
}
```

### Step 3: Deploy
```bash
# Start services
docker-compose up -d

# Check logs
docker-compose logs -f tipbot

# Access dashboard
open http://localhost:12000
```

### Step 4: Install Wallets
```bash
# Enter container
docker-compose exec tipbot bash

# Install wallets
./scripts/install_wallets.sh

# Exit container
exit

# Restart to apply changes
docker-compose restart tipbot
```

## 🖥️ VPS Deployment

### Recommended VPS Specs
- **CPU:** 2+ cores
- **RAM:** 4GB+ 
- **Storage:** 20GB+ SSD
- **OS:** Ubuntu 20.04+ LTS
- **Network:** 100Mbps+

### Popular VPS Providers
- **DigitalOcean:** $20/month droplet
- **Linode:** $20/month VPS
- **Vultr:** $20/month instance
- **AWS EC2:** t3.medium instance
- **Google Cloud:** e2-medium instance

### VPS Setup Script
```bash
#!/bin/bash
# Community Tipbot VPS Setup

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Setup firewall
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw allow 12000 # Dashboard
sudo ufw --force enable

# Deploy tipbot
git clone https://github.com/your-username/community-tipbot.git
cd community-tipbot
cp config/config.example.json config/config.json

echo "✅ VPS setup complete!"
echo "📝 Edit config/config.json with your settings"
echo "🚀 Run: docker-compose up -d"
```

## ☁️ Cloud Platform Deployment

### AWS EC2
```bash
# Launch EC2 instance (t3.medium recommended)
# Security Group: Allow ports 22, 80, 443, 12000

# Connect via SSH
ssh -i your-key.pem ubuntu@your-ec2-ip

# Run VPS setup script
curl -sSL https://raw.githubusercontent.com/your-username/community-tipbot/main/scripts/vps-setup.sh | bash
```

### Google Cloud Platform
```bash
# Create Compute Engine instance
gcloud compute instances create tipbot-instance \
  --machine-type=e2-medium \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=20GB

# SSH and setup
gcloud compute ssh tipbot-instance
curl -sSL https://raw.githubusercontent.com/your-username/community-tipbot/main/scripts/vps-setup.sh | bash
```

### DigitalOcean
```bash
# Create droplet via web interface or API
# Choose Ubuntu 20.04, 4GB RAM, 2 CPUs

# SSH to droplet
ssh root@your-droplet-ip

# Run setup
curl -sSL https://raw.githubusercontent.com/your-username/community-tipbot/main/scripts/vps-setup.sh | bash
```

## 🔧 Production Configuration

### Environment Variables
```bash
# Create .env file
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
ADMIN_USER_ID=your_telegram_id
DATABASE_URL=sqlite:///data/tipbot.db
ENCRYPTION_KEY=your_encryption_key
ADMIN_PASSWORD=your_admin_password
EOF
```

### SSL/HTTPS Setup
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    location / {
        proxy_pass http://127.0.0.1:12000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Services
```bash
# Install as system service
sudo cp /tmp/community-tipbot.service /etc/systemd/system/
sudo cp /tmp/tipbot-dashboard.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable community-tipbot tipbot-dashboard
sudo systemctl start community-tipbot tipbot-dashboard

# Check status
sudo systemctl status community-tipbot
```

## 📊 Monitoring & Maintenance

### Log Monitoring
```bash
# View live logs
docker-compose logs -f tipbot

# Check log files
tail -f logs/bot.log
tail -f logs/dashboard.log

# Log rotation
sudo logrotate -f /etc/logrotate.d/tipbot
```

### Health Checks
```bash
# Check bot health
curl http://localhost:12000/health

# Check database
sqlite3 data/tipbot.db ".tables"

# Check wallet connections
./scripts/check_wallets.sh
```

### Backup Strategy
```bash
# Daily database backup
0 2 * * * /usr/bin/sqlite3 /app/data/tipbot.db ".backup /app/data/backups/tipbot-$(date +\%Y\%m\%d).db"

# Weekly full backup
0 3 * * 0 /usr/bin/tar -czf /app/data/backups/full-backup-$(date +\%Y\%m\%d).tar.gz /app/data /app/config

# Cleanup old backups
0 4 * * * /usr/bin/find /app/data/backups -name "*.db" -mtime +30 -delete
```

### Update Procedure
```bash
# Backup current installation
docker-compose exec tipbot tar -czf /app/data/backups/pre-update-backup.tar.gz /app/data

# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verify update
docker-compose logs -f tipbot
```

## 🔒 Security Hardening

### Server Security
```bash
# Disable root login
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Change SSH port
sudo sed -i 's/#Port 22/Port 2222/' /etc/ssh/sshd_config

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Setup automatic updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Application Security
```bash
# Strong passwords
openssl rand -base64 32  # Generate strong password

# File permissions
chmod 600 config/config.json
chmod 700 data/
chmod 755 scripts/*.sh

# Regular security updates
docker-compose pull
docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Starting
```bash
# Check logs
docker-compose logs tipbot

# Check configuration
python3 -c "import json; print(json.load(open('config/config.json')))"

# Restart services
docker-compose restart
```

#### Wallet Connection Issues
```bash
# Check wallet status
docker-compose exec tipbot ./scripts/check_wallets.sh

# Restart wallet daemons
docker-compose exec tipbot ./scripts/restart_wallets.sh

# Check RPC connectivity
docker-compose exec tipbot curl -u user:pass http://localhost:8332
```

#### Database Errors
```bash
# Check database integrity
sqlite3 data/tipbot.db "PRAGMA integrity_check;"

# Backup and recreate
cp data/tipbot.db data/tipbot.db.backup
rm data/tipbot.db
docker-compose restart tipbot
```

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Restart services
docker-compose restart

# Check for memory leaks
docker-compose exec tipbot ps aux
```

### Performance Optimization
```bash
# Database optimization
sqlite3 data/tipbot.db "VACUUM;"
sqlite3 data/tipbot.db "ANALYZE;"

# Log cleanup
find logs/ -name "*.log" -mtime +7 -delete

# Docker cleanup
docker system prune -f
```

## 📞 Support

### Getting Help
- **Documentation:** Read all .md files
- **Issues:** GitHub Issues page
- **Community:** Telegram group
- **Email:** support@aegisum.com

### Reporting Issues
1. Check logs for errors
2. Provide configuration (remove sensitive data)
3. Include steps to reproduce
4. Mention your environment details

---
*Powered By Aegisum EcoSystem*