#!/usr/bin/env python3
"""
Coin Interface - Handles CLI interactions with different cryptocurrencies
Powered By Aegisum EcoSystem
"""

import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class CoinInterface:
    def __init__(self, config: dict):
        self.config = config
        self.supported_coins = {
            coin: details for coin, details in config['coins'].items() 
            if details.get('enabled', False)
        }
    
    async def execute_cli_command(self, coin_symbol: str, command: List[str]) -> Dict[str, Any]:
        """Execute a CLI command for a specific coin"""
        try:
            if coin_symbol not in self.supported_coins:
                raise ValueError(f"Unsupported coin: {coin_symbol}")
            
            coin_config = self.supported_coins[coin_symbol]
            cli_path = coin_config['cli_path']
            
            # Build full command
            full_command = [cli_path] + command
            
            logger.debug(f"Executing command: {' '.join(full_command)}")
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = {
                'success': process.returncode == 0,
                'returncode': process.returncode,
                'stdout': stdout.decode().strip(),
                'stderr': stderr.decode().strip(),
                'command': ' '.join(full_command)
            }
            
            if not result['success']:
                logger.error(f"CLI command failed: {result['stderr']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute CLI command for {coin_symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': ' '.join(command) if command else 'unknown'
            }
    
    async def get_wallet_info(self, coin_symbol: str) -> Dict[str, Any]:
        """Get wallet information"""
        result = await self.execute_cli_command(coin_symbol, ['getwalletinfo'])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                # Some wallets might return plain text
                return {'raw_output': result['stdout']}
        
        return {'error': result.get('stderr', 'Unknown error')}
    
    async def get_blockchain_info(self, coin_symbol: str) -> Dict[str, Any]:
        """Get blockchain information"""
        result = await self.execute_cli_command(coin_symbol, ['getblockchaininfo'])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return {'raw_output': result['stdout']}
        
        return {'error': result.get('stderr', 'Unknown error')}
    
    async def get_new_address(self, coin_symbol: str, account: str = "") -> Optional[str]:
        """Generate a new address"""
        command = ['getnewaddress']
        if account:
            command.append(account)
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return result['stdout']
        
        logger.error(f"Failed to generate new address for {coin_symbol}: {result.get('stderr')}")
        return None
    
    async def get_balance(self, coin_symbol: str, account: str = "", min_confirmations: int = 1) -> float:
        """Get balance for an account"""
        command = ['getbalance']
        if account:
            command.append(account)
        if min_confirmations != 1:
            command.append(str(min_confirmations))
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            try:
                return float(result['stdout'])
            except ValueError:
                logger.error(f"Invalid balance format for {coin_symbol}: {result['stdout']}")
                return 0.0
        
        # If account doesn't exist, return 0
        if "Account does not exist" in result.get('stderr', ''):
            return 0.0
        
        logger.error(f"Failed to get balance for {coin_symbol}: {result.get('stderr')}")
        return 0.0
    
    async def send_to_address(self, coin_symbol: str, address: str, amount: float, comment: str = "") -> Optional[str]:
        """Send coins to an address"""
        command = ['sendtoaddress', address, str(amount)]
        if comment:
            command.append(comment)
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return result['stdout']  # Transaction ID
        
        logger.error(f"Failed to send {coin_symbol} to {address}: {result.get('stderr')}")
        return None
    
    async def send_from_account(self, coin_symbol: str, from_account: str, to_address: str, amount: float, comment: str = "") -> Optional[str]:
        """Send coins from a specific account"""
        command = ['sendfrom', from_account, to_address, str(amount)]
        if comment:
            command.append(comment)
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return result['stdout']  # Transaction ID
        
        logger.error(f"Failed to send {coin_symbol} from {from_account}: {result.get('stderr')}")
        return None
    
    async def move_coins(self, coin_symbol: str, from_account: str, to_account: str, amount: float, comment: str = "") -> bool:
        """Move coins between accounts (internal transfer)"""
        command = ['move', from_account, to_account, str(amount)]
        if comment:
            command.append(comment)
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return result['stdout'].lower() == 'true'
        
        logger.error(f"Failed to move {coin_symbol} from {from_account} to {to_account}: {result.get('stderr')}")
        return False
    
    async def get_transaction(self, coin_symbol: str, tx_id: str) -> Dict[str, Any]:
        """Get transaction details"""
        result = await self.execute_cli_command(coin_symbol, ['gettransaction', tx_id])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return {'raw_output': result['stdout']}
        
        return {'error': result.get('stderr', 'Unknown error')}
    
    async def list_transactions(self, coin_symbol: str, account: str = "", count: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """List transactions for an account"""
        command = ['listtransactions']
        if account:
            command.append(account)
        command.extend([str(count), str(skip)])
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response for listtransactions: {result['stdout']}")
                return []
        
        # If account doesn't exist, return empty list
        if "Account does not exist" in result.get('stderr', ''):
            return []
        
        logger.error(f"Failed to list transactions for {coin_symbol}: {result.get('stderr')}")
        return []
    
    async def list_unspent(self, coin_symbol: str, min_confirmations: int = 1, max_confirmations: int = 9999999, addresses: List[str] = None) -> List[Dict[str, Any]]:
        """List unspent transaction outputs"""
        command = ['listunspent', str(min_confirmations), str(max_confirmations)]
        if addresses:
            command.append(json.dumps(addresses))
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response for listunspent: {result['stdout']}")
                return []
        
        logger.error(f"Failed to list unspent for {coin_symbol}: {result.get('stderr')}")
        return []
    
    async def validate_address(self, coin_symbol: str, address: str) -> Dict[str, Any]:
        """Validate an address"""
        result = await self.execute_cli_command(coin_symbol, ['validateaddress', address])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return {'raw_output': result['stdout']}
        
        return {'error': result.get('stderr', 'Unknown error')}
    
    async def import_private_key(self, coin_symbol: str, private_key: str, account: str = "", rescan: bool = True) -> bool:
        """Import a private key"""
        command = ['importprivkey', private_key]
        if account:
            command.append(account)
        command.append('true' if rescan else 'false')
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return True
        
        logger.error(f"Failed to import private key for {coin_symbol}: {result.get('stderr')}")
        return False
    
    async def dump_private_key(self, coin_symbol: str, address: str) -> Optional[str]:
        """Export private key for an address"""
        result = await self.execute_cli_command(coin_symbol, ['dumpprivkey', address])
        
        if result['success']:
            return result['stdout']
        
        logger.error(f"Failed to dump private key for {coin_symbol} address {address}: {result.get('stderr')}")
        return None
    
    async def get_network_info(self, coin_symbol: str) -> Dict[str, Any]:
        """Get network information"""
        result = await self.execute_cli_command(coin_symbol, ['getnetworkinfo'])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                return {'raw_output': result['stdout']}
        
        return {'error': result.get('stderr', 'Unknown error')}
    
    async def estimate_fee(self, coin_symbol: str, blocks: int = 6) -> float:
        """Estimate transaction fee"""
        # Try estimatefee first (newer wallets)
        result = await self.execute_cli_command(coin_symbol, ['estimatefee', str(blocks)])
        
        if result['success']:
            try:
                fee = float(result['stdout'])
                if fee > 0:
                    return fee
            except ValueError:
                pass
        
        # Fallback to estimatesmartfee (if available)
        result = await self.execute_cli_command(coin_symbol, ['estimatesmartfee', str(blocks)])
        
        if result['success']:
            try:
                fee_data = json.loads(result['stdout'])
                if 'feerate' in fee_data:
                    return float(fee_data['feerate'])
            except (json.JSONDecodeError, ValueError):
                pass
        
        # Return default network fee from config
        return self.supported_coins[coin_symbol].get('network_fee', 0.0001)
    
    async def send_many(self, coin_symbol: str, from_account: str, recipients: Dict[str, float], comment: str = "") -> Optional[str]:
        """Send to multiple addresses in one transaction"""
        command = ['sendmany', from_account, json.dumps(recipients)]
        if comment:
            command.append(comment)
        
        result = await self.execute_cli_command(coin_symbol, command)
        
        if result['success']:
            return result['stdout']  # Transaction ID
        
        logger.error(f"Failed to send many for {coin_symbol}: {result.get('stderr')}")
        return None
    
    async def get_account_address(self, coin_symbol: str, account: str) -> Optional[str]:
        """Get the current address for an account"""
        result = await self.execute_cli_command(coin_symbol, ['getaccountaddress', account])
        
        if result['success']:
            return result['stdout']
        
        logger.error(f"Failed to get account address for {coin_symbol}: {result.get('stderr')}")
        return None
    
    async def list_accounts(self, coin_symbol: str, min_confirmations: int = 1) -> Dict[str, float]:
        """List all accounts and their balances"""
        result = await self.execute_cli_command(coin_symbol, ['listaccounts', str(min_confirmations)])
        
        if result['success']:
            try:
                return json.loads(result['stdout'])
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response for listaccounts: {result['stdout']}")
                return {}
        
        logger.error(f"Failed to list accounts for {coin_symbol}: {result.get('stderr')}")
        return {}
    
    async def backup_wallet(self, coin_symbol: str, destination: str) -> bool:
        """Backup wallet to file"""
        result = await self.execute_cli_command(coin_symbol, ['backupwallet', destination])
        
        if result['success']:
            return True
        
        logger.error(f"Failed to backup wallet for {coin_symbol}: {result.get('stderr')}")
        return False
    
    async def check_daemon_status(self, coin_symbol: str) -> bool:
        """Check if the daemon is running and responsive"""
        try:
            result = await self.execute_cli_command(coin_symbol, ['getblockcount'])
            return result['success']
        except Exception as e:
            logger.error(f"Failed to check daemon status for {coin_symbol}: {e}")
            return False
    
    def get_coin_config(self, coin_symbol: str) -> Dict[str, Any]:
        """Get configuration for a specific coin"""
        return self.supported_coins.get(coin_symbol, {})
    
    def get_supported_coins(self) -> List[str]:
        """Get list of supported coin symbols"""
        return list(self.supported_coins.keys())
    
    def is_coin_enabled(self, coin_symbol: str) -> bool:
        """Check if a coin is enabled"""
        return coin_symbol in self.supported_coins