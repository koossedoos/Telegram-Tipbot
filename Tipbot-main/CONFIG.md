# Community Tipbot Configuration Guide

## 📋 Configuration Overview

The Community Tipbot uses a JSON configuration file located at `config/config.json`. This file contains all the settings needed to run your tipbot.

## 🚀 Quick Configuration

Use the configuration helper script:

```bash
python3 configure_bot.py
```

This interactive script will guide you through the essential settings.

## 📝 Manual Configuration

### 1. Copy Example Configuration

```bash
cp config/config.example.json config/config.json
```

### 2. Edit Configuration File

Open `config/config.json` in your favorite text editor and configure the following sections:

## 🤖 Bot Configuration

```json
{
  "bot": {
    "token": "YOUR_BOT_TOKEN_HERE",
    "admin_users": [123456789],
    "allowed_groups": [],
    "cooldown_seconds": 30,
    "max_tip_amount": 1000000,
    "min_tip_amount": 0.01
  }
}
```

### Bot Settings Explained:

- **token**: Your Telegram bot token from [@BotFather](https://t.me/BotFather)
- **admin_users**: Array of Telegram user IDs who have admin access
- **allowed_groups**: Array of group chat IDs where bot can operate (empty = all groups)
- **cooldown_seconds**: Minimum time between commands per user
- **max_tip_amount**: Maximum amount that can be tipped in a single transaction
- **min_tip_amount**: Minimum amount that can be tipped

### Getting Your Bot Token:

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot`
3. Choose a name and username for your bot
4. Copy the token provided

### Finding Your User ID:

1. Message [@userinfobot](https://t.me/userinfobot) on Telegram
2. Your user ID will be displayed

## 💰 Coin Configuration

```json
{
  "coins": {
    "AEGS": {
      "name": "Aegisum",
      "enabled": true,
      "cli_path": "/usr/local/bin/aegisum-cli",
      "rpc_host": "127.0.0.1",
      "rpc_port": 8332,
      "rpc_user": "aegisumrpc",
      "rpc_password": "your_rpc_password",
      "decimals": 8,
      "withdrawal_fee": 0.001,
      "network_fee": 0.0001,
      "min_confirmations": 3,
      "explorer_url": "https://explorer.aegisum.com/tx/"
    }
  }
}
```

### Coin Settings Explained:

- **name**: Full name of the cryptocurrency
- **enabled**: Whether this coin is active in the bot
- **cli_path**: Path to the coin's CLI executable
- **rpc_host**: RPC server host (usually localhost)
- **rpc_port**: RPC server port
- **rpc_user**: RPC username
- **rpc_password**: RPC password (generate a strong one)
- **decimals**: Number of decimal places for the coin
- **withdrawal_fee**: Fee charged by the bot for withdrawals
- **network_fee**: Network transaction fee
- **min_confirmations**: Required confirmations for deposits
- **explorer_url**: Block explorer URL for transaction links

### Supported Coins:

The bot comes pre-configured for:
- **AEGS** (Aegisum) - Port 8332
- **SHIC** (ShibaCoin) - Port 8333
- **PEPE** (PepeCoin) - Port 8334
- **ADVC** (AdvCoin) - Port 8335

## 🎛️ Feature Configuration

```json
{
  "features": {
    "tips": true,
    "rain": true,
    "airdrops": true,
    "withdrawals": true,
    "deposits": true,
    "backup": true,
    "multi_coin": true
  }
}
```

### Feature Settings:

- **tips**: Enable/disable tipping functionality
- **rain**: Enable/disable rain (distribute to active users)
- **airdrops**: Enable/disable airdrop functionality
- **withdrawals**: Enable/disable withdrawals to external addresses
- **deposits**: Enable/disable deposit functionality
- **backup**: Enable/disable wallet backup feature
- **multi_coin**: Enable/disable multi-coin support

## 🌧️ Rain Configuration

```json
{
  "rain": {
    "min_active_users": 3,
    "activity_window_minutes": 60,
    "min_amount": 1.0,
    "max_recipients": 50
  }
}
```

### Rain Settings:

- **min_active_users**: Minimum users needed for rain
- **activity_window_minutes**: Time window to consider users active
- **min_amount**: Minimum amount for rain
- **max_recipients**: Maximum number of rain recipients

## 🎁 Airdrop Configuration

```json
{
  "airdrops": {
    "max_duration_minutes": 60,
    "min_amount": 10.0,
    "max_participants": 100
  }
}
```

### Airdrop Settings:

- **max_duration_minutes**: Maximum airdrop duration
- **min_amount**: Minimum amount for airdrops
- **max_participants**: Maximum airdrop participants

## 🔐 Security Configuration

```json
{
  "security": {
    "encryption_key": "GENERATE_RANDOM_KEY_HERE",
    "wallet_backup_encryption": true,
    "require_confirmation": true,
    "max_daily_withdrawal": 10000
  }
}
```

### Security Settings:

- **encryption_key**: Key for encrypting sensitive data (auto-generated)
- **wallet_backup_encryption**: Encrypt wallet backups
- **require_confirmation**: Require confirmation for large transactions
- **max_daily_withdrawal**: Maximum daily withdrawal per user

## 🖥️ Admin Dashboard Configuration

```json
{
  "admin_dashboard": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 12000,
    "password": "your_admin_password",
    "session_timeout": 3600
  }
}
```

### Dashboard Settings:

- **enabled**: Enable/disable admin dashboard
- **host**: Dashboard host (0.0.0.0 for all interfaces)
- **port**: Dashboard port
- **password**: Admin login password
- **session_timeout**: Session timeout in seconds

## 📊 Database Configuration

```json
{
  "database": {
    "path": "data/tipbot.db",
    "backup_interval_hours": 24,
    "max_backups": 7
  }
}
```

### Database Settings:

- **path**: SQLite database file path
- **backup_interval_hours**: Automatic backup interval
- **max_backups**: Maximum number of backups to keep

## 📝 Logging Configuration

```json
{
  "logging": {
    "level": "INFO",
    "file": "logs/bot.log",
    "max_size_mb": 10,
    "backup_count": 5
  }
}
```

### Logging Settings:

- **level**: Log level (DEBUG, INFO, WARNING, ERROR)
- **file**: Log file path
- **max_size_mb**: Maximum log file size
- **backup_count**: Number of log files to keep

## 🔧 Advanced Configuration

### Environment Variables

You can override configuration values using environment variables:

```bash
export TIPBOT_BOT_TOKEN="your_bot_token"
export TIPBOT_ADMIN_PASSWORD="your_admin_password"
export TIPBOT_AEGS_RPC_PASSWORD="aegs_rpc_password"
```

### Configuration Validation

The bot validates configuration on startup. Common issues:

1. **Invalid bot token**: Check token format
2. **RPC connection failed**: Verify wallet daemon is running
3. **Invalid user IDs**: Ensure admin_users contains valid Telegram user IDs
4. **Port conflicts**: Ensure ports are not in use by other services

### Testing Configuration

Test your configuration:

```bash
# Test bot connection
python3 -c "
import sys
sys.path.append('src')
from bot import CommunityTipBot
bot = CommunityTipBot()
print('Configuration loaded successfully!')
"

