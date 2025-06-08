#!/usr/bin/env python3
"""
Database Manager - Handles all database operations
Powered By Aegisum EcoSystem
"""

import sqlite3
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
    
    async def initialize(self):
        """Initialize database and create tables"""
        try:
            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            
            await self._create_tables()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def _create_tables(self):
        """Create all necessary database tables"""
        cursor = self.connection.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin BOOLEAN DEFAULT FALSE,
                backup_created BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # User addresses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_addresses (
                user_id INTEGER,
                coin_symbol TEXT,
                address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, coin_symbol),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Tips table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                coin_symbol TEXT,
                amount REAL,
                tx_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                FOREIGN KEY (to_user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Rain table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rain (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                chat_id INTEGER,
                coin_symbol TEXT,
                total_amount REAL,
                recipient_count INTEGER,
                rain_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (user_id)
            )
        ''')
        
        # Airdrops table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER,
                chat_id INTEGER,
                coin_symbol TEXT,
                total_amount REAL,
                duration_minutes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ends_at TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE,
                participant_count INTEGER DEFAULT 0,
                FOREIGN KEY (creator_id) REFERENCES users (user_id)
            )
        ''')
        
        # Airdrop participants table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrop_participants (
                airdrop_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (airdrop_id, user_id),
                FOREIGN KEY (airdrop_id) REFERENCES airdrops (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Withdrawals table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_symbol TEXT,
                amount REAL,
                address TEXT,
                tx_id TEXT,
                fee REAL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Deposits table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                coin_symbol TEXT,
                amount REAL,
                address TEXT,
                tx_id TEXT,
                confirmations INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # User activity table (for rain eligibility)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER,
                chat_id INTEGER,
                last_message TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_count INTEGER DEFAULT 1,
                PRIMARY KEY (user_id, chat_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Admin settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stat_type TEXT,
                coin_symbol TEXT,
                value REAL,
                date DATE DEFAULT (date('now')),
                UNIQUE(stat_type, coin_symbol, date)
            )
        ''')
        
        self.connection.commit()
    
    def create_user(self, user_id: int, username: str) -> bool:
        """Create a new user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO users (user_id, username)
                VALUES (?, ?)
            ''', (user_id, username))
            
            self.connection.commit()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Get user by username"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            
            row = cursor.fetchone()
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    def update_user_activity(self, user_id: int, chat_id: int):
        """Update user activity for rain eligibility"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_activity (user_id, chat_id, last_message, message_count)
                VALUES (?, ?, CURRENT_TIMESTAMP, 
                    COALESCE((SELECT message_count FROM user_activity WHERE user_id = ? AND chat_id = ?), 0) + 1)
            ''', (user_id, chat_id, user_id, chat_id))
            
            # Also update last_active in users table
            cursor.execute('''
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?
            ''', (user_id,))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to update user activity for {user_id}: {e}")
    
    def store_user_address(self, user_id: int, coin_symbol: str, address: str):
        """Store user's address for a coin"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_addresses (user_id, coin_symbol, address)
                VALUES (?, ?, ?)
            ''', (user_id, coin_symbol, address))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to store address for user {user_id}: {e}")
    
    def get_user_address(self, user_id: int, coin_symbol: str) -> Optional[str]:
        """Get user's address for a coin"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT address FROM user_addresses 
                WHERE user_id = ? AND coin_symbol = ?
            ''', (user_id, coin_symbol))
            
            row = cursor.fetchone()
            return row[0] if row else None
            
        except Exception as e:
            logger.error(f"Failed to get address for user {user_id}: {e}")
            return None
    
    def record_tip(self, from_user_id: int, to_user_id: int, coin_symbol: str, amount: float, tx_id: str):
        """Record a tip transaction"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO tips (from_user_id, to_user_id, coin_symbol, amount, tx_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (from_user_id, to_user_id, coin_symbol, amount, tx_id))
            
            self.connection.commit()
            
            # Update statistics
            self._update_statistics('tips_sent', coin_symbol, amount)
            
        except Exception as e:
            logger.error(f"Failed to record tip: {e}")
    
    def record_rain(self, sender_id: int, chat_id: int, coin_symbol: str, total_amount: float, recipient_count: int, rain_id: str):
        """Record a rain event"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO rain (sender_id, chat_id, coin_symbol, total_amount, recipient_count, rain_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (sender_id, chat_id, coin_symbol, total_amount, recipient_count, rain_id))
            
            self.connection.commit()
            
            # Update statistics
            self._update_statistics('rain_sent', coin_symbol, total_amount)
            
        except Exception as e:
            logger.error(f"Failed to record rain: {e}")
    
    def record_withdrawal(self, user_id: int, coin_symbol: str, amount: float, address: str, tx_id: str, fee: float):
        """Record a withdrawal"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO withdrawals (user_id, coin_symbol, amount, address, tx_id, fee)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, coin_symbol, amount, address, tx_id, fee))
            
            self.connection.commit()
            
            # Update statistics
            self._update_statistics('withdrawals', coin_symbol, amount)
            
        except Exception as e:
            logger.error(f"Failed to record withdrawal: {e}")
    
    def record_deposit(self, user_id: int, coin_symbol: str, amount: float, address: str, tx_id: str, confirmations: int = 0):
        """Record a deposit"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO deposits (user_id, coin_symbol, amount, address, tx_id, confirmations)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, coin_symbol, amount, address, tx_id, confirmations))
            
            self.connection.commit()
            
            # Update statistics if confirmed
            if confirmations > 0:
                self._update_statistics('deposits', coin_symbol, amount)
            
        except Exception as e:
            logger.error(f"Failed to record deposit: {e}")
    
    def get_recent_active_users(self, chat_id: int, hours: int = 24) -> List[Dict]:
        """Get users active in the last N hours"""
        try:
            cursor = self.connection.cursor()
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT u.user_id, u.username, ua.last_message, ua.message_count
                FROM user_activity ua
                JOIN users u ON ua.user_id = u.user_id
                WHERE ua.chat_id = ? AND ua.last_message > ?
                ORDER BY ua.last_message DESC
            ''', (chat_id, cutoff_time))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get recent active users: {e}")
            return []
    
    def get_user_tips(self, user_id: int, limit: int = 10) -> List[Dict]:
        """Get user's tip history"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT t.*, 
                       u1.username as from_username,
                       u2.username as to_username
                FROM tips t
                LEFT JOIN users u1 ON t.from_user_id = u1.user_id
                LEFT JOIN users u2 ON t.to_user_id = u2.user_id
                WHERE t.from_user_id = ? OR t.to_user_id = ?
                ORDER BY t.created_at DESC
                LIMIT ?
            ''', (user_id, user_id, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get user tips: {e}")
            return []
    
    def get_unclaimed_tips(self, user_id: int) -> List[Dict]:
        """Get unclaimed tips for a user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                SELECT t.*, u.username as from_username
                FROM tips t
                JOIN users u ON t.from_user_id = u.user_id
                WHERE t.to_user_id = ? AND t.claimed = FALSE
                ORDER BY t.created_at DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get unclaimed tips: {e}")
            return []
    
    def claim_tips(self, user_id: int) -> int:
        """Mark all tips as claimed for a user"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                UPDATE tips SET claimed = TRUE 
                WHERE to_user_id = ? AND claimed = FALSE
            ''', (user_id,))
            
            self.connection.commit()
            return cursor.rowcount
            
        except Exception as e:
            logger.error(f"Failed to claim tips for user {user_id}: {e}")
            return 0
    
    def get_top_users(self, stat_type: str, coin_symbol: str = None, limit: int = 10) -> List[Dict]:
        """Get top users by various statistics"""
        try:
            cursor = self.connection.cursor()
            
            if stat_type == 'tippers':
                query = '''
                    SELECT u.username, t.coin_symbol, 
                           COUNT(*) as tip_count, 
                           SUM(t.amount) as total_amount
                    FROM tips t
                    JOIN users u ON t.from_user_id = u.user_id
                    WHERE (? IS NULL OR t.coin_symbol = ?)
                    GROUP BY t.from_user_id, t.coin_symbol
                    ORDER BY total_amount DESC
                    LIMIT ?
                '''
                cursor.execute(query, (coin_symbol, coin_symbol, limit))
                
            elif stat_type == 'receivers':
                query = '''
                    SELECT u.username, t.coin_symbol,
                           COUNT(*) as tips_received,
                           SUM(t.amount) as total_received
                    FROM tips t
                    JOIN users u ON t.to_user_id = u.user_id
                    WHERE (? IS NULL OR t.coin_symbol = ?)
                    GROUP BY t.to_user_id, t.coin_symbol
                    ORDER BY total_received DESC
                    LIMIT ?
                '''
                cursor.execute(query, (coin_symbol, coin_symbol, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to get top users: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get global statistics"""
        try:
            cursor = self.connection.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            # Total tips
            cursor.execute('SELECT COUNT(*) FROM tips')
            stats['total_tips'] = cursor.fetchone()[0]
            
            # Total rain events
            cursor.execute('SELECT COUNT(*) FROM rain')
            stats['total_rain'] = cursor.fetchone()[0]
            
            # Total withdrawals
            cursor.execute('SELECT COUNT(*) FROM withdrawals')
            stats['total_withdrawals'] = cursor.fetchone()[0]
            
            # Per-coin statistics
            cursor.execute('''
                SELECT coin_symbol, 
                       COUNT(*) as tip_count,
                       SUM(amount) as total_amount
                FROM tips 
                GROUP BY coin_symbol
            ''')
            
            coin_stats = {}
            for row in cursor.fetchall():
                coin_stats[row[0]] = {
                    'tip_count': row[1],
                    'total_tipped': row[2]
                }
            
            stats['coin_stats'] = coin_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def _update_statistics(self, stat_type: str, coin_symbol: str, value: float):
        """Update daily statistics"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO statistics (stat_type, coin_symbol, value, date)
                VALUES (?, ?, 
                    COALESCE((SELECT value FROM statistics WHERE stat_type = ? AND coin_symbol = ? AND date = date('now')), 0) + ?,
                    date('now'))
            ''', (stat_type, coin_symbol, stat_type, coin_symbol, value))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to update statistics: {e}")
    
    def set_admin_setting(self, key: str, value: str):
        """Set an admin setting"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO admin_settings (key, value)
                VALUES (?, ?)
            ''', (key, value))
            
            self.connection.commit()
            
        except Exception as e:
            logger.error(f"Failed to set admin setting {key}: {e}")
    
    def get_admin_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get an admin setting"""
        try:
            cursor = self.connection.cursor()
            cursor.execute('SELECT value FROM admin_settings WHERE key = ?', (key,))
            
            row = cursor.fetchone()
            return row[0] if row else default
            
        except Exception as e:
            logger.error(f"Failed to get admin setting {key}: {e}")
            return default
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()