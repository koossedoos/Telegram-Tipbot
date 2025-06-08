# Community Tipbot - Aegisum Ecosystem

A comprehensive Telegram wallet and tip bot supporting multiple cryptocurrencies including AEGS, SHIC, PEPE, and ADVC.

## Features

- 🔐 Non-custodial wallet management
- 💸 Multi-coin tipping system
- 🌧️ Rain and airdrop functionality
- 📊 Community engagement tools
- 🛡️ Admin controls and toggles
- 📱 Real-time transaction notifications
- 💾 Secure backup and restore

## Supported Coins

- **AEGS (Aegisum)** - CLI: `aegisum-cli`
- **SHIC (ShibaCoin)** - CLI: `shibacoin-cli`
- **PEPE (PepeCoin)** - CLI: `pepecoin-cli`
- **ADVC (AdvCoin)** - CLI: `advc-cli`

## Installation

See [INSTALL.md](INSTALL.md) for detailed setup instructions.

## Configuration

See [CONFIG.md](CONFIG.md) for configuration options.

## Commands

### User Commands
- `/start` - Create wallet or restore with key
- `/balance` - View per-coin balances
- `/deposit` - Get your deposit address
- `/withdraw coin amount address` - Withdraw to wallet
- `/tip @user coin amount` - Send tip
- `/rain coin amount` - Distribute evenly to recent active users
- `/airdrop coin amount time_minutes` - Users click "Join Airdrop"
- `/claimtips` - Claim tips received while offline
- `/history` - See your recent transactions
- `/backup` - Export encrypted wallet/private key
- `/help` - Show command list

### Community Tools
- `/top` - Show top tippers, earners, and rain receivers
- `/donate coin amount` - Donate to community funding
- `/fees` - Show current estimated fees

### Admin Commands
- `/setgroups` - Allow specific group IDs
- `/setcooldown 30` - Anti-spam cooldown
- `/disable feature` - Disable features
- `/enable feature` - Enable features
- `/addcoin` - Add new coin support
- `/setfees` - Update fees
- `/stats` - View global statistics

---
*Powered By Aegisum EcoSystem*