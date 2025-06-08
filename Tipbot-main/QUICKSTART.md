# Community Tipbot - Quick Start Guide

Get your Community Tipbot up and running in minutes!

## Prerequisites

- Ubuntu 20.04+ server
- Python 3.8+
- Telegram Bot Token from @BotFather
- Your Telegram User ID (get from @userinfobot)

## Quick Installation

### 1. Download and Setup
```bash
# Clone the repository
git clone https://github.com/your-username/community-tipbot.git
cd community-tipbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Bot
```bash
# Copy example configuration
cp config/config.example.json config/config.json

# Edit configuration
nano config/config.json
```

**Required Changes:**
- Replace `YOUR_BOT_TOKEN_HERE` with your bot token
- Replace `123456789` with your Telegram user ID
- Update RPC passwords for all coins

### 3. Install Wallets
```bash
# Run wallet installation script
chmod +x scripts/install_wallets.sh
./scripts/install_wallets.sh
```

### 4. Start Bot
```bash
# Start the bot
python3 start_bot.py
```

### 5. Test Bot
1. Open Telegram and find your bot
2. Send `/start` command
3. Check if wallet addresses are generated
4. Test with `/balance` command

## Admin Dashboard

Access the web dashboard at: `http://your-server-ip:12000`

Default credentials:
- Username: `admin`
- Password: `change_this_password` (change in config!)

## Basic Commands

### User Commands
- `/start` - Create wallet
- `/balance` - Check balances
- `/deposit` - Get deposit addresses
- `/tip @user AEGS 10` - Send tip
- `/rain AEGS 100` - Rain to active users
- `/withdraw AEGS 10 address` - Withdraw coins

### Admin Commands
- `/admin` - Admin panel
- `/stats` - View statistics
- `/disable tipping` - Disable features
- `/enable tipping` - Enable features

## Supported Coins

- **AEGS** (Aegisum) - Primary coin
- **SHIC** (ShibaCoin)
- **PEPE** (PepeCoin)
- **ADVC** (AdvCoin)

## Security Notes

1. **Change default passwords** in config
2. **Backup wallet files** regularly
3. **Use strong encryption keys**
4. **Monitor logs** for issues
5. **Keep software updated**

## Troubleshooting

### Bot not responding?
```bash
# Check bot logs
tail -f logs/bot.log

# Restart bot
python3 start_bot.py
```

### Wallet connection issues?
```bash
# Check wallet status
~/wallets/wallet_info.sh

# Restart wallets
~/wallets/manage_wallets.sh restart
```

### Database errors?
```bash
# Check database permissions
ls -la data/

# Recreate database
rm data/tipbot.db
python3 start_bot.py
```

## Getting Help

- Read the full [Installation Guide](INSTALL.md)
- Check [Configuration Guide](CONFIG.md)
- Visit [Aegisum Website](https://aegisum.com)
- Join our Telegram community

## Features

✅ **Multi-coin wallet**
✅ **Tip system**
✅ **Rain distribution**
✅ **Admin controls**
✅ **Transaction monitoring**
✅ **Web dashboard**
✅ **Backup/restore**
✅ **Real-time notifications**

## Next Steps

1. **Customize** bot settings in config
2. **Add more coins** if needed
3. **Setup monitoring** and alerts
4. **Create backups** regularly
5. **Invite users** to test

---
*Powered By Aegisum EcoSystem*