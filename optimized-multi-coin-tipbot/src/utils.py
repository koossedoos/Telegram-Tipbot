#!/usr/bin/env python3
"""
Utilities - Helper functions and utilities
Powered By Aegisum EcoSystem
"""

import re
import hashlib
import secrets
from typing import Optional
from decimal import Decimal, ROUND_DOWN

def format_amount(amount: float, decimals: int = 8) -> str:
    """Format amount with proper decimal places"""
    try:
        # Use Decimal for precise formatting
        decimal_amount = Decimal(str(amount))
        
        # Round down to specified decimal places
        factor = Decimal('10') ** decimals
        rounded_amount = decimal_amount.quantize(Decimal('1') / factor, rounding=ROUND_DOWN)
        
        # Format as string and remove trailing zeros
        formatted = f"{rounded_amount:.{decimals}f}".rstrip('0').rstrip('.')
        
        # Ensure at least one decimal place for small amounts
        if '.' not in formatted and amount < 1:
            formatted += '.0'
        
        return formatted
        
    except Exception:
        # Fallback to simple formatting
        return f"{amount:.{decimals}f}".rstrip('0').rstrip('.')

def validate_address(address: str, coin_symbol: str) -> bool:
    """Validate cryptocurrency address format"""
    if not address or len(address) < 20:
        return False
    
    # Basic validation patterns for different coins
    patterns = {
        'AEGS': r'^[A-Za-z0-9]{25,34}$',  # Aegisum addresses
        'SHIC': r'^[A-Za-z0-9]{25,34}$',  # ShibaCoin addresses  
        'PEPE': r'^[A-Za-z0-9]{25,34}$',  # PepeCoin addresses
        'ADVC': r'^[A-Za-z0-9]{25,34}$',  # AdvCoin addresses
    }
    
    pattern = patterns.get(coin_symbol.upper())
    if not pattern:
        # Generic validation for unknown coins
        pattern = r'^[A-Za-z0-9]{20,50}$'
    
    return bool(re.match(pattern, address))

def validate_amount(amount_str: str, min_amount: float = 0.00000001, max_amount: float = 1000000000) -> Optional[float]:
    """Validate and parse amount string"""
    try:
        amount = float(amount_str)
        
        if amount < min_amount:
            return None
        
        if amount > max_amount:
            return None
        
        # Check for reasonable decimal places (max 8)
        decimal_places = len(amount_str.split('.')[-1]) if '.' in amount_str else 0
        if decimal_places > 8:
            return None
        
        return amount
        
    except (ValueError, TypeError):
        return None

def validate_username(username: str) -> bool:
    """Validate Telegram username format"""
    if not username:
        return False
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Telegram username rules: 5-32 characters, alphanumeric + underscores
    pattern = r'^[a-zA-Z0-9_]{5,32}$'
    return bool(re.match(pattern, username))

def generate_secure_key(length: int = 32) -> str:
    """Generate a secure random key"""
    return secrets.token_hex(length)

def hash_string(text: str, salt: str = "") -> str:
    """Hash a string with optional salt"""
    combined = text + salt
    return hashlib.sha256(combined.encode()).hexdigest()

def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_powered_by_text() -> str:
    """Get the 'Powered By Aegisum EcoSystem' text"""
    return "_Powered By Aegisum EcoSystem_"

def format_time_ago(timestamp) -> str:
    """Format timestamp as 'time ago' string"""
    from datetime import datetime, timezone
    
    try:
        if isinstance(timestamp, str):
            # Parse ISO format timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        elif isinstance(timestamp, (int, float)):
            # Unix timestamp
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        else:
            dt = timestamp
        
        now = datetime.now(timezone.utc)
        diff = now - dt.replace(tzinfo=timezone.utc)
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return f"{seconds}s ago"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}m ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours}h ago"
        else:
            days = seconds // 86400
            return f"{days}d ago"
            
    except Exception:
        return "unknown"

