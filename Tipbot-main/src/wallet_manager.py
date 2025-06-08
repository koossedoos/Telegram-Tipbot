#!/usr/bin/env python3
"""
Wallet Manager - Handles wallet operations for all supported coins
Powered By Aegisum EcoSystem
"""

import asyncio
import json
import logging
import os
import subprocess
from typing import Dict, List, Optional, Tuple
from cryptography.fernet import Fernet
import sqlite3

logger = logging.getLogger(__name__)

class WalletManager:
    def __init__(self, config: dict):
        self.config = config
        self.wallets_dir = "data/wallets"
        os.makedirs(self.wallets_dir, exist_ok=True)
        
        # Initialize encryption
        self.encryption_key = self.config['security']['encryption_key'].encode()
        if len(self.encryption_key) != 44:  # Fernet key length
            # Generate a new key if not properly set
            self.encryption_key = Fernet.generate_key()
            logger.warning("Generated new encryption key. Update your config!")
        
        self.cipher = Fernet(self.encryption_key)
    
    async def generate_address(self, user_id: int, coin_symbol: str) -> str:
        """Generate a new address for a user and coin"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Generate new address using CLI
            cmd = [cli_path, 'getnewaddress', f'user_{user_id}']
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"CLI error: {stderr.decode()}")
            
            address = stdout.decode().strip()
            
            # Store the address mapping
            await self._store_address_mapping(user_id, coin_symbol, address)
            
            logger.info(f"Generated {coin_symbol} address for user {user_id}: {address}")
            return address
            
        except Exception as e:
            logger.error(f"Failed to generate {coin_symbol} address for user {user_id}: {e}")
            raise
    
    async def get_balance(self, user_id: int, coin_symbol: str) -> float:
        """Get user's balance for a specific coin"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Get balance using CLI
            cmd = [cli_path, 'getbalance', f'user_{user_id}']
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                # If account doesn't exist, return 0
                if "Account does not exist" in stderr.decode():
                    return 0.0
                raise Exception(f"CLI error: {stderr.decode()}")
            
            balance = float(stdout.decode().strip())
            return balance
            
        except Exception as e:
            logger.error(f"Failed to get {coin_symbol} balance for user {user_id}: {e}")
            return 0.0
    
    async def send_tip(self, from_user_id: int, to_user_id: int, coin_symbol: str, amount: float) -> str:
        """Send a tip from one user to another"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Move coins from sender to receiver account
            cmd = [
                cli_path, 'move', 
                f'user_{from_user_id}', 
                f'user_{to_user_id}', 
                str(amount)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"CLI error: {stderr.decode()}")
            
            # Generate a pseudo transaction ID for internal tracking
            tx_id = f"tip_{from_user_id}_{to_user_id}_{coin_symbol}_{int(asyncio.get_event_loop().time())}"
            
            logger.info(f"Tip sent: {amount} {coin_symbol} from user {from_user_id} to user {to_user_id}")
            return tx_id
            
        except Exception as e:
            logger.error(f"Failed to send tip: {e}")
            raise
    
    async def withdraw(self, user_id: int, coin_symbol: str, amount: float, address: str) -> str:
        """Withdraw coins to external address"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Send from user account to external address
            cmd = [
                cli_path, 'sendfrom', 
                f'user_{user_id}', 
                address, 
                str(amount)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"CLI error: {stderr.decode()}")
            
            tx_id = stdout.decode().strip()
            
            logger.info(f"Withdrawal sent: {amount} {coin_symbol} from user {user_id} to {address}, TX: {tx_id}")
            return tx_id
            
        except Exception as e:
            logger.error(f"Failed to process withdrawal: {e}")
            raise
    
    async def process_rain(self, sender_id: int, coin_symbol: str, total_amount: float, recipients: List[dict]) -> str:
        """Process rain distribution to multiple users"""
        try:
            amount_per_user = total_amount / len(recipients)
            
            # Process each rain payment
            for recipient in recipients:
                recipient_id = recipient['user_id']
                await self.send_tip(sender_id, recipient_id, coin_symbol, amount_per_user)
            
            # Generate rain ID for tracking
            rain_id = f"rain_{sender_id}_{coin_symbol}_{int(asyncio.get_event_loop().time())}"
            
            logger.info(f"Rain processed: {total_amount} {coin_symbol} from user {sender_id} to {len(recipients)} recipients")
            return rain_id
            
        except Exception as e:
            logger.error(f"Failed to process rain: {e}")
            raise
    
    async def get_transaction_history(self, user_id: int, coin_symbol: str, limit: int = 10) -> List[dict]:
        """Get transaction history for a user"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Get transactions for user account
            cmd = [cli_path, 'listtransactions', f'user_{user_id}', str(limit)]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                if "Account does not exist" in stderr.decode():
                    return []
                raise Exception(f"CLI error: {stderr.decode()}")
            
            transactions = json.loads(stdout.decode())
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to get transaction history for user {user_id}: {e}")
            return []
    
    async def backup_wallet(self, user_id: int) -> dict:
        """Create encrypted backup of user's wallet"""
        try:
            backup_data = {
                'user_id': user_id,
                'addresses': {},
                'private_keys': {},
                'timestamp': asyncio.get_event_loop().time()
            }
            
            # Get addresses and private keys for all coins
            for coin_symbol in self.config['coins']:
                if self.config['coins'][coin_symbol]['enabled']:
                    try:
                        # Get address
                        address = await self._get_user_address(user_id, coin_symbol)
                        if address:
                            backup_data['addresses'][coin_symbol] = address
                            
                            # Get private key
                            private_key = await self._get_private_key(coin_symbol, address)
                            if private_key:
                                backup_data['private_keys'][coin_symbol] = private_key
                                
                    except Exception as e:
                        logger.warning(f"Failed to backup {coin_symbol} for user {user_id}: {e}")
            
            # Encrypt backup data
            backup_json = json.dumps(backup_data)
            encrypted_backup = self.cipher.encrypt(backup_json.encode())
            
            return {
                'encrypted_data': encrypted_backup.decode(),
                'coins_backed_up': list(backup_data['addresses'].keys())
            }
            
        except Exception as e:
            logger.error(f"Failed to create backup for user {user_id}: {e}")
            raise
    
    async def restore_wallet(self, user_id: int, encrypted_backup: str) -> dict:
        """Restore wallet from encrypted backup"""
        try:
            # Decrypt backup data
            decrypted_data = self.cipher.decrypt(encrypted_backup.encode())
            backup_data = json.loads(decrypted_data.decode())
            
            restored_coins = []
            
            # Restore each coin
            for coin_symbol, private_key in backup_data['private_keys'].items():
                if coin_symbol in self.config['coins'] and self.config['coins'][coin_symbol]['enabled']:
                    try:
                        await self._import_private_key(coin_symbol, private_key, f'user_{user_id}')
                        restored_coins.append(coin_symbol)
                    except Exception as e:
                        logger.warning(f"Failed to restore {coin_symbol} for user {user_id}: {e}")
            
            return {
                'restored_coins': restored_coins,
                'total_coins': len(backup_data['private_keys'])
            }
            
        except Exception as e:
            logger.error(f"Failed to restore wallet for user {user_id}: {e}")
            raise
    
    async def _store_address_mapping(self, user_id: int, coin_symbol: str, address: str):
        """Store address mapping in local database"""
        db_path = "data/address_mappings.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS address_mappings (
                user_id INTEGER,
                coin_symbol TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, coin_symbol)
            )
        ''')
        
        # Insert or update mapping
        cursor.execute('''
            INSERT OR REPLACE INTO address_mappings (user_id, coin_symbol, address)
            VALUES (?, ?, ?)
        ''', (user_id, coin_symbol, address))
        
        conn.commit()
        conn.close()
    
    async def _get_user_address(self, user_id: int, coin_symbol: str) -> Optional[str]:
        """Get user's address for a coin from local database"""
        db_path = "data/address_mappings.db"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT address FROM address_mappings 
                WHERE user_id = ? AND coin_symbol = ?
            ''', (user_id, coin_symbol))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get address for user {user_id}, coin {coin_symbol}: {e}")
            return None
    
    async def _get_private_key(self, coin_symbol: str, address: str) -> Optional[str]:
        """Get private key for an address"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            cmd = [cli_path, 'dumpprivkey', address]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"CLI error: {stderr.decode()}")
            
            private_key = stdout.decode().strip()
            return private_key
            
        except Exception as e:
            logger.error(f"Failed to get private key for {coin_symbol} address {address}: {e}")
            return None
    
    async def _import_private_key(self, coin_symbol: str, private_key: str, account: str):
        """Import private key into wallet"""
        try:
            coin_config = self.config['coins'][coin_symbol]
            cli_path = coin_config['cli_path']
            
            cmd = [cli_path, 'importprivkey', private_key, account]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"CLI error: {stderr.decode()}")
            
            logger.info(f"Imported private key for {coin_symbol} into account {account}")
            
        except Exception as e:
            logger.error(f"Failed to import private key for {coin_symbol}: {e}")
            raise
    
    async def check_deposits(self, user_id: int, coin_symbol: str) -> List[dict]:
        """Check for new deposits for a user"""
        try:
            # Get recent transactions
            transactions = await self.get_transaction_history(user_id, coin_symbol, 50)
            
            # Filter for deposits (received transactions)
            deposits = []
            for tx in transactions:
                if tx.get('category') == 'receive' and tx.get('confirmations', 0) >= 0:
                    deposits.append({
                        'txid': tx.get('txid'),
                        'amount': tx.get('amount'),
                        'confirmations': tx.get('confirmations'),
                        'time': tx.get('time'),
                        'address': tx.get('address')
                    })
            
            return deposits
            
        except Exception as e:
            logger.error(f"Failed to check deposits for user {user_id}: {e}")
            return []