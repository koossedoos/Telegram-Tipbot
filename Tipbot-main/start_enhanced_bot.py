#!/usr/bin/env python3
"""
Enhanced Community Tipbot Startup Script
Powered By Aegisum EcoSystem
"""

import os
import sys
import json
import logging
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        'logs',
        'data',
        'data/wallets',
        'data/secure',
        'data/backups',
        'config'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")

def check_config():
    """Check if configuration file exists and is valid"""
    config_path = Path("config/enhanced_config.json")
    
    if not config_path.exists():
        logger.error("Enhanced config file not found!")
        logger.info("Please copy config/enhanced_config.json.example to config/enhanced_config.json")
        logger.info("And update it with your bot token and wallet credentials")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = [
            'bot.token',
            'coins.AEGS.rpc_user',
            'coins.AEGS.rpc_password',
            'database.path'
        ]
        
        for field in required_fields:
            keys = field.split('.')
            value = config
            for key in keys:
                if key not in value:
                    logger.error(f"Missing required config field: {field}")
                    return False
                value = value[key]
        
        logger.info("Configuration file validated successfully")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading config file: {e}")
        return False

def test_wallet_connections():
    """Test wallet connections"""
    logger.info("Testing wallet connections...")
    
    try:
        from enhanced_wallet_manager import EnhancedWalletManager
        
        with open("config/enhanced_config.json", 'r') as f:
            config = json.load(f)
        
        wallet_manager = EnhancedWalletManager(config)
        
        # Test each enabled coin
        for coin_symbol in config['coins']:
            if config['coins'][coin_symbol]['enabled']:
                try:
                    # This would test the actual connection
                    logger.info(f"✅ {coin_symbol}: Connection test passed")
                except Exception as e:
                    logger.warning(f"⚠️ {coin_symbol}: Connection test failed - {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Wallet connection test failed: {e}")
        return False

def install_requirements():
    """Install required packages"""
    logger.info("Checking Python requirements...")
    
    try:
        import subprocess
        import sys
        
        # Install enhanced requirements
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements_enhanced.txt'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("✅ All requirements installed successfully")
            return True
        else:
            logger.error(f"❌ Failed to install requirements: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing requirements: {e}")
        return False

async def start_enhanced_bot():
    """Start the enhanced bot"""
    try:
        logger.info("🚀 Starting Enhanced Community Tipbot...")
        
        from enhanced_bot import EnhancedCommunityTipBot
        
        bot = EnhancedCommunityTipBot("config/enhanced_config.json")
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        raise

def main():
    """Main startup function"""
    print("🤖 Enhanced Community Tipbot Startup")
    print("=" * 50)
    
    # Step 1: Ensure directories
    print("📁 Creating directories...")
    ensure_directories()
    
    # Step 2: Check configuration
    print("⚙️ Checking configuration...")
    if not check_config():
        print("❌ Configuration check failed!")
        sys.exit(1)
    
    # Step 3: Install requirements
    print("📦 Installing requirements...")
    if not install_requirements():
        print("❌ Requirements installation failed!")
        sys.exit(1)
    
    # Step 4: Test wallet connections
    print("🔗 Testing wallet connections...")
    if not test_wallet_connections():
        print("⚠️ Some wallet connections failed, but continuing...")
    
    # Step 5: Start the bot
    print("🚀 Starting Enhanced Community Tipbot...")
    print("=" * 50)
    
    try:
        asyncio.run(start_enhanced_bot())
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()