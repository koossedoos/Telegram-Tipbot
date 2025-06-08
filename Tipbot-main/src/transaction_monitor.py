#!/usr/bin/env python3
"""
Transaction Monitor - Monitors blockchain transactions and sends notifications
Powered By Aegisum EcoSystem
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional
from telegram import Bot
from telegram.error import TelegramError

from utils import format_amount, get_powered_by_text

logger = logging.getLogger(__name__)

class TransactionMonitor:
    def __init__(self, config: dict, database, coin_interface):
        self.config = config
        self.db = database
        self.coin_interface = coin_interface
        self.bot = None
        self.monitoring = False
        
        # Track processed transactions to avoid duplicates
        self.processed_deposits = set()
        self.processed_withdrawals = set()
        
        # Monitoring intervals
        self.deposit_check_interval = 30  # seconds
        self.withdrawal_check_interval = 60  # seconds
    
    async def start(self):
        """Start the transaction monitoring service"""
        try:
            # Initialize Telegram bot
            self.bot = Bot(token=self.config['bot']['token'])
            
            self.monitoring = True
            logger.info("Transaction monitor started")
            
            # Start monitoring tasks
            asyncio.create_task(self._monitor_deposits())
            asyncio.create_task(self._monitor_withdrawals())
            
        except Exception as e:
            logger.error(f"Failed to start transaction monitor: {e}")
            raise
    
    async def stop(self):
        """Stop the transaction monitoring service"""
        self.monitoring = False
        logger.info("Transaction monitor stopped")
    
    async def _monitor_deposits(self):
        """Monitor for new deposits"""
        while self.monitoring:
            try:
                await self._check_all_deposits()
                await asyncio.sleep(self.deposit_check_interval)
            except Exception as e:
                logger.error(f"Error in deposit monitoring: {e}")
                await asyncio.sleep(self.deposit_check_interval)
    
    async def _monitor_withdrawals(self):
        """Monitor withdrawal confirmations"""
        while self.monitoring:
            try:
                await self._check_withdrawal_confirmations()
                await asyncio.sleep(self.withdrawal_check_interval)
            except Exception as e:
                logger.error(f"Error in withdrawal monitoring: {e}")
                await asyncio.sleep(self.withdrawal_check_interval)
    
    async def _check_all_deposits(self):
        """Check for deposits across all users and coins"""
        try:
            # Get all user addresses
            cursor = self.db.connection.cursor()
            cursor.execute('''
                SELECT DISTINCT user_id, coin_symbol, address 
                FROM user_addresses 
                WHERE coin_symbol IN ({})
            '''.format(','.join(['?' for _ in self.coin_interface.get_supported_coins()])),
                      self.coin_interface.get_supported_coins())
            
            user_addresses = cursor.fetchall()
            
            for user_id, coin_symbol, address in user_addresses:
                await self._check_user_deposits(user_id, coin_symbol, address)
                
        except Exception as e:
            logger.error(f"Failed to check all deposits: {e}")
    
    async def _check_user_deposits(self, user_id: int, coin_symbol: str, address: str):
        """Check for deposits for a specific user and coin"""
        try:
            # Get recent transactions for this address
            unspent = await self.coin_interface.list_unspent(
                coin_symbol, 
                min_confirmations=0,
                addresses=[address]
            )
            
            for utxo in unspent:
                tx_id = utxo.get('txid')
                amount = utxo.get('amount', 0)
                confirmations = utxo.get('confirmations', 0)
                
                if not tx_id or amount <= 0:
                    continue
                
                # Check if we've already processed this deposit
                deposit_key = f"{user_id}_{coin_symbol}_{tx_id}"
                
                if deposit_key not in self.processed_deposits:
                    # New deposit detected
                    await self._handle_new_deposit(user_id, coin_symbol, address, tx_id, amount, confirmations)
                    self.processed_deposits.add(deposit_key)
                
                elif confirmations > 0:
                    # Check if deposit needs confirmation update
                    await self._update_deposit_confirmations(user_id, coin_symbol, tx_id, confirmations)
                    
        except Exception as e:
            logger.error(f"Failed to check deposits for user {user_id}, coin {coin_symbol}: {e}")
    
    async def _handle_new_deposit(self, user_id: int, coin_symbol: str, address: str, tx_id: str, amount: float, confirmations: int):
        """Handle a newly detected deposit"""
        try:
            # Record deposit in database
            self.db.record_deposit(user_id, coin_symbol, amount, address, tx_id, confirmations)
            
            # Send notification based on confirmation status
            if confirmations == 0:
                await self._send_pending_deposit_notification(user_id, coin_symbol, amount, tx_id)
            else:
                await self._send_confirmed_deposit_notification(user_id, coin_symbol, amount, tx_id, confirmations)
            
            logger.info(f"New deposit detected: {amount} {coin_symbol} for user {user_id}, TX: {tx_id}")
            
        except Exception as e:
            logger.error(f"Failed to handle new deposit: {e}")
    
    async def _update_deposit_confirmations(self, user_id: int, coin_symbol: str, tx_id: str, confirmations: int):
        """Update deposit confirmation count"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get current deposit status
            cursor.execute('''
                SELECT confirmations, status FROM deposits 
                WHERE user_id = ? AND coin_symbol = ? AND tx_id = ?
            ''', (user_id, coin_symbol, tx_id))
            
            result = cursor.fetchone()
            if not result:
                return
            
            old_confirmations, status = result
            min_confirmations = self.config['coins'][coin_symbol]['min_confirmations']
            
            # Update confirmations
            cursor.execute('''
                UPDATE deposits 
                SET confirmations = ?, 
                    status = CASE 
                        WHEN ? >= ? THEN 'confirmed' 
                        ELSE 'pending' 
                    END,
                    confirmed_at = CASE 
                        WHEN ? >= ? AND status != 'confirmed' THEN CURRENT_TIMESTAMP 
                        ELSE confirmed_at 
                    END
                WHERE user_id = ? AND coin_symbol = ? AND tx_id = ?
            ''', (confirmations, confirmations, min_confirmations, 
                  confirmations, min_confirmations, user_id, coin_symbol, tx_id))
            
            self.db.connection.commit()
            
            # Send confirmation notification if just confirmed
            if old_confirmations < min_confirmations and confirmations >= min_confirmations:
                cursor.execute('''
                    SELECT amount FROM deposits 
                    WHERE user_id = ? AND coin_symbol = ? AND tx_id = ?
                ''', (user_id, coin_symbol, tx_id))
                
                amount_result = cursor.fetchone()
                if amount_result:
                    amount = amount_result[0]
                    await self._send_confirmed_deposit_notification(user_id, coin_symbol, amount, tx_id, confirmations)
            
        except Exception as e:
            logger.error(f"Failed to update deposit confirmations: {e}")
    
    async def _check_withdrawal_confirmations(self):
        """Check for withdrawal confirmations"""
        try:
            cursor = self.db.connection.cursor()
            
            # Get pending withdrawals
            cursor.execute('''
                SELECT user_id, coin_symbol, amount, address, tx_id, fee
                FROM withdrawals 
                WHERE status = 'pending'
            ''')
            
            pending_withdrawals = cursor.fetchall()
            
            for user_id, coin_symbol, amount, address, tx_id, fee in pending_withdrawals:
                await self._check_withdrawal_status(user_id, coin_symbol, amount, address, tx_id, fee)
                
        except Exception as e:
            logger.error(f"Failed to check withdrawal confirmations: {e}")
    
    async def _check_withdrawal_status(self, user_id: int, coin_symbol: str, amount: float, address: str, tx_id: str, fee: float):
        """Check the status of a specific withdrawal"""
        try:
            # Get transaction details
            tx_info = await self.coin_interface.get_transaction(coin_symbol, tx_id)
            
            if 'error' in tx_info:
                logger.warning(f"Could not get transaction info for {tx_id}: {tx_info['error']}")
                return
            
            confirmations = tx_info.get('confirmations', 0)
            min_confirmations = self.config['coins'][coin_symbol]['min_confirmations']
            
            if confirmations >= min_confirmations:
                # Mark as confirmed
                cursor = self.db.connection.cursor()
                cursor.execute('''
                    UPDATE withdrawals 
                    SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND coin_symbol = ? AND tx_id = ?
                ''', (user_id, coin_symbol, tx_id))
                
                self.db.connection.commit()
                
                # Send confirmation notification
                await self._send_confirmed_withdrawal_notification(user_id, coin_symbol, amount, address, tx_id, confirmations)
                
                logger.info(f"Withdrawal confirmed: {amount} {coin_symbol} for user {user_id}, TX: {tx_id}")
            
        except Exception as e:
            logger.error(f"Failed to check withdrawal status for {tx_id}: {e}")
    
    async def _send_pending_deposit_notification(self, user_id: int, coin_symbol: str, amount: float, tx_id: str):
        """Send pending deposit notification"""
        if not self.config['notifications']['pending_tx']:
            return
        
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"⏳ **Pending Deposit Detected**\n\n"
                f"💰 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"🔗 **TX ID:** `{tx_id}`\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"⚠️ Waiting for confirmations...\n"
                f"You'll receive another notification when confirmed.\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send pending deposit notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending pending deposit notification: {e}")
    
    async def _send_confirmed_deposit_notification(self, user_id: int, coin_symbol: str, amount: float, tx_id: str, confirmations: int):
        """Send confirmed deposit notification"""
        if not self.config['notifications']['confirmed_tx']:
            return
        
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"✅ **Deposit Confirmed!**\n\n"
                f"💰 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"🔗 **TX ID:** `{tx_id}`\n"
                f"✔️ **Confirmations:** {confirmations}\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"💳 Your balance has been updated!\n"
                f"Use /balance to check your current balance.\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send confirmed deposit notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending confirmed deposit notification: {e}")
    
    async def _send_confirmed_withdrawal_notification(self, user_id: int, coin_symbol: str, amount: float, address: str, tx_id: str, confirmations: int):
        """Send confirmed withdrawal notification"""
        if not self.config['notifications']['confirmed_tx']:
            return
        
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"✅ **Withdrawal Confirmed!**\n\n"
                f"💸 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"📍 **To:** `{address}`\n"
                f"🔗 **TX ID:** `{tx_id}`\n"
                f"✔️ **Confirmations:** {confirmations}\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"🎉 Your withdrawal has been successfully processed!\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send confirmed withdrawal notification to user {user_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending confirmed withdrawal notification: {e}")
    
    async def send_tip_notification(self, recipient_id: int, sender_username: str, coin_symbol: str, amount: float, tx_id: str):
        """Send tip received notification"""
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"🎁 **You received a tip!**\n\n"
                f"💰 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"👤 **From:** @{sender_username}\n"
                f"🔗 **TX ID:** `{tx_id}`\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Use /claimtips to claim your tips!\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=recipient_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send tip notification to user {recipient_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending tip notification: {e}")
    
    async def send_rain_notification(self, recipient_id: int, sender_username: str, coin_symbol: str, amount: float):
        """Send rain received notification"""
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"🌧️ **You caught some rain!**\n\n"
                f"💰 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"👤 **From:** @{sender_username}\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Use /claimtips to claim your rain!\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=recipient_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send rain notification to user {recipient_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending rain notification: {e}")
    
    async def send_airdrop_notification(self, recipient_id: int, coin_symbol: str, amount: float, airdrop_id: int):
        """Send airdrop received notification"""
        try:
            decimals = self.config['coins'][coin_symbol]['decimals']
            formatted_amount = format_amount(amount, decimals)
            
            message = (
                f"🪂 **Airdrop Received!**\n\n"
                f"💰 **Amount:** {formatted_amount} {coin_symbol}\n"
                f"🆔 **Airdrop ID:** #{airdrop_id}\n"
                f"⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Your airdrop has been automatically added to your balance!\n\n"
                f"{get_powered_by_text()}"
            )
            
            await self.bot.send_message(
                chat_id=recipient_id,
                text=message,
                parse_mode='Markdown'
            )
            
        except TelegramError as e:
            logger.warning(f"Failed to send airdrop notification to user {recipient_id}: {e}")
        except Exception as e:
            logger.error(f"Error sending airdrop notification: {e}")