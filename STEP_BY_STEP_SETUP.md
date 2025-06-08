# Step-by-Step Setup Guide for Ubuntu Server

## 🚀 Complete Setup Instructions

This guide will help you:
1. Clean up unnecessary wallet cores
2. Pull the optimized tipbot from GitHub
3. Install and configure everything
4. Set up your bot token
5. Start the tipbot

## Step 1: Clean Up Your Ubuntu Server

### 🧹 Remove Unnecessary Wallet Cores

**IMPORTANT: Backup any important wallet.dat files first!**

```bash
# 1. Check what's currently installed
ls -la /usr/local/bin/ | grep -E "(bitcoin|litecoin|dash|viacoin|dogecoin|monero)"

# 2. Stop all unnecessary services
sudo systemctl stop bitcoind litecoind dashd viacoind dogecoind monerod 2>/dev/null || true
sudo systemctl disable bitcoind litecoind dashd viacoind dogecoind monerod 2>/dev/null || true

# 3. Remove service files
sudo rm -f /etc/systemd/system/{bitcoin,litecoin,dash,viacoin,dogecoin,monero}*.service

# 4. Remove binaries
sudo rm -f /usr/local/bin/{bitcoin,litecoin,dash,viacoin,dogecoin,monero}*

# 5. Remove data directories (BACKUP FIRST!)
# Only run this after backing up any important wallets!
rm -rf ~/.bitcoin ~/.litecoin ~/.dashcore ~/.viacoin ~/.dogecoin ~/.monero

# 6. Reload systemd
sudo systemctl daemon-reload

echo "✅ Cleanup completed!"
```

### 🔍 Verify Only Your 4 Coins Remain

```bash
# Check what wallet binaries are left
ls -la /usr/local/bin/ | grep -E "(aegisum|advc|shibacoin|pepecoin)"

# Check what data directories exist
ls -la ~/ | grep -E "\.(aegisum|advc|shibacoin|pepecoin)"
```

## Step 2: Pull Optimized Tipbot from GitHub

```bash
# 1. Navigate to your home directory
cd ~

# 2. Clone the updated repository
git clone https://github.com/koossedoos/Telegram-Tipbot.git

# 3. Navigate to the optimized tipbot
cd Telegram-Tipbot/optimized-multi-coin-tipbot

# 4. Check the contents
ls -la
```

## Step 3: Install Dependencies

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python and pip (if not already installed)
sudo apt install python3 python3-pip python3-venv -y

# 3. Create virtual environment
python3 -m venv venv

# 4. Activate virtual environment
source venv/bin/activate

# 5. Install Python dependencies
pip install -r requirements.txt
```

## Step 4: Configure Your Bot

### 🤖 Create Telegram Bot

1. **Message @BotFather on Telegram**
2. **Send:** `/newbot`
3. **Choose a name:** `Your Multi-Coin Tipbot`
4. **Choose a username:** `your_tipbot` (must end with 'bot')
5. **Copy the token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### ⚙️ Configure the Bot

```bash
# 1. Copy example config
cp config/config.example.json config/config.json

# 2. Edit configuration
nano config/config.json
```

**Edit these important fields:**

```json
{
  "bot": {
    "token": "YOUR_TELEGRAM_BOT_TOKEN_HERE",  // ← Put your bot token here
    "admin_users": [YOUR_TELEGRAM_USER_ID],   // ← Put your Telegram user ID
  },
  "coins": {
    "AEGS": {
      "rpc_password": "YOUR_AEGISUM_RPC_PASSWORD"  // ← Update with actual password
    },
    "ADVC": {
      "rpc_password": "YOUR_ADVC_RPC_PASSWORD"     // ← Update with actual password
    },
    "SHIC": {
      "rpc_password": "YOUR_SHIC_RPC_PASSWORD"     // ← Update with actual password
    },
    "PEPE": {
      "rpc_password": "YOUR_PEPE_RPC_PASSWORD"     // ← Update with actual password
    }
  }
}
```

### 🔑 Get Your Telegram User ID

Send a message to @userinfobot on Telegram to get your user ID.

## Step 5: Install Wallet Cores

```bash
# 1. Run the wallet installation script
./scripts/install_wallets.sh

# 2. This will create configurations and show you the RPC passwords
# Copy these passwords to your config.json file

# 3. Download your wallet binaries manually and copy to /usr/local/bin/
# You need to get these from your coin developers:
# - aegisumd, aegisum-cli
# - advcd, advc-cli  
# - shibacoind, shibacoin-cli
# - pepecoind, pepecoin-cli

# 4. Make binaries executable
sudo chmod +x /usr/local/bin/{aegisumd,aegisum-cli,advcd,advc-cli,shibacoind,shibacoin-cli,pepecoind,pepecoin-cli}
```

## Step 6: Start Wallet Daemons

```bash
# 1. Start all wallet daemons
~/wallets/manage_wallets.sh start

# 2. Check status
~/wallets/manage_wallets.sh status

# 3. Monitor synchronization
~/wallets/manage_wallets.sh sync
```

## Step 7: Start the Tipbot

```bash
# 1. Make sure you're in the tipbot directory with venv activated
cd ~/Telegram-Tipbot/optimized-multi-coin-tipbot
source venv/bin/activate

# 2. Start the bot
python start_bot.py
```

## Step 8: Test Your Bot

1. **Find your bot on Telegram** using the username you created
2. **Send:** `/start`
3. **Test commands:**
   - `/help` - Show all commands
   - `/balance AEGS` - Check balance
   - `/faucet AEGS` - Get free coins
   - `/deposit AEGS` - Get deposit address

## 🔧 Troubleshooting

### If wallet daemons won't start:
```bash
# Check logs
tail -f ~/.aegisum/debug.log
tail -f ~/.advc/debug.log
tail -f ~/.shibacoin/debug.log
tail -f ~/.pepecoin/debug.log
```

### If bot won't start:
```bash
# Check bot logs
tail -f data/bot.log

# Verify configuration
python -c "import json; print(json.load(open('config/config.json')))"
```

### If RPC connection fails:
```bash
# Test RPC connection
aegisum-cli getblockchaininfo
advc-cli getblockchaininfo
shibacoin-cli getblockchaininfo
pepecoin-cli getblockchaininfo
```

## 🎯 Quick Commands Reference

```bash
# Wallet management
~/wallets/manage_wallets.sh start     # Start all wallets
~/wallets/manage_wallets.sh stop      # Stop all wallets
~/wallets/manage_wallets.sh status    # Check status
~/wallets/manage_wallets.sh backup    # Backup wallets

# Bot management
cd ~/Telegram-Tipbot/optimized-multi-coin-tipbot
source venv/bin/activate
python start_bot.py                   # Start bot

# Monitor resources
htop                                   # CPU/RAM usage
df -h                                  # Disk space
~/wallets/monitor_wallets.sh          # Wallet status
```

## 🛡️ Security Setup

```bash
# 1. Set up firewall
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8332:8336/tcp  # RPC ports
sudo ufw allow 12000/tcp      # Admin dashboard

# 2. Secure file permissions
chmod 600 config/config.json
chmod 600 ~/wallets/rpc_passwords.txt
chmod 700 ~/.aegisum ~/.advc ~/.shibacoin ~/.pepecoin
```

## 🎉 You're Done!

Your optimized multi-coin tipbot is now running with only your 4 coins:
- ✅ **AEGS** (Aegisum)
- ✅ **ADVC** (AdventureCoin)  
- ✅ **SHIC** (ShibaCoin)
- ✅ **PEPE** (PepeCoin)

**Powered By Aegisum EcoSystem** 🚀