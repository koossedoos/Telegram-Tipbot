#!/usr/bin/env python3
"""
Community Tipbot - Main Bot Application
Powered By Aegisum EcoSystem
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

from wallet_manager import WalletManager
from coin_interface import CoinInterface
from database import Database
from admin_controls import AdminControls
from transaction_monitor import TransactionMonitor
from utils import format_amount, validate_address, get_powered_by_text

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CommunityTipBot:
    def __init__(self, config_path: str = "config/config.json"):
        """Initialize the Community Tip Bot"""
        self.config = self.load_config(config_path)
        self.db = Database(self.config['database']['path'])
        self.wallet_manager = WalletManager(self.config)
        self.coin_interface = CoinInterface(self.config)
        self.admin_controls = AdminControls(self.config, self.db)
        self.transaction_monitor = TransactionMonitor(self.config, self.db, self.coin_interface)
        
        # Bot application
        self.application = None
        
        # Active airdrops and rain sessions
        self.active_airdrops = {}
        self.rain_participants = {}
        
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
        """Handle /start command"""
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        
        # Check if user already exists
        user_data = self.db.get_user(user_id)
        
        if user_data:
            message = (
                f"🎉 Welcome back to Community Tipbot!\n\n"
                f"Your wallet is ready to use.\n"
                f"Use /help to see available commands.\n\n"
                f"{get_powered_by_text()}"
            )
        else:
            # Create new user and wallets
            self.db.create_user(user_id, username)
            
            # Generate addresses for all enabled coins
            addresses = {}
            for coin_symbol in self.config['coins']:
                if self.config['coins'][coin_symbol]['enabled']:
                    try:
                        address = await self.wallet_manager.generate_address(user_id, coin_symbol)
                        addresses[coin_symbol] = address
                    except Exception as e:
                        logger.error(f"Failed to generate {coin_symbol} address for user {user_id}: {e}")
            
            # Store addresses in database
            for coin_symbol, address in addresses.items():
                self.db.store_user_address(user_id, coin_symbol, address)
            
            message = (
                f"🎉 Welcome to Community Tipbot!\n\n"
                f"Your multi-coin wallet has been created!\n"
                f"Supported coins: {', '.join(addresses.keys())}\n\n"
                f"Use /deposit to see your deposit addresses\n"
                f"Use /help to see all available commands\n\n"
                f"⚠️ Important: Use /backup to secure your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
        
        await update.message.reply_text(message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "🤖 **Community Tipbot Commands**\n\n"
            "**💰 Wallet Commands:**\n"
            "• `/balance` - View your coin balances\n"
            "• `/deposit` - Get your deposit addresses\n"
            "• `/withdraw <coin> <amount> <address>` - Withdraw coins\n"
            "• `/backup` - Export your wallet backup\n"
            "• `/history` - View transaction history\n\n"
            
            "**🎁 Tipping & Rewards:**\n"
            "• `/tip @user <coin> <amount>` - Send a tip\n"
            "• `/rain <coin> <amount>` - Rain coins to active users\n"
            "• `/airdrop <coin> <amount> <minutes>` - Start an airdrop\n"
            "• `/claimtips` - Claim pending tips\n\n"
            
            "**📊 Community:**\n"
            "• `/top` - View top contributors\n"
            "• `/donate <coin> <amount>` - Donate to community\n"
            "• `/fees` - View current network fees\n\n"
            
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def balance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        user_id = update.effective_user.id
        
        if not self.db.get_user(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        balances = {}
        total_value = 0
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                try:
                    balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
                    balances[coin_symbol] = balance
                except Exception as e:
                    logger.error(f"Failed to get {coin_symbol} balance for user {user_id}: {e}")
                    balances[coin_symbol] = 0
        
        balance_text = "💰 **Your Wallet Balances:**\n\n"
        
        for coin_symbol, balance in balances.items():
            formatted_balance = format_amount(balance, self.config['coins'][coin_symbol]['decimals'])
            balance_text += f"• **{coin_symbol}:** {formatted_balance}\n"
        
        balance_text += f"\n{get_powered_by_text()}"
        
        await update.message.reply_text(balance_text, parse_mode='Markdown')
    
    async def deposit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /deposit command"""
        user_id = update.effective_user.id
        
        if not self.db.get_user(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        deposit_text = "📥 **Your Deposit Addresses:**\n\n"
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                address = self.db.get_user_address(user_id, coin_symbol)
                if address:
                    deposit_text += f"**{coin_symbol}:**\n`{address}`\n\n"
        
        deposit_text += (
            "⚠️ **Important:**\n"
            "• Only send the correct coin to each address\n"
            "• Deposits require confirmations before showing in balance\n"
            "• You'll receive notifications when deposits are detected\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(deposit_text, parse_mode='Markdown')
    
    async def tip_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /tip command"""
        user_id = update.effective_user.id
        
        if not self.config['features']['tipping']:
            await update.message.reply_text(
                "❌ Tipping is currently disabled.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: `/tip @username <coin> <amount>`\n\n"
                "Example: `/tip @alice AEGS 10`\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        target_username = context.args[0].replace('@', '')
        coin_symbol = context.args[1].upper()
        
        try:
            amount = float(context.args[2])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Validate coin
        if coin_symbol not in self.config['coins'] or not self.config['coins'][coin_symbol]['enabled']:
            await update.message.reply_text(
                f"❌ Unsupported coin: {coin_symbol}\n\n"
                f"Supported coins: {', '.join([c for c in self.config['coins'] if self.config['coins'][c]['enabled']])}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Validate amount
        min_amount = self.config['bot']['min_tip_amount']
        max_amount = self.config['bot']['max_tip_amount']
        
        if amount < min_amount or amount > max_amount:
            await update.message.reply_text(
                f"❌ Tip amount must be between {min_amount} and {max_amount} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Find target user
        target_user = self.db.get_user_by_username(target_username)
        if not target_user:
            await update.message.reply_text(
                f"❌ User @{target_username} not found. They need to use /start first.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        target_user_id = target_user['user_id']
        
        # Check if user is trying to tip themselves
        if user_id == target_user_id:
            await update.message.reply_text(
                "❌ You cannot tip yourself!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Check balance
        balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
        if balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {format_amount(balance, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            # Process the tip
            tx_id = await self.wallet_manager.send_tip(user_id, target_user_id, coin_symbol, amount)
            
            # Record in database
            self.db.record_tip(user_id, target_user_id, coin_symbol, amount, tx_id)
            
            # Send confirmation
            formatted_amount = format_amount(amount, self.config['coins'][coin_symbol]['decimals'])
            await update.message.reply_text(
                f"✅ **Tip Sent!**\n\n"
                f"💸 {formatted_amount} {coin_symbol} → @{target_username}\n"
                f"🔗 TX ID: `{tx_id}`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            
            # Notify recipient
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=(
                        f"🎁 **You received a tip!**\n\n"
                        f"💰 {formatted_amount} {coin_symbol} from @{update.effective_user.username or 'Anonymous'}\n"
                        f"🔗 TX ID: `{tx_id}`\n\n"
                        f"Use /claimtips to claim your tips!\n\n"
                        f"{get_powered_by_text()}"
                    ),
                    parse_mode='Markdown'
                )
            except Exception as e:
                logger.warning(f"Could not notify tip recipient {target_user_id}: {e}")
                
        except Exception as e:
            logger.error(f"Failed to process tip: {e}")
            await update.message.reply_text(
                f"❌ Failed to send tip. Please try again later.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def withdraw_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /withdraw command"""
        user_id = update.effective_user.id
        
        if not self.config['features']['withdrawals']:
            await update.message.reply_text(
                "❌ Withdrawals are currently disabled.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: `/withdraw <coin> <amount> <address>`\n\n"
                "Example: `/withdraw AEGS 10 AegsAddressHere123`\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_symbol = context.args[0].upper()
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        address = context.args[2]
        
        # Validate coin
        if coin_symbol not in self.config['coins'] or not self.config['coins'][coin_symbol]['enabled']:
            await update.message.reply_text(
                f"❌ Unsupported coin: {coin_symbol}\n\n"
                f"Supported coins: {', '.join([c for c in self.config['coins'] if self.config['coins'][c]['enabled']])}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Validate address
        if not validate_address(address, coin_symbol):
            await update.message.reply_text(
                f"❌ Invalid {coin_symbol} address format.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Check balance
        balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
        withdrawal_fee = self.config['coins'][coin_symbol]['withdrawal_fee']
        total_needed = amount + withdrawal_fee
        
        if balance < total_needed:
            await update.message.reply_text(
                f"❌ Insufficient balance.\n\n"
                f"Amount: {format_amount(amount, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
                f"Fee: {format_amount(withdrawal_fee, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
                f"Total needed: {format_amount(total_needed, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n"
                f"Your balance: {format_amount(balance, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            # Process withdrawal
            tx_id = await self.wallet_manager.withdraw(user_id, coin_symbol, amount, address)
            
            # Record in database
            self.db.record_withdrawal(user_id, coin_symbol, amount, address, tx_id, withdrawal_fee)
            
            # Send confirmation
            formatted_amount = format_amount(amount, self.config['coins'][coin_symbol]['decimals'])
            formatted_fee = format_amount(withdrawal_fee, self.config['coins'][coin_symbol]['decimals'])
            
            await update.message.reply_text(
                f"✅ **Withdrawal Sent!**\n\n"
                f"💸 {formatted_amount} {coin_symbol}\n"
                f"📍 To: `{address}`\n"
                f"💰 Fee: {formatted_fee} {coin_symbol}\n"
                f"🔗 TX ID: `{tx_id}`\n\n"
                f"⏳ **Status: Pending**\n"
                f"You'll receive a notification when confirmed.\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to process withdrawal: {e}")
            await update.message.reply_text(
                f"❌ Failed to process withdrawal. Please try again later.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def rain_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /rain command"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.config['features']['rain']:
            await update.message.reply_text(
                "❌ Rain is currently disabled.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: `/rain <coin> <amount>`\n\n"
                "Example: `/rain AEGS 100`\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_symbol = context.args[0].upper()
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Validate coin
        if coin_symbol not in self.config['coins'] or not self.config['coins'][coin_symbol]['enabled']:
            await update.message.reply_text(
                f"❌ Unsupported coin: {coin_symbol}\n\n"
                f"Supported coins: {', '.join([c for c in self.config['coins'] if self.config['coins'][c]['enabled']])}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Check balance
        balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
        if balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {format_amount(balance, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Get recent active users (last 24 hours)
        active_users = self.db.get_recent_active_users(chat_id, hours=24)
        active_users = [u for u in active_users if u['user_id'] != user_id]  # Exclude rain sender
        
        if len(active_users) < 2:
            await update.message.reply_text(
                "❌ Not enough active users for rain. Need at least 2 active users in the last 24 hours.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Calculate amount per user
        amount_per_user = amount / len(active_users)
        min_amount = self.config['bot']['min_tip_amount']
        
        if amount_per_user < min_amount:
            await update.message.reply_text(
                f"❌ Rain amount too small. Each user would receive {format_amount(amount_per_user, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}, "
                f"but minimum is {min_amount} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            # Process rain
            rain_id = await self.wallet_manager.process_rain(user_id, coin_symbol, amount, active_users)
            
            # Record in database
            self.db.record_rain(user_id, chat_id, coin_symbol, amount, len(active_users), rain_id)
            
            # Send confirmation
            formatted_total = format_amount(amount, self.config['coins'][coin_symbol]['decimals'])
            formatted_per_user = format_amount(amount_per_user, self.config['coins'][coin_symbol]['decimals'])
            
            await update.message.reply_text(
                f"🌧️ **Rain Started!**\n\n"
                f"💰 {formatted_total} {coin_symbol} distributed\n"
                f"👥 {len(active_users)} recipients\n"
                f"💸 {formatted_per_user} {coin_symbol} each\n\n"
                f"Recipients will be notified!\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            
            # Notify recipients
            for user in active_users:
                try:
                    await context.bot.send_message(
                        chat_id=user['user_id'],
                        text=(
                            f"🌧️ **You caught some rain!**\n\n"
                            f"💰 {formatted_per_user} {coin_symbol}\n"
                            f"👤 From: @{update.effective_user.username or 'Anonymous'}\n\n"
                            f"Use /claimtips to claim your rain!\n\n"
                            f"{get_powered_by_text()}"
                        ),
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.warning(f"Could not notify rain recipient {user['user_id']}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to process rain: {e}")
            await update.message.reply_text(
                f"❌ Failed to process rain. Please try again later.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def claim_tips_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /claimtips command"""
        user_id = update.effective_user.id
        
        if not self.db.get_user(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Get unclaimed tips
        unclaimed_tips = self.db.get_unclaimed_tips(user_id)
        
        if not unclaimed_tips:
            await update.message.reply_text(
                "ℹ️ You have no unclaimed tips.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Mark tips as claimed
        claimed_count = self.db.claim_tips(user_id)
        
        # Calculate totals by coin
        coin_totals = {}
        for tip in unclaimed_tips:
            coin = tip['coin_symbol']
            amount = tip['amount']
            coin_totals[coin] = coin_totals.get(coin, 0) + amount
        
        claim_text = f"✅ **Tips Claimed!**\n\n"
        claim_text += f"📦 **{claimed_count} tips claimed:**\n\n"
        
        for coin, total in coin_totals.items():
            decimals = self.config['coins'][coin]['decimals']
            formatted_total = format_amount(total, decimals)
            claim_text += f"• **{coin}:** {formatted_total}\n"
        
        claim_text += f"\n💰 Your balance has been updated!\n\n{get_powered_by_text()}"
        
        await update.message.reply_text(claim_text, parse_mode='Markdown')
    
    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command"""
        user_id = update.effective_user.id
        
        if not self.db.get_user(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Get user's transaction history
        tips = self.db.get_user_tips(user_id, limit=10)
        
        if not tips:
            await update.message.reply_text(
                "ℹ️ No transaction history found.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        history_text = "📋 **Transaction History** (Last 10)\n\n"
        
        for tip in tips:
            tip_type = "📤 Sent" if tip['from_user_id'] == user_id else "📥 Received"
            other_user = tip['to_username'] if tip['from_user_id'] == user_id else tip['from_username']
            amount = format_amount(tip['amount'], self.config['coins'][tip['coin_symbol']]['decimals'])
            
            history_text += (
                f"{tip_type} {amount} {tip['coin_symbol']}\n"
                f"{'To' if tip['from_user_id'] == user_id else 'From'}: @{other_user or 'Unknown'}\n"
                f"Time: {tip['created_at']}\n\n"
            )
        
        history_text += f"{get_powered_by_text()}"
        
        await update.message.reply_text(history_text, parse_mode='Markdown')
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /backup command"""
        user_id = update.effective_user.id
        
        if not self.config['features']['backup']:
            await update.message.reply_text(
                "❌ Backup feature is currently disabled.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        if not self.db.get_user(user_id):
            await update.message.reply_text(
                "❌ Please use /start first to create your wallet!\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            # Create encrypted backup
            backup_data = await self.wallet_manager.backup_wallet(user_id)
            
            backup_text = (
                f"💾 **Wallet Backup Created**\n\n"
                f"🔐 **Encrypted backup data:**\n"
                f"`{backup_data['encrypted_data'][:100]}...`\n\n"
                f"💰 **Coins backed up:** {', '.join(backup_data['coins_backed_up'])}\n\n"
                f"⚠️ **IMPORTANT:**\n"
                f"• Save this backup data securely\n"
                f"• You'll need it to restore your wallet\n"
                f"• Keep it private and secure\n\n"
                f"{get_powered_by_text()}"
            )
            
            await update.message.reply_text(backup_text, parse_mode='Markdown')
            
            # Send full backup data in a separate message
            await update.message.reply_text(
                f"🔐 **Full Backup Data:**\n`{backup_data['encrypted_data']}`",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Failed to create backup for user {user_id}: {e}")
            await update.message.reply_text(
                f"❌ Failed to create backup. Please try again later.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /top command"""
        try:
            # Get top tippers
            top_tippers = self.db.get_top_users('tippers', limit=5)
            top_receivers = self.db.get_top_users('receivers', limit=5)
            
            top_text = "🏆 **Community Leaderboard**\n\n"
            
            if top_tippers:
                top_text += "**💸 Top Tippers:**\n"
                for i, tipper in enumerate(top_tippers, 1):
                    amount = format_amount(tipper['total_amount'], self.config['coins'][tipper['coin_symbol']]['decimals'])
                    top_text += f"{i}. @{tipper['username']} - {amount} {tipper['coin_symbol']}\n"
                top_text += "\n"
            
            if top_receivers:
                top_text += "**📥 Top Receivers:**\n"
                for i, receiver in enumerate(top_receivers, 1):
                    amount = format_amount(receiver['total_received'], self.config['coins'][receiver['coin_symbol']]['decimals'])
                    top_text += f"{i}. @{receiver['username']} - {amount} {receiver['coin_symbol']}\n"
                top_text += "\n"
            
            if not top_tippers and not top_receivers:
                top_text += "No activity yet. Be the first to tip!\n\n"
            
            top_text += f"{get_powered_by_text()}"
            
            await update.message.reply_text(top_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Failed to get top users: {e}")
            await update.message.reply_text(
                f"❌ Failed to get leaderboard. Please try again later.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def fees_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /fees command"""
        fees_text = "💰 **Current Network Fees**\n\n"
        
        for coin_symbol in self.config['coins']:
            if self.config['coins'][coin_symbol]['enabled']:
                coin_config = self.config['coins'][coin_symbol]
                withdrawal_fee = coin_config['withdrawal_fee']
                network_fee = coin_config['network_fee']
                
                fees_text += (
                    f"**{coin_symbol}:**\n"
                    f"• Withdrawal Fee: {withdrawal_fee} {coin_symbol}\n"
                    f"• Network Fee: {network_fee} {coin_symbol}\n\n"
                )
        
        fees_text += f"{get_powered_by_text()}"
        
        await update.message.reply_text(fees_text, parse_mode='Markdown')
    
    async def airdrop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /airdrop command"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        if not self.config['features']['airdrops']:
            await update.message.reply_text(
                "❌ Airdrops are currently disabled.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        if len(context.args) < 3:
            await update.message.reply_text(
                "❌ Usage: `/airdrop <coin> <amount> <minutes>`\n\n"
                "Example: `/airdrop AEGS 100 5`\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Placeholder for airdrop functionality
        await update.message.reply_text(
            "🚧 **Airdrop Feature**\n\n"
            "This feature is coming soon!\n"
            "Users will be able to join airdrops and receive coins after a timer.\n\n"
            f"{get_powered_by_text()}",
            parse_mode='Markdown'
        )
    
    async def donate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /donate command"""
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: `/donate <coin> <amount>`\n\n"
                "Example: `/donate AEGS 10`\n\n"
                "Donations support the community and development.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_symbol = context.args[0].upper()
        
        try:
            amount = float(context.args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid amount. Please enter a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Validate coin
        if coin_symbol not in self.config['coins'] or not self.config['coins'][coin_symbol]['enabled']:
            await update.message.reply_text(
                f"❌ Unsupported coin: {coin_symbol}\n\n"
                f"Supported coins: {', '.join([c for c in self.config['coins'] if self.config['coins'][c]['enabled']])}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # Check balance
        balance = await self.wallet_manager.get_balance(user_id, coin_symbol)
        if balance < amount:
            await update.message.reply_text(
                f"❌ Insufficient balance. You have {format_amount(balance, self.config['coins'][coin_symbol]['decimals'])} {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        # For now, just show a thank you message (donation address would be configured)
        formatted_amount = format_amount(amount, self.config['coins'][coin_symbol]['decimals'])
        await update.message.reply_text(
            f"💝 **Thank you for your donation!**\n\n"
            f"💰 Amount: {formatted_amount} {coin_symbol}\n\n"
            f"🚧 Donation feature is being finalized.\n"
            f"Your generous contribution will support the community!\n\n"
            f"{get_powered_by_text()}",
            parse_mode='Markdown'
        )
    
    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages for activity tracking"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Update user activity for rain eligibility
        self.db.update_user_activity(user_id, chat_id)
    
    async def setup_handlers(self):
        """Setup all command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("balance", self.balance_command))
        self.application.add_handler(CommandHandler("deposit", self.deposit_command))
        self.application.add_handler(CommandHandler("tip", self.tip_command))
        self.application.add_handler(CommandHandler("withdraw", self.withdraw_command))
        self.application.add_handler(CommandHandler("rain", self.rain_command))
        self.application.add_handler(CommandHandler("claimtips", self.claim_tips_command))
        self.application.add_handler(CommandHandler("history", self.history_command))
        self.application.add_handler(CommandHandler("backup", self.backup_command))
        self.application.add_handler(CommandHandler("top", self.top_command))
        self.application.add_handler(CommandHandler("fees", self.fees_command))
        self.application.add_handler(CommandHandler("airdrop", self.airdrop_command))
        self.application.add_handler(CommandHandler("donate", self.donate_command))
        
        # Message handler for activity tracking
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.message_handler))
        
        # Admin handlers
        admin_handlers = self.admin_controls.get_handlers()
        for handler in admin_handlers:
            self.application.add_handler(handler)
        
        logger.info("All handlers setup complete")
    
    async def run(self):
        """Start the bot"""
        try:
            # Initialize database
            await self.db.initialize()
            
            # Create application
            self.application = Application.builder().token(self.config['bot']['token']).build()
            
            # Setup handlers
            await self.setup_handlers()
            
            # Start transaction monitor
            await self.transaction_monitor.start()
            
            logger.info("Community Tipbot starting...")
            
            # Start the bot
            await self.application.run_polling(drop_pending_updates=True)
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    # Initialize and run bot
    bot = CommunityTipBot()
    asyncio.run(bot.run())

if __name__ == "__main__":
    main()