def format_large_number(number: float) -> str:
    """Format large numbers with K, M, B suffixes"""
    try:
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.2f}K"
        else:
            return str(number)
    except Exception:
        return str(number)

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
    
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    # Limit length
    return text[:1000]

def parse_coin_amount(amount_str: str, coin_symbol: str, coin_config: dict) -> Optional[float]:
    """Parse coin amount string with validation"""
    try:
        amount = float(amount_str)
        
        # Check minimum amount
        min_amount = coin_config.get('min_amount', 0.00000001)
        if amount < min_amount:
            return None
        
        # Check maximum amount  
        max_amount = coin_config.get('max_amount', 1000000000)
        if amount > max_amount:
            return None
        
        # Check decimal places
        decimals = coin_config.get('decimals', 8)
        decimal_places = len(amount_str.split('.')[-1]) if '.' in amount_str else 0
        if decimal_places > decimals:
            return None
        
        return amount
        
    except (ValueError, TypeError):
        return None

def create_transaction_id(prefix: str = "tx") -> str:
    """Create a unique transaction ID"""
    import time
    timestamp = int(time.time() * 1000)  # milliseconds
    random_part = secrets.token_hex(8)
    return f"{prefix}_{timestamp}_{random_part}"

def validate_tx_id(tx_id: str) -> bool:
    """Validate transaction ID format"""
    if not tx_id:
        return False
    
    # Basic validation - should be alphanumeric with possible dashes/underscores
    pattern = r'^[a-zA-Z0-9_-]{10,100}$'
    return bool(re.match(pattern, tx_id))

def format_percentage(value: float, decimals: int = 2) -> str:
    """Format percentage value"""
    try:
        return f"{value:.{decimals}f}%"
    except Exception:
        return "0.00%"

def calculate_fee(amount: float, fee_rate: float, min_fee: float = 0, max_fee: float = None) -> float:
    """Calculate transaction fee"""
    try:
        fee = amount * fee_rate
        
        if fee < min_fee:
            fee = min_fee
        
        if max_fee and fee > max_fee:
            fee = max_fee
        
        return fee
        
    except Exception:
        return min_fee

def is_valid_chat_id(chat_id) -> bool:
    """Validate Telegram chat ID"""
    try:
        chat_id = int(chat_id)
        # Telegram chat IDs are typically negative for groups/channels
        # and positive for private chats
        return abs(chat_id) > 0
    except (ValueError, TypeError):
        return False

def escape_markdown(text: str) -> str:
    """Escape special characters for Telegram Markdown"""
    if not text:
        return ""
    
    # Characters that need escaping in Telegram Markdown
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    
    for char in escape_chars:
        text = text.replace(char, f'\\{char}')
    
    return text

def format_coin_list(coins: list, enabled_only: bool = True, coin_config: dict = None) -> str:
    """Format list of coins for display"""
    if not coins:
        return "None"
    
    if coin_config and enabled_only:
        coins = [coin for coin in coins if coin_config.get(coin, {}).get('enabled', False)]
    
    return ', '.join(sorted(coins))

def validate_config(config: dict) -> list:
    """Validate configuration and return list of errors"""
    errors = []
    
    # Check required sections
    required_sections = ['bot', 'coins', 'features', 'database']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Check bot configuration
    if 'bot' in config:
        bot_config = config['bot']
        if not bot_config.get('token'):
            errors.append("Bot token is required")
        
        if not isinstance(bot_config.get('admin_users', []), list):
            errors.append("admin_users must be a list")
    
    # Check coin configurations
    if 'coins' in config:
        for coin_symbol, coin_config in config['coins'].items():
            if not coin_config.get('cli_path'):
                errors.append(f"CLI path required for coin {coin_symbol}")
            
            if not isinstance(coin_config.get('decimals'), int):
                errors.append(f"Decimals must be integer for coin {coin_symbol}")
    
    return errors

def get_file_size(file_path: str) -> int:
    """Get file size in bytes"""
    try:
        import os
        return os.path.getsize(file_path)
    except Exception:
        return 0

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    try:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        return "Unknown"