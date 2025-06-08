#!/usr/bin/env python3
"""
Community Tipbot - Startup Script
Powered By Aegisum EcoSystem
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main startup function"""
    try:
        # Create necessary directories
        os.makedirs("logs", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        
        # Import and start the bot
        from bot import CommunityTipBot
        
        logger.info("Starting Community Tipbot...")
        
        # Initialize bot
        bot = CommunityTipBot()
        
        # Run the bot
        asyncio.run(bot.run())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()