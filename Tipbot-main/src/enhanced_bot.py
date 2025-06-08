#!/usr/bin/env python3
"""
Enhanced Community Tipbot - Professional Telegram Bot with Advanced Features
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

from enhanced_wallet_manager import EnhancedWalletManager
from database import Database
from admin_controls import AdminControls
from transaction_monitor import TransactionMonitor
from utils import format_amount, validate_address, get_powered_by_text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/enhanced_bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Conversation states
(WALLET_CHOICE, WALLET_PASSWORD, WALLET_CONFIRM_PASSWORD, 
 WALLET_IMPORT_SEED, WITHDRAWAL_PASSWORD, WITHDRAWAL_2FA,
 BACKUP_PASSWORD, BACKUP_2FA) = range(8)

class EnhancedCommunityTipBot:
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize the Enhanced Community Tip Bot"""
        self.config = self.load_config(config_path)
        self.db = Database(self.config['database']['path'])
        self.wallet_manager = EnhancedWalletManager(self.config)
        self.admin_controls = AdminControls(self.config, self.db)
        
        # Bot application
        self.application = None
        
        # Active sessions and features
        self.active_airdrops = {}
        self.rain_participants = {}
        self.user_sessions = {}  # For tracking user states
        self.faucet_claims = {}  # For faucet cooldowns
        self.dice_games = {}     # For dice game sessions
        
        # Privacy settings per user
        self.privacy_settings = {}
        
        # Leaderboard data
        self.leaderboard_cache = {}
        self.leaderboard_cache_time = 0
        
        # Community challenges
        self.active_challenges = {}
        
    def load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced /start command with wallet creation/import flow"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Check if user already has a wallet
        if self._user_has_wallet(user_id):
            # Existing user
            balance_summary = await self._get_balance_summary(user_id)
            
            keyboard = [
                [InlineKeyboardButton("💰 Check Balance", callback_data="balance")],
                [InlineKeyboardButton("📥 Deposit", callback_data="deposit")],
                [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
                [InlineKeyboardButton("🎁 Faucet", callback_data="faucet")],
                [InlineKeyboardButton("📊 Stats", callback_data="stats")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = (
                f"🎉 **Welcome back to Community Tipbot!**\n\n"
                f"👤 **User:** @{username}\n"
                f"💰 **Portfolio Value:** {balance_summary}\n\n"
                f"🚀 **Quick Actions:**\n"
                f"• Use buttons below for quick access\n"
                f"• Type /help for all commands\n"
                f"• Join our community features!\n\n"
                f"🔒 **Your wallet is secure and ready!**\n\n"
                f"{get_powered_by_text()}"
            )
            
            await update.message.reply_text(
                message, 
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            # New user - start wallet creation flow
            await self._start_wallet_setup(update, context)
    
    async def _start_wallet_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start the wallet setup process for new users"""
        keyboard = [
            [InlineKeyboardButton("🆕 Create New Wallet", callback_data="create_wallet")],
            [InlineKeyboardButton("📥 Import Existing Wallet", callback_data="import_wallet")],
            [InlineKeyboardButton("ℹ️ Learn More", callback_data="wallet_info")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = (
            f"🎉 **Welcome to Community Tipbot!**\n\n"
            f"🔐 **Secure Multi-Coin Wallet**\n"
            f"• Support for AEGS, SHIC, PEPE, ADVC\n"
            f"• Password protected with 2FA\n"
            f"• 24-word seed phrase backup\n"
            f"• Non-custodial - you control your keys\n\n"
            f"🚀 **Features:**\n"
            f"• Tip users across all supported coins\n"
            f"• Rain coins to active community members\n"
            f"• Participate in airdrops and challenges\n"
            f"• Secure withdrawals with limits\n"
            f"• Daily faucet rewards\n"
            f"• Dice games and community features\n\n"
            f"**Choose an option to get started:**\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
        
        return WALLET_CHOICE
    
    async def wallet_choice_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle wallet creation/import choice"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "create_wallet":
            await self._start_wallet_creation(update, context)
        elif query.data == "import_wallet":
            await self._start_wallet_import(update, context)
        elif query.data == "wallet_info":
            await self._show_wallet_info(update, context)
        
        return WALLET_PASSWORD
    
    async def _start_wallet_creation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start wallet creation process"""
        message = (
            f"🔐 **Create Secure Wallet**\n\n"
            f"Please create a strong password for your wallet.\n\n"
            f"**Password Requirements:**\n"
            f"• At least 8 characters long\n"
            f"• Include uppercase and lowercase letters\n"
            f"• Include at least one number\n"
            f"• Include at least one special character\n\n"
            f"⚠️ **Important:** This password encrypts your seed phrase.\n"
            f"If you lose it, you cannot recover your wallet!\n\n"
            f"**Please enter your password:**"
        )
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
        context.user_data['wallet_action'] = 'create'
        
        return WALLET_PASSWORD
    
    async def _start_wallet_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start wallet import process"""
        message = (
            f"📥 **Import Existing Wallet**\n\n"
            f"Please enter your 24-word seed phrase.\n\n"
            f"**Format:** word1 word2 word3 ... word24\n\n"
            f"⚠️ **Security Notice:**\n"
            f"• Only enter your seed phrase in this private chat\n"
            f"• Never share your seed phrase with anyone\n"
            f"• Make sure you're in a secure environment\n\n"
            f"**Please enter your seed phrase:**"
        )
        
        await query.edit_message_text(message, parse_mode=ParseMode.MARKDOWN)
        context.user_data['wallet_action'] = 'import'
        
        return WALLET_IMPORT_SEED
    
    async def handle_wallet_password(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle wallet password input"""
        password = update.message.text
        user_id = update.effective_user.id
        
        # Delete the message for security
        await update.message.delete()
        
        # Validate password strength
        if not self._validate_password(password):
            await update.message.reply_text(
                "❌ **Password too weak!**\n\n"
                "Please ensure your password meets all requirements:\n"
                "• At least 8 characters long\n"
                "• Include uppercase and lowercase letters\n"
                "• Include at least one number\n"
                "• Include at least one special character\n\n"
                "**Please try again:**"
            )
            return WALLET_PASSWORD
        
        context.user_data['password'] = password
        
        if context.user_data.get('wallet_action') == 'create':
            # Create new wallet
            try:
                result = await self.wallet_manager.create_wallet(user_id, password)
                
                if result['success']:
                    # Store user in database
                    self.db.create_user(user_id, update.effective_user.username or "Unknown")
                    
                    # Store addresses
                    for coin_symbol, address in result['addresses'].items():
                        self.db.store_user_address(user_id, coin_symbol, address)
                    
                    # Show seed phrase and setup completion
                    await self._show_wallet_created(update, context, result)
                    
                    return ConversationHandler.END
                
            except Exception as e:
                logger.error(f"Failed to create wallet for user {user_id}: {e}")
                await update.message.reply_text(
                    "❌ **Wallet creation failed!**\n\n"
                    "Please try again or contact support.\n\n"
                    "Use /start to begin again."
                )
                return ConversationHandler.END
        
        else:
            # Import wallet - ask for seed phrase
            await update.message.reply_text(
                "🔐 **Password Set Successfully**\n\n"
                "Now please enter your 24-word seed phrase:\n\n"
                "**Format:** word1 word2 word3 ... word24"
            )
            return WALLET_IMPORT_SEED
    
    async def handle_seed_import(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle seed phrase import"""
        seed_phrase = update.message.text.strip()
        user_id = update.effective_user.id
        password = context.user_data.get('password')
        
        # Delete the message for security
        await update.message.delete()
        
        try:
            result = await self.wallet_manager.import_wallet(user_id, seed_phrase, password)
            
            if result['success']:
                # Store user in database
                self.db.create_user(user_id, update.effective_user.username or "Unknown")
                
                # Store addresses
                for coin_symbol, address in result['addresses'].items():
                    self.db.store_user_address(user_id, coin_symbol, address)
                
                # Show import success
                await self._show_wallet_imported(update, context, result)
                
                return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Failed to import wallet for user {user_id}: {e}")
            await update.message.reply_text(
                "❌ **Wallet import failed!**\n\n"
                "Please check your seed phrase and try again.\n\n"
                "Use /start to begin again."
            )
            return ConversationHandler.END
    
    async def _show_wallet_created(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict):
        """Show wallet creation success with seed phrase"""
        user_id = update.effective_user.id
        
        # Create backup message with seed phrase
        seed_message = (
            f"🎉 **Wallet Created Successfully!**\n\n"
            f"🔐 **Your 24-Word Seed Phrase:**\n"
            f"`{result['seed_phrase']}`\n\n"
            f"⚠️ **CRITICAL - READ CAREFULLY:**\n"
            f"• Write down these words in order\n"
            f"• Store them in a safe, offline location\n"
            f"• NEVER share them with anyone\n"
            f"• You need these words to recover your wallet\n"
            f"• If you lose them, your funds are gone forever!\n\n"
            f"🔒 **2FA Setup Required:**\n"
            f"• Scan the QR code below with your authenticator app\n"
            f"• Or manually enter: `{result['two_factor_secret']}`\n\n"
            f"**This message will be deleted in 60 seconds for security!**"
        )
        
        # Send seed phrase message
        seed_msg = await update.message.reply_text(
            seed_message,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Send QR code for 2FA
        qr_msg = await update.message.reply_photo(
            photo=f"data:image/png;base64,{result['qr_code_data']}",
            caption="📱 **Scan this QR code with your authenticator app**"
        )
        
        # Show addresses
        addresses_text = "📥 **Your Deposit Addresses:**\n\n"
        for coin_symbol, address in result['addresses'].items():
            addresses_text += f"**{coin_symbol}:** `{address}`\n\n"
        
        addresses_text += (
            f"✅ **Setup Complete!**\n"
            f"• Your wallet is now ready to use\n"
            f"• Use /help to see all commands\n"
            f"• Use /backup to practice wallet recovery\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(addresses_text, parse_mode=ParseMode.MARKDOWN)
        
        # Schedule deletion of sensitive messages
        asyncio.create_task(self._delete_sensitive_messages([seed_msg, qr_msg], 60))
    
    async def _show_wallet_imported(self, update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict):
        """Show wallet import success"""
        addresses_text = "✅ **Wallet Imported Successfully!**\n\n"
        addresses_text += "📥 **Your Deposit Addresses:**\n\n"
        
        for coin_symbol, address in result['addresses'].items():
            addresses_text += f"**{coin_symbol}:** `{address}`\n\n"
        
        addresses_text += (
            f"🔒 **2FA Secret:** `{result['two_factor_secret']}`\n"
            f"• Add this to your authenticator app\n\n"
            f"✅ **Import Complete!**\n"
            f"• Your wallet is now ready to use\n"
            f"• Use /help to see all commands\n"
            f"• Use /balance to check your funds\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(addresses_text, parse_mode=ParseMode.MARKDOWN)
    
    async def _delete_sensitive_messages(self, messages: List, delay: int):
        """Delete sensitive messages after delay"""
        await asyncio.sleep(delay)
        for msg in messages:
            try:
                await msg.delete()
            except Exception as e:
                logger.warning(f"Failed to delete sensitive message: {e}")
    
    def _validate_password(self, password: str) -> bool:
        """Validate password strength"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _user_has_wallet(self, user_id: int) -> bool:
        """Check if user has a wallet"""
        return self.db.get_user(user_id) is not None
    
    async def _get_balance_summary(self, user_id: int) -> str:
        """Get formatted balance summary"""
        total_value = 0.0
        balances = []
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
                if balance > 0:
                    formatted = format_amount(balance, self.config['coins'][coin_symbol]['decimals'])
                    balances.append(f"{formatted} {coin_symbol}")
        
        if balances:
            return " | ".join(balances[:3]) + ("..." if len(balances) > 3 else "")
        else:
            return "Empty Portfolio"
    
    async def enhanced_balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced balance command with portfolio view"""
        user_id = update.effective_user.id
        
        if not self._user_has_wallet(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!"
            )
            return
        
        # Get balances for all coins
        balances = {}
        total_value = 0.0
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
                balances[coin_symbol] = balance
        
        # Create portfolio view
        portfolio_text = "💰 **Your Portfolio**\n\n"
        
        for coin_symbol, balance in balances.items():
            coin_config = self.config['coins'][coin_symbol]
            formatted_balance = format_amount(balance, coin_config['decimals'])
            
            if balance > 0:
                portfolio_text += f"💎 **{coin_symbol}:** {formatted_balance}\n"
            else:
                portfolio_text += f"⚪ **{coin_symbol}:** {formatted_balance}\n"
        
        # Add quick action buttons
        keyboard = [
            [InlineKeyboardButton("📥 Deposit", callback_data="deposit"),
             InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
            [InlineKeyboardButton("🎁 Faucet", callback_data="faucet"),
             InlineKeyboardButton("🔄 Refresh", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        portfolio_text += f"\n{get_powered_by_text()}"
        
        await update.message.reply_text(
            portfolio_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def enhanced_deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enhanced deposit command with QR codes"""
        user_id = update.effective_user.id
        
        if not self._user_has_wallet(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!"
            )
            return
        
        # Check if this should be DM only
        if update.effective_chat.type != 'private':
            await update.message.reply_text(
                "🔒 **Security Notice**\n\n"
                "For your security, deposit addresses are only shown in private messages.\n\n"
                "Please send me a direct message and use /deposit there."
            )
            return
        
        deposit_text = "📥 **Your Deposit Addresses**\n\n"
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                try:
                    address = await self.wallet_manager.generate_address(user_id, coin_symbol)
                    deposit_text += f"**{coin_symbol} ({self.config['coins'][coin_symbol].get('full_name', coin_symbol)}):**\n"
                    deposit_text += f"`{address}`\n\n"
                except Exception as e:
                    logger.error(f"Failed to get {coin_symbol} address for user {user_id}: {e}")
                    deposit_text += f"**{coin_symbol}:** Error generating address\n\n"
        
        deposit_text += (
            "⚠️ **Important Security Notes:**\n"
            "• Only send the correct coin to each address\n"
            "• Double-check addresses before sending\n"
            "• Deposits require network confirmations\n"
            "• You'll be notified when deposits arrive\n"
            "• Never share these addresses publicly\n\n"
            f"{get_powered_by_text()}"
        )
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🔄 Generate New Address", callback_data="new_address")],
            [InlineKeyboardButton("📊 Transaction History", callback_data="history")],
            [InlineKeyboardButton("💰 Check Balance", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            deposit_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def faucet_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Daily faucet command"""
        user_id = update.effective_user.id
        
        if not self._user_has_wallet(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!"
            )
            return
        
        # Check cooldown
        current_time = time.time()
        last_claim = self.faucet_claims.get(user_id, 0)
        cooldown = 24 * 60 * 60  # 24 hours
        
        if current_time - last_claim < cooldown:
            remaining = cooldown - (current_time - last_claim)
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            
            await update.message.reply_text(
                f"⏰ **Faucet Cooldown**\n\n"
                f"You can claim again in {hours}h {minutes}m\n\n"
                f"💡 **Tip:** While you wait, try:\n"
                f"• Participating in community chat\n"
                f"• Playing /dice games\n"
                f"• Checking /top leaderboards\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Give faucet rewards
        rewards = {}
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                # Random reward amount
                base_amount = self.config.get('faucet', {}).get(coin_symbol, 0.1)
                reward = base_amount * random.uniform(0.5, 2.0)
                rewards[coin_symbol] = reward
        
        # Record faucet claim
        self.faucet_claims[user_id] = current_time
        
        # Add rewards to user balance (simulate)
        reward_text = "🎁 **Daily Faucet Rewards!**\n\n"
        for coin_symbol, amount in rewards.items():
            formatted_amount = format_amount(amount, self.config['coins'][coin_symbol]['decimals'])
            reward_text += f"💰 **{coin_symbol}:** +{formatted_amount}\n"
        
        reward_text += (
            f"\n✅ **Rewards added to your wallet!**\n"
            f"🕐 **Next claim:** 24 hours\n\n"
            f"💡 **Pro Tips:**\n"
            f"• Use /tip to share with friends\n"
            f"• Join /rain events for bonus coins\n"
            f"• Check /challenges for extra rewards\n\n"
            f"{get_powered_by_text()}"
        )
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("💰 Check Balance", callback_data="balance")],
            [InlineKeyboardButton("🎲 Play Dice", callback_data="dice")],
            [InlineKeyboardButton("📊 Leaderboard", callback_data="top")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            reward_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def dice_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Dice gambling game"""
        user_id = update.effective_user.id
        
        if not self._user_has_wallet(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!"
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "🎲 **Dice Game**\n\n"
                "**Usage:** `/dice <coin> <amount>`\n"
                "**Example:** `/dice AEGS 10`\n\n"
                "**Rules:**\n"
                "• Roll 1-2: Lose your bet\n"
                "• Roll 3-4: Get your bet back\n"
                "• Roll 5: Win 2x your bet\n"
                "• Roll 6: Win 3x your bet\n\n"
                "**Limits:**\n"
                "• Min bet: 0.1 of any coin\n"
                "• Max bet: 100 of any coin\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_symbol = context.args[0].upper()
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text("❌ Invalid amount!")
            return
        
        # Validate coin and amount
        if coin_symbol not in self.config['coins'] or not self.config['coins'][coin_symbol]['enabled']:
            await update.message.reply_text(f"❌ Unsupported coin: {coin_symbol}")
            return
        
        if amount < 0.1 or amount > 100:
            await update.message.reply_text("❌ Bet amount must be between 0.1 and 100")
            return
        
        # Check balance
        balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
        if balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {format_amount(balance, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}"
            )
            return
        
        # Roll dice
        roll = random.randint(1, 6)
        
        # Calculate winnings
        if roll <= 2:
            multiplier = 0  # Lose
            result_text = "💸 **You Lost!**"
        elif roll <= 4:
            multiplier = 1  # Break even
            result_text = "😐 **Break Even!**"
        elif roll == 5:
            multiplier = 2  # Win 2x
            result_text = "🎉 **You Won 2x!**"
        else:  # roll == 6
            multiplier = 3  # Win 3x
            result_text = "🚀 **JACKPOT! 3x Win!**"
        
        winnings = amount * multiplier
        net_result = winnings - amount
        
        # Format result message
        dice_emoji = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"][roll - 1]
        
        result_message = (
            f"🎲 **Dice Game Result**\n\n"
            f"🎯 **Roll:** {dice_emoji} ({roll})\n"
            f"💰 **Bet:** {format_amount(amount, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
            f"🎊 **Result:** {result_text}\n"
        )
        
        if net_result > 0:
            result_message += f"💎 **Won:** +{format_amount(net_result, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
        elif net_result < 0:
            result_message += f"💸 **Lost:** {format_amount(abs(net_result), self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
        else:
            result_message += f"🔄 **No change**\n"
        
        result_message += f"\n{get_powered_by_text()}"
        
        # Add play again button
        keyboard = [
            [InlineKeyboardButton("🎲 Play Again", callback_data=f"dice_{coin_symbol}_{amount}")],
            [InlineKeyboardButton("💰 Check Balance", callback_data="balance")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            result_message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show leaderboards"""
        # Check cache
        current_time = time.time()
        if current_time - self.leaderboard_cache_time < 300:  # 5 minutes cache
            leaderboard_data = self.leaderboard_cache
        else:
            # Generate fresh leaderboard data
            leaderboard_data = await self._generate_leaderboard()
            self.leaderboard_cache = leaderboard_data
            self.leaderboard_cache_time = current_time
        
        leaderboard_text = "🏆 **Community Leaderboards**\n\n"
        
        # Top Tippers
        leaderboard_text += "💸 **Top Tippers (This Week):**\n"
        for i, tipper in enumerate(leaderboard_data['top_tippers'][:5], 1):
            medal = ["🥇", "🥈", "🥉", "🏅", "🏅"][i-1]
            leaderboard_text += f"{medal} @{tipper['username']} - {tipper['total_tips']} tips\n"
        
        leaderboard_text += "\n🌧️ **Rain Masters (This Month):**\n"
        for i, rainer in enumerate(leaderboard_data['rain_masters'][:5], 1):
            medal = ["🥇", "🥈", "🥉", "🏅", "🏅"][i-1]
            leaderboard_text += f"{medal} @{rainer['username']} - {rainer['total_rains']} rains\n"
        
        leaderboard_text += "\n💎 **Biggest Holders:**\n"
        for i, holder in enumerate(leaderboard_data['big_holders'][:3], 1):
            medal = ["🥇", "🥈", "🥉"][i-1]
            leaderboard_text += f"{medal} @{holder['username']} - {holder['total_value']} portfolio\n"
        
        leaderboard_text += f"\n📊 **Community Stats:**\n"
        leaderboard_text += f"👥 Total Users: {leaderboard_data['total_users']}\n"
        leaderboard_text += f"💰 Total Tips: {leaderboard_data['total_tips']}\n"
        leaderboard_text += f"🌧️ Total Rains: {leaderboard_data['total_rains']}\n"
        
        leaderboard_text += f"\n{get_powered_by_text()}"
        
        # Add action buttons
        keyboard = [
            [InlineKeyboardButton("🎯 My Stats", callback_data="my_stats")],
            [InlineKeyboardButton("🏆 Challenges", callback_data="challenges")],
            [InlineKeyboardButton("🔄 Refresh", callback_data="top")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            leaderboard_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def _generate_leaderboard(self) -> dict:
        """Generate leaderboard data"""
        # This would query the database for real stats
        # For now, return mock data
        return {
            'top_tippers': [
                {'username': 'user1', 'total_tips': 150},
                {'username': 'user2', 'total_tips': 120},
                {'username': 'user3', 'total_tips': 95},
            ],
            'rain_masters': [
                {'username': 'user1', 'total_rains': 50},
                {'username': 'user4', 'total_rains': 35},
                {'username': 'user2', 'total_rains': 28},
            ],
            'big_holders': [
                {'username': 'user5', 'total_value': '10,000 AEGS'},
                {'username': 'user1', 'total_value': '7,500 AEGS'},
                {'username': 'user6', 'total_value': '5,200 AEGS'},
            ],
            'total_users': 1247,
            'total_tips': 15420,
            'total_rains': 892
        }
    
    async def setup_handlers(self):
        """Setup all command and callback handlers"""
        # Conversation handler for wallet setup
        wallet_conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start_command)],
            states={
                WALLET_CHOICE: [CallbackQueryHandler(self.wallet_choice_callback)],
                WALLET_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_wallet_password)],
                WALLET_IMPORT_SEED: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_seed_import)],
            },
            fallbacks=[CommandHandler('cancel', self.cancel_conversation)]
        )
        
        self.application.add_handler(wallet_conv_handler)
        
        # Regular command handlers
        self.application.add_handler(CommandHandler("balance", self.enhanced_balance_command))
        self.application.add_handler(CommandHandler("deposit", self.enhanced_deposit_command))
        self.application.add_handler(CommandHandler("faucet", self.faucet_command))
        self.application.add_handler(CommandHandler("dice", self.dice_command))
        self.application.add_handler(CommandHandler("top", self.top_command))
        
        # Callback query handlers
        self.application.add_handler(CallbackQueryHandler(self.handle_callback_query))
        
        logger.info("All handlers setup complete")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "balance":
            await self.enhanced_balance_command(update, context)
        elif query.data == "deposit":
            await self.enhanced_deposit_command(update, context)
        elif query.data == "faucet":
            await self.faucet_command(update, context)
        elif query.data == "top":
            await self.top_command(update, context)
        # Add more callback handlers as needed
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel conversation"""
        await update.message.reply_text(
            "❌ **Operation Cancelled**\n\n"
            "Use /start to begin again.\n\n"
            f"{get_powered_by_text()}"
        )
        return ConversationHandler.END
    
    async def start(self):
        """Start the bot"""
        try:
            # Create application
            self.application = Application.builder().token(self.config['bot']['token']).build()
            
            # Setup handlers
            await self.setup_handlers()
            
            # Set bot commands
            commands = [
                BotCommand("start", "Create or access your wallet"),
                BotCommand("balance", "Check your coin balances"),
                BotCommand("deposit", "Get your deposit addresses"),
                BotCommand("withdraw", "Withdraw coins to external address"),
                BotCommand("tip", "Send tips to other users"),
                BotCommand("rain", "Rain coins to active users"),
                BotCommand("faucet", "Claim daily faucet rewards"),
                BotCommand("dice", "Play dice gambling game"),
                BotCommand("top", "View community leaderboards"),
                BotCommand("help", "Show all available commands"),
            ]
            
            await self.application.bot.set_my_commands(commands)
            
            logger.info("Enhanced Community Tipbot starting...")
            
            # Start polling
            await self.application.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            raise

def main():
    """Main function"""
    try:
        bot = EnhancedCommunityTipBot()
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()