# Test wallet connections
python3 -c "
import sys
sys.path.append('src')
from wallet_manager import WalletManager
import asyncio

async def test():
    wm = WalletManager('config/config.json')
    for coin in ['AEGS', 'SHIC', 'PEPE', 'ADVC']:
        try:
            info = await wm.get_wallet_info(coin)
            print(f'{coin}: Connected ✅')
        except Exception as e:
            print(f'{coin}: Failed ❌ - {e}')

asyncio.run(test())
"
```

## 🚨 Security Best Practices

1. **Use strong RPC passwords** (32+ characters)
2. **Restrict RPC access** to localhost only
3. **Regular backups** of wallets and database
4. **Monitor logs** for suspicious activity
5. **Update regularly** to get security fixes
6. **Use HTTPS** for admin dashboard in production
7. **Firewall configuration** to restrict access

## 🔄 Configuration Updates

When updating configuration:

1. **Stop the bot**: `./manage_bot.sh stop`
2. **Edit configuration**: `nano config/config.json`
3. **Validate changes**: Run test commands above
4. **Restart bot**: `./manage_bot.sh start`

## 📞 Support

If you need help with configuration:

1. Check the logs: `./manage_bot.sh logs`
2. Verify wallet status: `~/wallets/wallet_info.sh`
3. Test individual components
4. Join the Aegisum community for support

---
*Powered By Aegisum EcoSystem*