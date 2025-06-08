# Optimized Multi-Coin Tipbot for Aegisum, ADVC, SHIC, and PEPE

This is an optimized version of your Telegram tipbot, specifically configured for your four custom blockchains:
- **AEGS** (Aegisum)
- **ADVC** (AdventureCoin) 
- **SHIC** (ShibaCoin)
- **PEPE** (PepeCoin)

## Features

✅ **Multi-coin support** for your 4 custom blockchains  
✅ **Secure wallet management** with encryption  
✅ **Advanced tipping features** (rain, airdrops, dice games)  
✅ **Admin dashboard** with monitoring  
✅ **2FA security** for withdrawals  
✅ **Automatic backups** and recovery  
✅ **Transaction monitoring** and notifications  
✅ **Faucet system** for user onboarding  

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure your bot:**
   ```bash
   cp config/config.example.json config/config.json
   # Edit config.json with your settings
   ```

3. **Install wallet cores:**
   ```bash
   ./scripts/install_wallets.sh
   ```

4. **Start the bot:**
   ```bash
   python start_bot.py
   ```

## Node Requirements

For optimal performance on your Ubuntu server, you'll need:

### Minimum Requirements:
- **CPU:** 4 cores (2.0 GHz+)
- **RAM:** 8GB 
- **Storage:** 200GB SSD
- **Network:** 100 Mbps

### Recommended Requirements:
- **CPU:** 8 cores (3.0 GHz+)
- **RAM:** 16GB
- **Storage:** 500GB NVMe SSD
- **Network:** 1 Gbps

### Per-Blockchain Storage Estimates:
- **Aegisum:** ~50GB (estimated)
- **ADVC:** ~30GB (estimated)
- **SHIC:** ~40GB (estimated)
- **PEPE:** ~35GB (estimated)

## Security Features

- 🔐 **Encrypted wallet storage**
- 🔑 **2FA for withdrawals**
- 🛡️ **Rate limiting and cooldowns**
- 📊 **Suspicious activity detection**
- 💾 **Automatic encrypted backups**

## Powered By Aegisum EcoSystem