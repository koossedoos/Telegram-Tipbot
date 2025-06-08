#!/usr/bin/env python3
"""
Optimized Multi-Coin Tipbot Startup Script
Powered By Aegisum EcoSystem
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from optimized_bot import OptimizedMultiCoinTipBot

def check_config():
    """Check if configuration exists and is valid"""
    config_path = "config/config.json"
    
    if not os.path.exists(config_path):
        print("❌ Configuration file not found!")
        print("📋 Please copy config/config.example.json to config/config.json and edit it.")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ['bot.token', 'coins.AEGS', 'coins.ADVC', 'coins.SHIC', 'coins.PEPE']
        
        for field in required_fields:
            keys = field.split('.')
            current = config
            for key in keys:
                if key not in current:
                    print(f"❌ Missing required configuration: {field}")
                    return False
                current = current[key]
        
        # Check if token is placeholder
        if config['bot']['token'] == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
            print("❌ Please set your Telegram bot token in config/config.json")
            return False
        
        print("✅ Configuration validated successfully")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in configuration file: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import telegram
        import cryptography
        import aiosqlite
        import mnemonic
        import qrcode
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("📦 Please run: pip install -r requirements.txt")
        return False

def setup_directories():
    """Create necessary directories"""
    directories = [
        "data",
        "data/wallets", 
        "data/secure",
        "data/backups",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def main():
    """Main startup function"""
    print("🚀 Optimized Multi-Coin Tipbot")
    print("=" * 50)
    print("Supported Coins: AEGS, ADVC, SHIC, PEPE")
    print("Powered By Aegisum EcoSystem")
    print("=" * 50)
    print()
    
    # Pre-flight checks
    print("🔍 Running pre-flight checks...")
    
    if not check_dependencies():
        sys.exit(1)
    
    if not check_config():
        sys.exit(1)
    
    setup_directories()
    
    print()
    print("✅ All checks passed!")
    print("🚀 Starting bot...")
    print()
    
    # Start the bot
    try:
        bot = OptimizedMultiCoinTipBot()
        import asyncio
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Bot crashed: {e}")
        logging.exception("Bot crash details:")
        sys.exit(1)

if __name__ == "__main__":
    main()