#!/usr/bin/env python3
"""
Admin Controls - Handles administrative commands and settings
Powered By Aegisum EcoSystem
"""

import json
import logging
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, ContextTypes

from utils import get_powered_by_text, format_amount

logger = logging.getLogger(__name__)

class AdminControls:
    def __init__(self, config: dict, database):
        self.config = config
        self.db = database
        self.admin_users = set(config['bot'].get('admin_users', []))
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin"""
        return user_id in self.admin_users
    
    def get_handlers(self) -> List[CommandHandler]:
        """Get all admin command handlers"""
        return [
            CommandHandler("admin", self.admin_command),
            CommandHandler("setgroups", self.set_groups_command),
            CommandHandler("setcooldown", self.set_cooldown_command),
            CommandHandler("disable", self.disable_command),
            CommandHandler("enable", self.enable_command),
            CommandHandler("addcoin", self.add_coin_command),
            CommandHandler("setfees", self.set_fees_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("addadmin", self.add_admin_command),
            CommandHandler("removeadmin", self.remove_admin_command),
            CommandHandler("broadcast", self.broadcast_command),
            CommandHandler("maintenance", self.maintenance_command),
            CommandHandler("backup", self.backup_command),
            CommandHandler("coininfo", self.coin_info_command),
        ]
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main admin command - shows admin panel"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text(
                "❌ You don't have admin privileges.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        admin_text = (
            "🛡️ **Admin Control Panel**\n\n"
            "**Feature Controls:**\n"
            "• `/disable <feature>` - Disable feature\n"
            "• `/enable <feature>` - Enable feature\n"
            "• `/setcooldown <seconds>` - Set command cooldown\n\n"
            
            "**Group Management:**\n"
            "• `/setgroups <group_ids>` - Set allowed groups\n\n"
            
            "**Coin Management:**\n"
            "• `/addcoin <symbol>` - Add new coin support\n"
            "• `/setfees <coin> <fee>` - Update withdrawal fees\n"
            "• `/coininfo <coin>` - View coin information\n\n"
            
            "**Statistics & Monitoring:**\n"
            "• `/stats` - View global statistics\n"
            "• `/backup` - Create system backup\n\n"
            
            "**User Management:**\n"
            "• `/addadmin <user_id>` - Add admin user\n"
            "• `/removeadmin <user_id>` - Remove admin user\n"
            "• `/broadcast <message>` - Send message to all users\n\n"
            
            "**System:**\n"
            "• `/maintenance <on/off>` - Toggle maintenance mode\n\n"
            
            f"**Available Features:** {', '.join(self.config['features'].keys())}\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(admin_text, parse_mode='Markdown')
    
    async def set_groups_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set allowed groups"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            current_groups = self.config['bot'].get('allowed_groups', [])
            await update.message.reply_text(
                f"📋 **Current allowed groups:**\n"
                f"{', '.join(map(str, current_groups)) if current_groups else 'All groups allowed'}\n\n"
                f"Usage: `/setgroups <group_id1> <group_id2> ...`\n"
                f"Use `/setgroups all` to allow all groups\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        if context.args[0].lower() == 'all':
            self.config['bot']['allowed_groups'] = []
            self.db.set_admin_setting('allowed_groups', json.dumps([]))
            await update.message.reply_text(
                "✅ All groups are now allowed.\n\n"
                f"{get_powered_by_text()}"
            )
        else:
            try:
                group_ids = [int(arg) for arg in context.args]
                self.config['bot']['allowed_groups'] = group_ids
                self.db.set_admin_setting('allowed_groups', json.dumps(group_ids))
                
                await update.message.reply_text(
                    f"✅ Allowed groups updated: {', '.join(map(str, group_ids))}\n\n"
                    f"{get_powered_by_text()}"
                )
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid group IDs. Please provide valid integers.\n\n"
                    f"{get_powered_by_text()}"
                )
    
    async def set_cooldown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set command cooldown"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            current_cooldown = self.config['bot'].get('cooldown_seconds', 30)
            await update.message.reply_text(
                f"⏱️ **Current cooldown:** {current_cooldown} seconds\n\n"
                f"Usage: `/setcooldown <seconds>`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        try:
            cooldown = int(context.args[0])
            if cooldown < 0:
                raise ValueError("Cooldown must be non-negative")
            
            self.config['bot']['cooldown_seconds'] = cooldown
            self.db.set_admin_setting('cooldown_seconds', str(cooldown))
            
            await update.message.reply_text(
                f"✅ Command cooldown set to {cooldown} seconds.\n\n"
                f"{get_powered_by_text()}"
            )
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid cooldown value. Please provide a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def disable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disable a feature"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            enabled_features = [f for f, enabled in self.config['features'].items() if enabled]
            await update.message.reply_text(
                f"🔧 **Available features to disable:**\n"
                f"{', '.join(enabled_features)}\n\n"
                f"Usage: `/disable <feature>`\n\n"
                f"You can also disable specific coins: `/disable <coin_symbol>`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        feature = context.args[0].lower()
        
        # Check if it's a feature
        if feature in self.config['features']:
            self.config['features'][feature] = False
            self.db.set_admin_setting(f'feature_{feature}', 'false')
            
            await update.message.reply_text(
                f"✅ Feature '{feature}' has been disabled.\n\n"
                f"{get_powered_by_text()}"
            )
        
        # Check if it's a coin
        elif feature.upper() in self.config['coins']:
            coin_symbol = feature.upper()
            self.config['coins'][coin_symbol]['enabled'] = False
            self.db.set_admin_setting(f'coin_{coin_symbol}_enabled', 'false')
            
            await update.message.reply_text(
                f"✅ Coin '{coin_symbol}' has been disabled.\n\n"
                f"{get_powered_by_text()}"
            )
        
        else:
            await update.message.reply_text(
                f"❌ Unknown feature or coin: {feature}\n\n"
                f"Available features: {', '.join(self.config['features'].keys())}\n"
                f"Available coins: {', '.join(self.config['coins'].keys())}\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def enable_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Enable a feature"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            disabled_features = [f for f, enabled in self.config['features'].items() if not enabled]
            await update.message.reply_text(
                f"🔧 **Available features to enable:**\n"
                f"{', '.join(disabled_features)}\n\n"
                f"Usage: `/enable <feature>`\n\n"
                f"You can also enable specific coins: `/enable <coin_symbol>`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        feature = context.args[0].lower()
        
        # Check if it's a feature
        if feature in self.config['features']:
            self.config['features'][feature] = True
            self.db.set_admin_setting(f'feature_{feature}', 'true')
            
            await update.message.reply_text(
                f"✅ Feature '{feature}' has been enabled.\n\n"
                f"{get_powered_by_text()}"
            )
        
        # Check if it's a coin
        elif feature.upper() in self.config['coins']:
            coin_symbol = feature.upper()
            self.config['coins'][coin_symbol]['enabled'] = True
            self.db.set_admin_setting(f'coin_{coin_symbol}_enabled', 'true')
            
            await update.message.reply_text(
                f"✅ Coin '{coin_symbol}' has been enabled.\n\n"
                f"{get_powered_by_text()}"
            )
        
        else:
            await update.message.reply_text(
                f"❌ Unknown feature or coin: {feature}\n\n"
                f"Available features: {', '.join(self.config['features'].keys())}\n"
                f"Available coins: {', '.join(self.config['coins'].keys())}\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show global statistics"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        try:
            stats = self.db.get_statistics()
            
            stats_text = (
                "📊 **Global Statistics**\n\n"
                f"👥 **Total Users:** {stats.get('total_users', 0)}\n"
                f"💸 **Total Tips:** {stats.get('total_tips', 0)}\n"
                f"🌧️ **Total Rain Events:** {stats.get('total_rain', 0)}\n"
                f"💳 **Total Withdrawals:** {stats.get('total_withdrawals', 0)}\n\n"
                
                "**Per-Coin Statistics:**\n"
            )
            
            coin_stats = stats.get('coin_stats', {})
            for coin_symbol, coin_data in coin_stats.items():
                tip_count = coin_data.get('tip_count', 0)
                total_tipped = coin_data.get('total_tipped', 0)
                decimals = self.config['coins'].get(coin_symbol, {}).get('decimals', 8)
                formatted_total = format_amount(total_tipped, decimals)
                
                stats_text += f"• **{coin_symbol}:** {tip_count} tips, {formatted_total} total\n"
            
            stats_text += f"\n{get_powered_by_text()}"
            
            await update.message.reply_text(stats_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            await update.message.reply_text(
                f"❌ Failed to retrieve statistics.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new admin user"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text(
                f"Usage: `/addadmin <user_id>`\n\n"
                f"Current admins: {', '.join(map(str, self.admin_users))}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            new_admin_id = int(context.args[0])
            
            if new_admin_id in self.admin_users:
                await update.message.reply_text(
                    f"ℹ️ User {new_admin_id} is already an admin.\n\n"
                    f"{get_powered_by_text()}"
                )
                return
            
            self.admin_users.add(new_admin_id)
            self.config['bot']['admin_users'] = list(self.admin_users)
            self.db.set_admin_setting('admin_users', json.dumps(list(self.admin_users)))
            
            await update.message.reply_text(
                f"✅ User {new_admin_id} has been added as an admin.\n\n"
                f"{get_powered_by_text()}"
            )
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Invalid user ID. Please provide a valid integer.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def remove_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Remove an admin user"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text(
                f"Usage: `/removeadmin <user_id>`\n\n"
                f"Current admins: {', '.join(map(str, self.admin_users))}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            remove_admin_id = int(context.args[0])
            
            if remove_admin_id == user_id:
                await update.message.reply_text(
                    f"❌ You cannot remove yourself as an admin.\n\n"
                    f"{get_powered_by_text()}"
                )
                return
            
            if remove_admin_id not in self.admin_users:
                await update.message.reply_text(
                    f"ℹ️ User {remove_admin_id} is not an admin.\n\n"
                    f"{get_powered_by_text()}"
                )
                return
            
            self.admin_users.remove(remove_admin_id)
            self.config['bot']['admin_users'] = list(self.admin_users)
            self.db.set_admin_setting('admin_users', json.dumps(list(self.admin_users)))
            
            await update.message.reply_text(
                f"✅ User {remove_admin_id} has been removed as an admin.\n\n"
                f"{get_powered_by_text()}"
            )
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Invalid user ID. Please provide a valid integer.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def coin_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show coin information"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            coin_list = ', '.join(self.config['coins'].keys())
            await update.message.reply_text(
                f"💰 **Available coins:** {coin_list}\n\n"
                f"Usage: `/coininfo <coin_symbol>`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        coin_symbol = context.args[0].upper()
        
        if coin_symbol not in self.config['coins']:
            await update.message.reply_text(
                f"❌ Unknown coin: {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_config = self.config['coins'][coin_symbol]
        
        info_text = (
            f"💰 **{coin_symbol} Information**\n\n"
            f"**Status:** {'✅ Enabled' if coin_config.get('enabled') else '❌ Disabled'}\n"
            f"**CLI Path:** `{coin_config.get('cli_path', 'N/A')}`\n"
            f"**Decimals:** {coin_config.get('decimals', 8)}\n"
            f"**Min Confirmations:** {coin_config.get('min_confirmations', 6)}\n"
            f"**Withdrawal Fee:** {coin_config.get('withdrawal_fee', 0)} {coin_symbol}\n"
            f"**Network Fee:** {coin_config.get('network_fee', 0)} {coin_symbol}\n"
            f"**RPC Host:** {coin_config.get('rpc_host', 'N/A')}\n"
            f"**RPC Port:** {coin_config.get('rpc_port', 'N/A')}\n\n"
            f"{get_powered_by_text()}"
        )
        
        await update.message.reply_text(info_text, parse_mode='Markdown')
    
    async def set_fees_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set withdrawal fees for a coin"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text(
                f"Usage: `/setfees <coin> <withdrawal_fee>`\n\n"
                f"Example: `/setfees AEGS 0.001`\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        coin_symbol = context.args[0].upper()
        
        if coin_symbol not in self.config['coins']:
            await update.message.reply_text(
                f"❌ Unknown coin: {coin_symbol}\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        try:
            new_fee = float(context.args[1])
            
            if new_fee < 0:
                raise ValueError("Fee cannot be negative")
            
            self.config['coins'][coin_symbol]['withdrawal_fee'] = new_fee
            self.db.set_admin_setting(f'coin_{coin_symbol}_withdrawal_fee', str(new_fee))
            
            await update.message.reply_text(
                f"✅ Withdrawal fee for {coin_symbol} set to {new_fee}\n\n"
                f"{get_powered_by_text()}"
            )
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Invalid fee amount. Please provide a valid number.\n\n"
                f"{get_powered_by_text()}"
            )
    
    async def maintenance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Toggle maintenance mode"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            current_mode = self.db.get_admin_setting('maintenance_mode', 'off')
            await update.message.reply_text(
                f"🔧 **Maintenance mode:** {current_mode.upper()}\n\n"
                f"Usage: `/maintenance <on/off>`\n\n"
                f"{get_powered_by_text()}",
                parse_mode='Markdown'
            )
            return
        
        mode = context.args[0].lower()
        
        if mode not in ['on', 'off']:
            await update.message.reply_text(
                f"❌ Invalid mode. Use 'on' or 'off'.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        self.db.set_admin_setting('maintenance_mode', mode)
        
        status_emoji = "🔧" if mode == 'on' else "✅"
        await update.message.reply_text(
            f"{status_emoji} Maintenance mode turned {mode.upper()}.\n\n"
            f"{get_powered_by_text()}"
        )
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        if not context.args:
            await update.message.reply_text(
                f"Usage: `/broadcast <message>`\n\n"
                f"This will send the message to all bot users.\n\n"
                f"{get_powered_by_text()}"
            )
            return
        
        message = ' '.join(context.args)
        
        # Get all users
        cursor = self.db.connection.cursor()
        cursor.execute('SELECT user_id FROM users')
        users = cursor.fetchall()
        
        broadcast_message = f"📢 **Admin Broadcast**\n\n{message}\n\n{get_powered_by_text()}"
        
        sent_count = 0
        failed_count = 0
        
        for (user_id_to_send,) in users:
            try:
                await context.bot.send_message(
                    chat_id=user_id_to_send,
                    text=broadcast_message,
                    parse_mode='Markdown'
                )
                sent_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {user_id_to_send}: {e}")
                failed_count += 1
        
        await update.message.reply_text(
            f"📢 **Broadcast Complete**\n\n"
            f"✅ Sent: {sent_count}\n"
            f"❌ Failed: {failed_count}\n\n"
            f"{get_powered_by_text()}",
            parse_mode='Markdown'
        )
    
    async def add_coin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add a new coin (placeholder for future implementation)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        await update.message.reply_text(
            f"🚧 **Add Coin Feature**\n\n"
            f"This feature is planned for future implementation.\n"
            f"Currently, new coins must be added manually to the config file.\n\n"
            f"{get_powered_by_text()}",
            parse_mode='Markdown'
        )
    
    async def backup_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Create system backup (placeholder)"""
        user_id = update.effective_user.id
        
        if not self.is_admin(user_id):
            await update.message.reply_text("❌ Admin access required.")
            return
        
        await update.message.reply_text(
            f"💾 **System Backup**\n\n"
            f"This feature is planned for future implementation.\n"
            f"Currently, please backup the database and config files manually.\n\n"
            f"Important files to backup:\n"
            f"• `data/tipbot.db`\n"
            f"• `config/config.json`\n"
            f"• Wallet files for each coin\n\n"
            f"{get_powered_by_text()}",
            parse_mode='Markdown'
        )