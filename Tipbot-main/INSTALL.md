# Community Tipbot Installation Guide

This guide will help you install and configure the Community Tipbot on a headless Ubuntu server.

## Prerequisites

- Ubuntu 20.04+ server with root access
- At least 2GB RAM and 20GB storage
- Python 3.8+
- Telegram Bot Token (from @BotFather)
- Cryptocurrency wallets/daemons for supported coins

## Step 1: System Preparation

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
sudo apt install -y python3 python3-pip python3-venv git curl wget build-essential
```

### Create Bot User
```bash
sudo useradd -m -s /bin/bash tipbot
sudo usermod -aG sudo tipbot
sudo su - tipbot
```

## Step 2: Download and Setup Bot

### Clone Repository
```bash
cd /home/tipbot
git clone https://github.com/your-username/community-tipbot.git
cd community-tipbot
```

### Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 3: Install Cryptocurrency Wallets

### AEGS (Aegisum)
```bash
# Download Aegisum wallet
wget https://github.com/aegisum/aegisum/releases/download/v1.0.0/aegisum-1.0.0-x86_64-linux-gnu.tar.gz
tar -xzf aegisum-1.0.0-x86_64-linux-gnu.tar.gz
sudo cp aegisum-1.0.0/bin/* /usr/local/bin/
```

### SHIC (ShibaCoin)
```bash
# Download ShibaCoin wallet
wget https://github.com/shibacoin/shibacoin/releases/download/v1.0.0/shibacoin-1.0.0-x86_64-linux-gnu.tar.gz
tar -xzf shibacoin-1.0.0-x86_64-linux-gnu.tar.gz
sudo cp shibacoin-1.0.0/bin/* /usr/local/bin/
```

### PEPE (PepeCoin)
```bash
# Download PepeCoin wallet
wget https://github.com/pepecoin/pepecoin/releases/download/v1.0.0/pepecoin-1.0.0-x86_64-linux-gnu.tar.gz
tar -xzf pepecoin-1.0.0-x86_64-linux-gnu.tar.gz
sudo cp pepecoin-1.0.0/bin/* /usr/local/bin/
```

### ADVC (AdvCoin)
```bash
# Download AdvCoin wallet
wget https://github.com/advcoin/advcoin/releases/download/v1.0.0/advc-1.0.0-x86_64-linux-gnu.tar.gz
tar -xzf advc-1.0.0-x86_64-linux-gnu.tar.gz
sudo cp advc-1.0.0/bin/* /usr/local/bin/
```

## Step 4: Configure Wallets

### Create Wallet Directories
```bash
mkdir -p ~/.aegisum ~/.shibacoin ~/.pepecoin ~/.advc
```

### AEGS Configuration
Create `~/.aegisum/aegisum.conf`:
```ini
rpcuser=aegisumrpc
rpcpassword=your_secure_password_here
rpcallowip=127.0.0.1
rpcport=8332
server=1
daemon=1
txindex=1
```

### SHIC Configuration
Create `~/.shibacoin/shibacoin.conf`:
```ini
rpcuser=shibacoirpc
rpcpassword=your_secure_password_here
rpcallowip=127.0.0.1
rpcport=8333
server=1
daemon=1
txindex=1
```

### PEPE Configuration
Create `~/.pepecoin/pepecoin.conf`:
```ini
rpcuser=pepecoirpc
rpcpassword=your_secure_password_here
rpcallowip=127.0.0.1
rpcport=8334
server=1
daemon=1
txindex=1
```

### ADVC Configuration
Create `~/.advc/advc.conf`:
```ini
rpcuser=advcrpc
rpcpassword=your_secure_password_here
rpcallowip=127.0.0.1
rpcport=8335
server=1
daemon=1
txindex=1
```

## Step 5: Start Wallet Daemons

### Start All Daemons
```bash
aegisumd -daemon
shibacoind -daemon
pepecoind -daemon
advcd -daemon
```

### Wait for Synchronization
```bash
# Check sync status for each coin
aegisum-cli getblockchaininfo
shibacoin-cli getblockchaininfo
pepecoin-cli getblockchaininfo
advc-cli getblockchaininfo
```

## Step 6: Configure Bot

### Edit Configuration
```bash
cd /home/tipbot/community-tipbot
cp config/config.json config/config.json.backup
nano config/config.json
```

### Update Required Settings
1. **Bot Token**: Replace `YOUR_BOT_TOKEN_HERE` with your Telegram bot token
2. **Admin Users**: Add your Telegram user ID to the admin_users array
3. **RPC Passwords**: Update all RPC passwords to match your wallet configurations
4. **Encryption Key**: Generate a secure encryption key

### Generate Encryption Key
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Step 7: Create Systemd Services

### Bot Service
Create `/etc/systemd/system/community-tipbot.service`:
```ini
[Unit]
Description=Community Tipbot
After=network.target

[Service]
Type=simple
User=tipbot
WorkingDirectory=/home/tipbot/community-tipbot
Environment=PATH=/home/tipbot/community-tipbot/venv/bin
ExecStart=/home/tipbot/community-tipbot/venv/bin/python src/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Admin Dashboard Service
Create `/etc/systemd/system/tipbot-dashboard.service`:
```ini
[Unit]
Description=Community Tipbot Admin Dashboard
After=network.target

[Service]
Type=simple
User=tipbot
WorkingDirectory=/home/tipbot/community-tipbot/admin_dashboard
Environment=PATH=/home/tipbot/community-tipbot/venv/bin
ExecStart=/home/tipbot/community-tipbot/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Wallet Services
Create services for each wallet daemon:

`/etc/systemd/system/aegisumd.service`:
```ini
[Unit]
Description=Aegisum Daemon
After=network.target

[Service]
Type=forking
User=tipbot
ExecStart=/usr/local/bin/aegisumd -daemon
ExecStop=/usr/local/bin/aegisum-cli stop
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Repeat for other coins (shibacoin, pepecoin, advc).

## Step 8: Start Services

### Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable aegisumd shibacoind pepecoind advcd
sudo systemctl enable community-tipbot tipbot-dashboard

sudo systemctl start aegisumd shibacoind pepecoind advcd
sudo systemctl start community-tipbot tipbot-dashboard
```

### Check Service Status
```bash
sudo systemctl status community-tipbot
sudo systemctl status tipbot-dashboard
sudo systemctl status aegisumd
```

## Step 9: Configure Firewall

### UFW Setup
```bash
sudo ufw allow ssh
sudo ufw allow 12000  # Admin dashboard
sudo ufw enable
```

## Step 10: Test Installation

### Test Bot Commands
1. Start a chat with your bot on Telegram
2. Send `/start` command
3. Check if wallet addresses are generated
4. Test `/balance` command

### Test Admin Dashboard
1. Open browser to `http://your-server-ip:12000`
2. Login with admin credentials
3. Check dashboard statistics

### Test CLI Commands
```bash
# Test wallet connectivity
aegisum-cli getwalletinfo
shibacoin-cli getwalletinfo
pepecoin-cli getwalletinfo
advc-cli getwalletinfo
```

## Step 11: Backup Setup

### Create Backup Script
Create `/home/tipbot/backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/tipbot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /home/tipbot/community-tipbot/data/tipbot.db $BACKUP_DIR/tipbot_$DATE.db

# Backup config
cp /home/tipbot/community-tipbot/config/config.json $BACKUP_DIR/config_$DATE.json

# Backup wallet files
cp ~/.aegisum/wallet.dat $BACKUP_DIR/aegisum_wallet_$DATE.dat
cp ~/.shibacoin/wallet.dat $BACKUP_DIR/shibacoin_wallet_$DATE.dat
cp ~/.pepecoin/wallet.dat $BACKUP_DIR/pepecoin_wallet_$DATE.dat
cp ~/.advc/wallet.dat $BACKUP_DIR/advc_wallet_$DATE.dat

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.json" -mtime +7 -delete
find $BACKUP_DIR -name "*.dat" -mtime +7 -delete
```

### Setup Cron Job
```bash
chmod +x /home/tipbot/backup.sh
crontab -e
```

Add line:
```
0 2 * * * /home/tipbot/backup.sh
```

## Troubleshooting

### Check Logs
```bash
# Bot logs
sudo journalctl -u community-tipbot -f

# Dashboard logs
sudo journalctl -u tipbot-dashboard -f

# Wallet logs
tail -f ~/.aegisum/debug.log
```

### Common Issues

1. **Bot not responding**: Check if bot token is correct and bot is started
2. **Wallet connection failed**: Ensure daemons are running and synced
3. **Permission denied**: Check file permissions and user ownership
4. **Database errors**: Ensure database directory is writable

### Restart Services
```bash
sudo systemctl restart community-tipbot
sudo systemctl restart tipbot-dashboard
sudo systemctl restart aegisumd
```

## Security Recommendations

1. **Change default passwords** in config files
2. **Enable firewall** and close unnecessary ports
3. **Regular backups** of wallets and database
4. **Monitor logs** for suspicious activity
5. **Keep software updated**
6. **Use strong encryption keys**

## Support

For support and updates:
- GitHub: https://github.com/your-username/community-tipbot
- Telegram: @your-support-channel
- Website: https://aegisum.com

---
*Powered By Aegisum EcoSystem*