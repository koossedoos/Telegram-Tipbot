# 🤖 Enhanced Community Tipbot

**Professional Multi-Coin Telegram Tipbot with Advanced Security Features**

*Powered By Aegisum EcoSystem* ⚡

## 🌟 Features Overview

### 🔐 **Enhanced Security & Privacy**
- **Password-Protected Wallets**: Strong password requirements with encryption
- **24-Word Seed Phrases**: BIP39 mnemonic generation for wallet recovery
- **Two-Factor Authentication**: TOTP-based 2FA for withdrawals and sensitive operations
- **Non-Custodial Design**: Users control their own private keys
- **Withdrawal Limits**: Daily limits with cooling periods
- **Suspicious Activity Detection**: Automated monitoring and alerts
- **IP-Based Security**: Track and monitor user activities
- **DM-Only Sensitive Commands**: Force sensitive operations to private messages

### 💰 **Multi-Coin Support**
- **AEGS (Aegisum)**: 3-minute blocks, fast confirmations
- **SHIC (ShibaCoin)**: Community favorite meme coin
- **PEPE (PepeCoin)**: Meme power with real utility
- **ADVC (AdventureCoin)**: Adventure awaits with rewards

### 🎮 **Community Features**
- **Advanced Tipping System**: Send tips with messages and privacy options
- **Rain Events**: Distribute coins to active community members
- **Airdrops**: Time-limited community rewards
- **Daily Faucet**: Free coins with anti-abuse protection
- **Dice Games**: Gambling with configurable odds and limits
- **Leaderboards**: Top tippers, rain masters, and active users
- **Community Challenges**: Weekly/monthly challenges with rewards
- **Referral System**: Earn rewards for bringing new users

### 🎯 **Advanced Wallet Features**
- **Scheduled Tips**: Set up recurring or delayed tips
- **Tip Splitting**: Send tips to multiple users at once
- **Tip Templates**: Save common tip messages and amounts
- **Portfolio Tracking**: Real-time balance monitoring
- **Transaction History**: Detailed history with search and filters
- **QR Code Generation**: Easy deposit address sharing
- **Address Labels**: Organize multiple addresses per coin

### 👑 **Admin Dashboard**
- **Real-Time Monitoring**: Live system health and statistics
- **User Management**: Search, filter, freeze/unfreeze accounts
- **Transaction Oversight**: Monitor all transactions with approval system
- **Wallet Status**: Real-time wallet connection monitoring
- **Security Logs**: Comprehensive security event tracking
- **Analytics**: User growth, transaction volume, popular commands
- **System Controls**: Backup creation, settings management
- **Performance Metrics**: Response times, error rates, uptime

### 🛡️ **Security Enhancements**
- **Encrypted Seed Storage**: Military-grade encryption for seed phrases
- **Password Strength Validation**: Enforce strong password policies
- **Session Management**: Secure session handling with timeouts
- **Rate Limiting**: Prevent abuse with intelligent rate limiting
- **Backup Reminders**: Automated reminders for wallet backups
- **Recovery System**: Secure wallet recovery with seed phrases
- **Audit Trails**: Complete audit logs for all operations

## 🚀 Quick Start

### 1. **Prerequisites**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv git

# Install wallet daemons (AEGS, SHIC, PEPE, ADVC)
# Follow individual coin installation guides
```

### 2. **Clone and Setup**
```bash
git clone https://github.com/mikekoosssss/Tipbot.git
cd Tipbot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install enhanced requirements
pip install -r requirements_enhanced.txt
```

### 3. **Configuration**
```bash
# Copy and edit configuration
cp config/enhanced_config.json.example config/enhanced_config.json
nano config/enhanced_config.json
```

**Required Configuration:**
```json
{
  "bot": {
    "token": "YOUR_TELEGRAM_BOT_TOKEN",
    "admin_users": [YOUR_TELEGRAM_USER_ID]
  },
  "coins": {
    "AEGS": {
      "rpc_user": "your_rpc_username",
      "rpc_password": "your_rpc_password",
      "rpc_port": 8332
    }
    // ... configure all coins
  }
}
```

### 4. **Start the Enhanced Bot**
```bash
# Using the enhanced startup script
python3 start_enhanced_bot.py

# Or manually
python3 src/enhanced_bot.py
```

### 5. **Start Admin Dashboard**
```bash
# In a separate terminal
cd admin_dashboard
python3 enhanced_app.py
```

Access dashboard at: `http://localhost:12000`

## 📱 User Commands

### 🔐 **Wallet Management**
- `/start` - Create or import wallet with seed phrase
- `/balance` - View portfolio with real-time balances
- `/deposit` - Get deposit addresses (DM only)
- `/withdraw <coin> <amount> <address>` - Withdraw with 2FA
- `/backup` - Export encrypted wallet backup
- `/seed` - View seed phrase (password + 2FA required)
- `/history` - Transaction history with filters

### 🎁 **Tipping & Rewards**
- `/tip @user <coin> <amount> [message]` - Send tips
- `/rain <coin> <amount> [duration]` - Rain to active users
- `/airdrop <coin> <amount> <duration>` - Create airdrops
- `/faucet` - Claim daily free coins
- `/claimtips` - Claim pending tips

### 🎮 **Games & Community**
- `/dice <coin> <amount>` - Play dice game
- `/top` - View leaderboards
- `/stats` - Personal statistics
- `/challenges` - View active challenges
- `/referral` - Get referral link

### ⚙️ **Settings & Privacy**
- `/settings` - Privacy and notification settings
- `/privacy` - Toggle private balance mode
- `/notifications` - Configure notifications
- `/2fa` - Setup two-factor authentication

