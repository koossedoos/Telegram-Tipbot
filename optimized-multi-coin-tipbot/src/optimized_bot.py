#!/usr/bin/env python3
"""
Optimized Multi-Coin Tipbot for Aegisum, ADVC, ShibaCoin, PepeCoin
Powered By Aegisum EcoSystem
"""

import asyncio
import json
import logging
import os
import sys
import time
import random
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters, ConversationHandler
)
from telegram.constants import ParseMode

from wallet_manager import EnhancedWalletManager
from database import Database
from utils import format_amount, validate_address, get_powered_by_text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('data/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
(WALLET_CHOICE, WALLET_PASSWORD, WITHDRAWAL_PASSWORD, BACKUP_PASSWORD) = range(4)

class OptimizedMultiCoinTipBot:
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize the Optimized Multi-Coin Tip Bot"""
        self.config_path = config_path
        self.load_config()
        
        # Initialize components
        self.wallet_manager = EnhancedWalletManager(self.config)
        self.database = Database(self.config['database']['path'])
        
        # Supported coins (only your 4 coins)
        self.supported_coins = ['AEGS', 'ADVC', 'SHIC', 'PEPE']
        
        # Rate limiting
        self.user_cooldowns = {}
        self.command_usage = {}
        
        # Statistics
        self.stats = {
            'tips_sent': 0,
            'total_volume': {},
            'active_users': set(),
            'commands_processed': 0
        }
        
        # Initialize stats for each coin
        for coin in self.supported_coins:
            self.stats['total_volume'][coin] = 0.0
    
    def load_config(self):
        """Load configuration from JSON file"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file {self.config_path} not found!")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
    
    def check_cooldown(self, user_id: int, command: str) -> bool:
        """Check if user is on cooldown for a command"""
        now = time.time()
        cooldown_key = f"{user_id}_{command}"
        
        if cooldown_key in self.user_cooldowns:
            time_left = self.user_cooldowns[cooldown_key] - now
            if time_left > 0:
                return False
        
        # Set cooldown
        cooldown_seconds = self.config['bot'].get('cooldown_seconds', 30)
        self.user_cooldowns[cooldown_key] = now + cooldown_seconds
        return True
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        self.stats['active_users'].add(user.id)
        
        welcome_message = f"""
🚀 **Welcome to the Optimized Multi-Coin Tipbot!**

Supported Coins:
🔹 **AEGS** (Aegisum) - Primary coin
🔹 **ADVC** (AdventureCoin)
🔹 **SHIC** (ShibaCoin)  
🔹 **PEPE** (PepeCoin)

**Quick Commands:**
• `/balance <coin>` - Check your balance
• `/deposit <coin>` - Get deposit address
• `/tip @user <amount> <coin>` - Send a tip
• `/withdraw <address> <amount> <coin>` - Withdraw coins
• `/rain <amount> <coin>` - Rain coins to active users
• `/faucet <coin>` - Get free coins (24h cooldown)
• `/help` - Show all commands

**Security Features:**
🔐 Encrypted wallet storage
🔑 2FA for withdrawals
🛡️ Rate limiting & cooldowns
💾 Automatic backups

{get_powered_by_text()}
"""
        
        await update.message.reply_text(
            welcome_message,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = f"""
📚 **Optimized Multi-Coin Tipbot Commands**

**💰 Wallet Commands:**
• `/balance <coin>` - Check balance
• `/deposit <coin>` - Get deposit address
• `/withdraw <address> <amount> <coin>` - Withdraw
• `/backup` - Backup your wallet

**🎁 Tipping Commands:**
• `/tip @user <amount> <coin>` - Send tip
• `/rain <amount> <coin>` - Rain to active users
• `/airdrop <amount> <coin> <duration>` - Create airdrop

**🎮 Fun Commands:**
• `/faucet <coin>` - Free coins (24h cooldown)
• `/dice <amount> <coin>` - Dice game
• `/leaderboard` - Top tippers

**📊 Info Commands:**
• `/stats` - Bot statistics
• `/price <coin>` - Coin price (if available)
• `/about` - About this bot

**Supported Coins:** AEGS, ADVC, SHIC, PEPE

{get_powered_by_text()}
"""
        
        await update.message.reply_text(
            help_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user_id = update.effective_user.id
        
        if not self.check_cooldown(user_id, 'balance'):
            await update.message.reply_text("⏰ Please wait before using this command again.")
            return
        
        if not context.args:
            # Show all balances
            balances = []
            for coin in self.supported_coins:
                try:
                    balance = await self.wallet_manager.get_balance(user_id, coin)
                    if balance > 0:
                        balances.append(f"**{coin}:** {format_amount(balance)}")
                except Exception as e:
                    logger.error(f"Error getting balance for {coin}: {e}")
                    balances.append(f"**{coin}:** Error")
            
            if balances:
                balance_text = "💰 **Your Balances:**\n\n" + "\n".join(balances)
            else:
                balance_text = "💰 **Your Balances:**\n\nNo balances found. Use `/faucet <coin>` to get started!"
        else:
            # Show specific coin balance
            coin = context.args[0].upper()
            if coin not in self.supported_coins:
                await update.message.reply_text(f"❌ Unsupported coin: {coin}\nSupported: {', '.join(self.supported_coins)}")
                return
            
            try:
                balance = await self.wallet_manager.get_balance(user_id, coin)
                balance_text = f"💰 **{coin} Balance:** {format_amount(balance)}"
            except Exception as e:
                logger.error(f"Error getting {coin} balance: {e}")
                balance_text = f"❌ Error getting {coin} balance"
        
        balance_text += f"\n\n{get_powered_by_text()}"
        
        await update.message.reply_text(
            balance_text,
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deposit command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                f"❌ Please specify a coin: `/deposit <coin>`\nSupported: {', '.join(self.supported_coins)}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        coin = context.args[0].upper()
        if coin not in self.supported_coins:
            await update.message.reply_text(f"❌ Unsupported coin: {coin}\nSupported: {', '.join(self.supported_coins)}")
            return
        
        try:
            address = await self.wallet_manager.get_deposit_address(user_id, coin)
            
            deposit_text = f"""
🏦 **{coin} Deposit Address**

`{address}`

⚠️ **Important:**
• Only send {coin} to this address
• Minimum confirmations: {self.config['coins'][coin]['min_confirmations']}
• Deposits will appear after confirmations

{get_powered_by_text()}
"""
            
            await update.message.reply_text(
                deposit_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error getting deposit address for {coin}: {e}")
            await update.message.reply_text("❌ Error generating deposit address. Please try again later.")
    
    async def tip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tip command"""
        user_id = update.effective_user.id
        
        if not self.check_cooldown(user_id, 'tip'):
            await update.message.reply_text("⏰ Please wait before tipping again.")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: `/tip @username <amount> <coin>`\nExample: `/tip @alice 10 AEGS`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Parse arguments
        recipient_username = context.args[0].replace('@', '')
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a number.")
            return
        
        coin = context.args[2].upper()
        if coin not in self.supported_coins:
            await update.message.reply_text(f"❌ Unsupported coin: {coin}\nSupported: {', '.join(self.supported_coins)}")
            return
        
        # Validate amount
        min_amount = self.config['bot']['min_tip_amount']
        max_amount = self.config['bot']['max_tip_amount']
        
        if amount < min_amount:
            await update.message.reply_text(f"❌ Minimum tip amount: {min_amount}")
            return
        
        if amount > max_amount:
            await update.message.reply_text(f"❌ Maximum tip amount: {max_amount}")
            return
        
        try:
            # Get recipient user ID
            recipient_id = await self.database.get_user_id_by_username(recipient_username)
            if not recipient_id:
                await update.message.reply_text(f"❌ User @{recipient_username} not found. They need to start the bot first.")
                return
            
            if recipient_id == user_id:
                await update.message.reply_text("❌ You cannot tip yourself!")
                return
            
            # Check balance
            balance = await self.wallet_manager.get_balance(user_id, coin)
            if balance < amount:
                await update.message.reply_text(f"❌ Insufficient balance. You have {format_amount(balance)} {coin}")
                return
            
            # Process tip
            success = await self.wallet_manager.transfer(user_id, recipient_id, amount, coin)
            
            if success:
                # Update statistics
                self.stats['tips_sent'] += 1
                self.stats['total_volume'][coin] += amount
                
                # Record in database
                await self.database.record_tip(user_id, recipient_id, amount, coin)
                
                tip_text = f"""
🎁 **Tip Sent Successfully!**

**From:** {update.effective_user.first_name}
**To:** @{recipient_username}
**Amount:** {format_amount(amount)} {coin}

{get_powered_by_text()}
"""
                
                await update.message.reply_text(
                    tip_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Notify recipient
                try:
                    await context.bot.send_message(
                        recipient_id,
                        f"🎁 You received a tip of {format_amount(amount)} {coin} from {update.effective_user.first_name}!"
                    )
                except:
                    pass  # Recipient might have blocked the bot
                
            else:
                await update.message.reply_text("❌ Tip failed. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error processing tip: {e}")
            await update.message.reply_text("❌ Error processing tip. Please try again later.")
    
    async def faucet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /faucet command"""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                f"❌ Please specify a coin: `/faucet <coin>`\nSupported: {', '.join(self.supported_coins)}",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        coin = context.args[0].upper()
        if coin not in self.supported_coins:
            await update.message.reply_text(f"❌ Unsupported coin: {coin}\nSupported: {', '.join(self.supported_coins)}")
            return
        
        try:
            # Check cooldown (24 hours)
            last_faucet = await self.database.get_last_faucet_time(user_id, coin)
            if last_faucet:
                time_diff = datetime.now() - last_faucet
                if time_diff.total_seconds() < 86400:  # 24 hours
                    hours_left = 24 - (time_diff.total_seconds() / 3600)
                    await update.message.reply_text(f"⏰ Faucet cooldown: {hours_left:.1f} hours remaining")
                    return
            
            # Get faucet amount
            faucet_amount = self.config['faucet']['rewards'].get(coin, 1.0)
            
            # Add random bonus
            bonus_range = self.config['faucet']['bonus_multiplier_range']
            bonus = random.uniform(bonus_range[0], bonus_range[1])
            final_amount = faucet_amount * bonus
            
            # Credit user
            success = await self.wallet_manager.credit_user(user_id, final_amount, coin)
            
            if success:
                await self.database.record_faucet_claim(user_id, coin, final_amount)
                
                faucet_text = f"""
🚰 **Faucet Claim Successful!**

**Amount:** {format_amount(final_amount)} {coin}
**Bonus:** {bonus:.2f}x

Next claim available in 24 hours.

{get_powered_by_text()}
"""
                
                await update.message.reply_text(
                    faucet_text,
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("❌ Faucet temporarily unavailable. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error processing faucet claim: {e}")
            await update.message.reply_text("❌ Error processing faucet claim. Please try again later.")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        try:
            total_volume_text = []
            for coin in self.supported_coins:
                volume = self.stats['total_volume'][coin]
                if volume > 0:
                    total_volume_text.append(f"**{coin}:** {format_amount(volume)}")
            
            stats_text = f"""
📊 **Bot Statistics**

**Tips Sent:** {self.stats['tips_sent']:,}
**Active Users:** {len(self.stats['active_users']):,}
**Commands Processed:** {self.stats['commands_processed']:,}

**Total Volume:**
{chr(10).join(total_volume_text) if total_volume_text else "No volume yet"}

**Supported Coins:** {', '.join(self.supported_coins)}

{get_powered_by_text()}
"""
            
            await update.message.reply_text(
                stats_text,
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            await update.message.reply_text("❌ Error getting statistics.")
    
    async def about_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /about command"""
        about_text = f"""
🤖 **Optimized Multi-Coin Tipbot**

**Version:** 1.0.0
**Supported Coins:** AEGS, ADVC, SHIC, PEPE

**Features:**
🔹 Secure multi-coin tipping
🔹 Encrypted wallet storage
🔹 2FA security for withdrawals
🔹 Faucet system
🔹 Rain and airdrops
🔹 Dice games
🔹 Real-time monitoring

**Security:**
🔐 All wallets are encrypted
🛡️ Rate limiting and cooldowns
💾 Automatic backups
🔑 2FA for sensitive operations

**Developer:** Aegisum EcoSystem
**Support:** Contact your server administrator

{get_powered_by_text()}
"""
        
        await update.message.reply_text(
            about_text,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Exception while handling an update: {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again later."
            )
    
    def setup_handlers(self, application: Application):
        """Setup command handlers"""
        # Command handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("balance", self.balance_command))
        application.add_handler(CommandHandler("deposit", self.deposit_command))
        application.add_handler(CommandHandler("tip", self.tip_command))
        application.add_handler(CommandHandler("faucet", self.faucet_command))
        application.add_handler(CommandHandler("stats", self.stats_command))
        application.add_handler(CommandHandler("about", self.about_command))
        
        # Error handler
        application.add_error_handler(self.error_handler)
        
        logger.info("Command handlers setup complete")
    
    async def run(self):
        """Run the bot"""
        try:
            # Create application
            application = Application.builder().token(self.config['bot']['token']).build()
            
            # Setup handlers
            self.setup_handlers(application)
            
            # Set bot commands
            commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Show help"),
                BotCommand("balance", "Check balance"),
                BotCommand("deposit", "Get deposit address"),
                BotCommand("tip", "Send a tip"),
                BotCommand("faucet", "Get free coins"),
                BotCommand("stats", "Bot statistics"),
                BotCommand("about", "About this bot"),
            ]
            
            await application.bot.set_my_commands(commands)
            
            logger.info("🚀 Optimized Multi-Coin Tipbot starting...")
            logger.info(f"Supported coins: {', '.join(self.supported_coins)}")
            
            # Start the bot
            await application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise

def main():
    """Main function"""
    # Create data directory
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/wallets", exist_ok=True)
    os.makedirs("data/secure", exist_ok=True)
    
    # Initialize and run bot
    bot = OptimizedMultiCoinTipBot()
    
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()