## 🛠️ Admin Commands

### 👥 **User Management**
- `/admin users` - List all users with filters
- `/admin user <id>` - View user details
- `/admin freeze <id>` - Freeze user account
- `/admin unfreeze <id>` - Unfreeze user account
- `/admin balance <id> <coin> <amount>` - Adjust balance

### 💰 **Financial Controls**
- `/admin withdrawals` - Pending withdrawal approvals
- `/admin approve <id>` - Approve withdrawal
- `/admin reject <id>` - Reject withdrawal
- `/admin limits <id> <amount>` - Set withdrawal limits

### 🔧 **System Management**
- `/admin backup` - Create system backup
- `/admin stats` - System statistics
- `/admin health` - System health check
- `/admin reload` - Reload configuration
- `/admin maintenance` - Toggle maintenance mode

## 🔧 Advanced Configuration

### 🔐 **Security Settings**
```json
{
  "security": {
    "password_min_length": 8,
    "require_2fa_for_withdrawals": true,
    "withdrawal_cooling_period": 300,
    "max_failed_attempts": 5,
    "account_lockout_duration": 3600
  }
}
```

### 🎮 **Game Configuration**
```json
{
  "dice": {
    "min_bet": 0.1,
    "max_bet": 100.0,
    "payout_table": {
      "1": 0, "2": 0, "3": 1, "4": 1, "5": 2, "6": 3
    }
  },
  "faucet": {
    "cooldown_hours": 24,
    "rewards": {
      "AEGS": 0.1,
      "SHIC": 10.0
    }
  }
}
```

### 🌧️ **Rain & Airdrop Settings**
```json
{
  "rain": {
    "min_amount": 1.0,
    "max_recipients": 50,
    "participation_window": 300
  },
  "airdrops": {
    "min_amount": 10.0,
    "max_duration": 3600,
    "max_participants": 100
  }
}
```

## 📊 Monitoring & Analytics

### 📈 **Dashboard Features**
- **Real-time Statistics**: Users, transactions, balances
- **Performance Metrics**: Response times, error rates
- **Security Monitoring**: Failed logins, suspicious activities
- **Wallet Health**: Connection status, block heights
- **User Analytics**: Growth charts, activity patterns

### 🔍 **Logging & Auditing**
- **Transaction Logs**: All financial operations
- **Security Events**: Login attempts, 2FA usage
- **Admin Actions**: All administrative operations
- **Error Tracking**: System errors and exceptions
- **Performance Logs**: Response times and bottlenecks

## 🔒 Security Best Practices

### 🛡️ **For Administrators**
1. **Use Strong Passwords**: Minimum 12 characters with mixed case, numbers, symbols
2. **Enable 2FA**: Always use two-factor authentication
3. **Regular Backups**: Automated daily backups with encryption
4. **Monitor Logs**: Review security logs regularly
5. **Update Regularly**: Keep all components updated
6. **Secure Server**: Use firewall, fail2ban, and secure SSH

### 👤 **For Users**
1. **Strong Wallet Password**: Use unique, strong passwords
2. **Backup Seed Phrase**: Store 24-word seed phrase securely offline
3. **Enable 2FA**: Use authenticator app for withdrawals
4. **Verify Addresses**: Always double-check withdrawal addresses
5. **Use DMs**: Perform sensitive operations in private messages
6. **Regular Backups**: Export wallet backups regularly

## 🚨 Troubleshooting

### ❌ **Common Issues**

**Bot Not Starting:**
```bash
# Check configuration
python3 -c "import json; json.load(open('config/enhanced_config.json'))"

# Check wallet connections
aegisum-cli getblockchaininfo
shibacoin-cli getblockchaininfo
```

**Wallet Connection Errors:**
```bash
# Check RPC credentials
grep rpc config/enhanced_config.json

# Test CLI access
aegisum-cli -rpcuser=user -rpcpassword=pass getinfo
```

**Database Issues:**
```bash
# Check database permissions
ls -la data/
sqlite3 data/enhanced_tipbot.db ".tables"
```

### 🔧 **Performance Optimization**

**Database Optimization:**
```sql
-- Run these commands in SQLite
VACUUM;
REINDEX;
ANALYZE;
```

**Memory Usage:**
```bash
# Monitor memory usage
ps aux | grep python
htop
```

## 📞 Support & Community

### 🆘 **Getting Help**
- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Comprehensive guides and tutorials
- **Community Chat**: Join our Telegram support group
- **Email Support**: Direct support for critical issues

### 🤝 **Contributing**
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request
5. Follow code review process

### 📜 **License**
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🎯 **What Makes This Special**

### 🔥 **Professional Grade**
- **Enterprise Security**: Military-grade encryption and security practices
- **Scalable Architecture**: Handles thousands of users efficiently
- **Comprehensive Monitoring**: Real-time insights and analytics
- **Automated Operations**: Self-healing and maintenance features

### 🚀 **User Experience**
- **Intuitive Interface**: Easy-to-use commands and responses
- **Rich Interactions**: Inline keyboards and interactive elements
- **Privacy Focused**: User privacy and security first
- **Community Driven**: Features designed for community engagement

### 💎 **Technical Excellence**
- **Modern Python**: Async/await, type hints, best practices
- **Robust Error Handling**: Graceful error recovery
- **Comprehensive Testing**: Unit tests and integration tests
- **Documentation**: Detailed documentation and examples

---

**Powered By Aegisum EcoSystem** ⚡

*Building the future of decentralized community engagement*