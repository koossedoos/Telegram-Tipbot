#!/usr/bin/env python3
"""
Enhanced Database Manager - Professional database operations with advanced features
Powered By Aegisum EcoSystem
"""

import sqlite3
import logging
import os
import time
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import hashlib

logger = logging.getLogger(__name__)

class EnhancedDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_directory_exists()
        self.init_database()
        
    def ensure_directory_exists(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def init_database(self):
        """Initialize database with all required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table with enhanced fields
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_banned BOOLEAN DEFAULT FALSE,
                ban_reason TEXT,
                total_tips_sent INTEGER DEFAULT 0,
                total_tips_received INTEGER DEFAULT 0,
                total_rain_sent INTEGER DEFAULT 0,
                total_rain_received INTEGER DEFAULT 0,
                reputation_score INTEGER DEFAULT 100,
                vip_level INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by INTEGER,
                privacy_settings TEXT DEFAULT '{}',
                notification_settings TEXT DEFAULT '{}',
                FOREIGN KEY (referred_by) REFERENCES users(user_id)
            )
        ''')
        
        # User addresses with enhanced tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_addresses (
                user_id INTEGER,
                coin_symbol TEXT,
                address TEXT NOT NULL,
                label TEXT,
                is_primary BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                total_received REAL DEFAULT 0.0,
                total_sent REAL DEFAULT 0.0,
                PRIMARY KEY (user_id, coin_symbol, address),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Enhanced transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_type TEXT NOT NULL,
                from_user_id INTEGER,
                to_user_id INTEGER,
                coin_symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL DEFAULT 0.0,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confirmed_at TIMESTAMP,
                block_height INTEGER,
                confirmations INTEGER DEFAULT 0,
                memo TEXT,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                FOREIGN KEY (to_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Tips table with enhanced features
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                message TEXT,
                chat_id INTEGER,
                message_id INTEGER,
                is_private BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                claimed_at TIMESTAMP,
                status TEXT DEFAULT 'pending',
                tx_hash TEXT,
                FOREIGN KEY (from_user_id) REFERENCES users(user_id),
                FOREIGN KEY (to_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Rain events
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rain_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                total_amount REAL NOT NULL,
                participants_count INTEGER NOT NULL,
                amount_per_user REAL NOT NULL,
                chat_id INTEGER,
                message_id INTEGER,
                duration_seconds INTEGER DEFAULT 300,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (sender_id) REFERENCES users(user_id)
            )
        ''')
        
        # Rain participants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rain_participants (
                rain_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount_received REAL,
                claimed BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (rain_id, user_id),
                FOREIGN KEY (rain_id) REFERENCES rain_events(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Airdrops
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                creator_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                total_amount REAL NOT NULL,
                amount_per_user REAL NOT NULL,
                max_participants INTEGER,
                requirements TEXT,
                duration_minutes INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ends_at TIMESTAMP,
                status TEXT DEFAULT 'active',
                participants_count INTEGER DEFAULT 0,
                FOREIGN KEY (creator_id) REFERENCES users(user_id)
            )
        ''')
        
        # Airdrop participants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS airdrop_participants (
                airdrop_id INTEGER,
                user_id INTEGER,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amount_received REAL,
                claimed BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (airdrop_id, user_id),
                FOREIGN KEY (airdrop_id) REFERENCES airdrops(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Withdrawals with enhanced tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS withdrawals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                fee REAL NOT NULL,
                to_address TEXT NOT NULL,
                tx_hash TEXT,
                status TEXT DEFAULT 'pending',
                requires_approval BOOLEAN DEFAULT FALSE,
                approved_by INTEGER,
                approved_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                ip_address TEXT,
                two_factor_verified BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (approved_by) REFERENCES users(user_id)
            )
        ''')
        
        # Faucet claims
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faucet_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                amount REAL NOT NULL,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Dice games
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dice_games (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                coin_symbol TEXT NOT NULL,
                bet_amount REAL NOT NULL,
                roll_result INTEGER NOT NULL,
                payout_multiplier REAL NOT NULL,
                winnings REAL NOT NULL,
                net_result REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Community challenges
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                challenge_type TEXT NOT NULL,
                requirements TEXT,
                reward_coin TEXT NOT NULL,
                reward_amount REAL NOT NULL,
                max_participants INTEGER,
                start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_date TIMESTAMP,
                status TEXT DEFAULT 'active',
                created_by INTEGER,
                participants_count INTEGER DEFAULT 0,
                FOREIGN KEY (created_by) REFERENCES users(user_id)
            )
        ''')
        
        # Challenge participants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS challenge_participants (
                challenge_id INTEGER,
                user_id INTEGER,
                progress REAL DEFAULT 0.0,
                completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                reward_claimed BOOLEAN DEFAULT FALSE,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (challenge_id, user_id),
                FOREIGN KEY (challenge_id) REFERENCES challenges(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Security logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                event_type TEXT NOT NULL,
                event_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                risk_score INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Admin actions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                target_user_id INTEGER,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (admin_id) REFERENCES users(user_id),
                FOREIGN KEY (target_user_id) REFERENCES users(user_id)
            )
        ''')
        
        # System settings
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by INTEGER,
                FOREIGN KEY (updated_by) REFERENCES users(user_id)
            )
        ''')
        
        # User sessions for tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # Referral system
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referrals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                referrer_id INTEGER NOT NULL,
                referred_id INTEGER NOT NULL,
                reward_coin TEXT,
                reward_amount REAL,
                reward_claimed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (referrer_id) REFERENCES users(user_id),
                FOREIGN KEY (referred_id) REFERENCES users(user_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(from_user_id, to_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_coin ON transactions(coin_symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tips_users ON tips(from_user_id, to_user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tips_status ON tips(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_withdrawals_user ON withdrawals(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_withdrawals_status ON withdrawals(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_logs_user ON security_logs(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_security_logs_type ON security_logs(event_type)')
        
        conn.commit()
        conn.close()
        
        logger.info("Enhanced database initialized successfully")
    
    def create_user(self, user_id: int, username: str, first_name: str = None, last_name: str = None) -> bool:
        """Create a new user with enhanced fields"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate unique referral code
            referral_code = self._generate_referral_code(user_id)
            
            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, referral_code)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, referral_code))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if success:
                logger.info(f"Created user {user_id} (@{username})")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create user {user_id}: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM users WHERE username = ? AND is_active = TRUE
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            return dict(result) if result else None
            
        except Exception as e:
            logger.error(f"Failed to get user by username {username}: {e}")
            return None
    
    def store_user_address(self, user_id: int, coin_symbol: str, address: str, label: str = None) -> bool:
        """Store user address with enhanced tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_addresses 
                (user_id, coin_symbol, address, label, last_used)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, coin_symbol, address, label))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Stored {coin_symbol} address for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store address for user {user_id}: {e}")
            return False
    
    def get_user_address(self, user_id: int, coin_symbol: str) -> Optional[str]:
        """Get user's primary address for a coin"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT address FROM user_addresses 
                WHERE user_id = ? AND coin_symbol = ? AND is_primary = TRUE
                ORDER BY created_at DESC LIMIT 1
            ''', (user_id, coin_symbol))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Failed to get address for user {user_id}, coin {coin_symbol}: {e}")
            return None
    
    def record_transaction(self, tx_type: str, from_user_id: int = None, to_user_id: int = None,
                          coin_symbol: str = None, amount: float = 0.0, fee: float = 0.0,
                          tx_hash: str = None, memo: str = None, ip_address: str = None) -> int:
        """Record a transaction with enhanced tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transactions 
                (tx_type, from_user_id, to_user_id, coin_symbol, amount, fee, tx_hash, memo, ip_address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (tx_type, from_user_id, to_user_id, coin_symbol, amount, fee, tx_hash, memo, ip_address))
            
            tx_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded {tx_type} transaction: {amount} {coin_symbol}")
            return tx_id
            
        except Exception as e:
            logger.error(f"Failed to record transaction: {e}")
            return 0
    
    def record_tip(self, from_user_id: int, to_user_id: int, coin_symbol: str, amount: float,
                   message: str = None, chat_id: int = None, message_id: int = None,
                   is_private: bool = False) -> int:
        """Record a tip with enhanced features"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO tips 
                (from_user_id, to_user_id, coin_symbol, amount, message, chat_id, message_id, is_private)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (from_user_id, to_user_id, coin_symbol, amount, message, chat_id, message_id, is_private))
            
            tip_id = cursor.lastrowid
            
            # Update user statistics
            cursor.execute('''
                UPDATE users SET total_tips_sent = total_tips_sent + 1 
                WHERE user_id = ?
            ''', (from_user_id,))
            
            cursor.execute('''
                UPDATE users SET total_tips_received = total_tips_received + 1 
                WHERE user_id = ?
            ''', (to_user_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded tip: {amount} {coin_symbol} from {from_user_id} to {to_user_id}")
            return tip_id
            
        except Exception as e:
            logger.error(f"Failed to record tip: {e}")
            return 0
    
    def create_rain_event(self, sender_id: int, coin_symbol: str, total_amount: float,
                         participants_count: int, chat_id: int = None, duration: int = 300) -> int:
        """Create a rain event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            amount_per_user = total_amount / participants_count
            
            cursor.execute('''
                INSERT INTO rain_events 
                (sender_id, coin_symbol, total_amount, participants_count, amount_per_user, 
                 chat_id, duration_seconds)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (sender_id, coin_symbol, total_amount, participants_count, amount_per_user, 
                  chat_id, duration))
            
            rain_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Created rain event: {total_amount} {coin_symbol} for {participants_count} users")
            return rain_id
            
        except Exception as e:
            logger.error(f"Failed to create rain event: {e}")
            return 0
    
    def join_rain(self, rain_id: int, user_id: int) -> bool:
        """Join a rain event"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if rain is still active
            cursor.execute('''
                SELECT status, amount_per_user FROM rain_events 
                WHERE id = ? AND status = 'active'
            ''', (rain_id,))
            
            rain_data = cursor.fetchone()
            if not rain_data:
                conn.close()
                return False
            
            amount_per_user = rain_data[1]
            
            cursor.execute('''
                INSERT OR IGNORE INTO rain_participants 
                (rain_id, user_id, amount_received)
                VALUES (?, ?, ?)
            ''', (rain_id, user_id, amount_per_user))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to join rain {rain_id} for user {user_id}: {e}")
            return False
    
    def record_faucet_claim(self, user_id: int, coin_symbol: str, amount: float, ip_address: str = None) -> bool:
        """Record a faucet claim"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO faucet_claims (user_id, coin_symbol, amount, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (user_id, coin_symbol, amount, ip_address))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded faucet claim: {amount} {coin_symbol} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record faucet claim: {e}")
            return False
    
    def get_last_faucet_claim(self, user_id: int) -> Optional[float]:
        """Get timestamp of last faucet claim"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT MAX(created_at) FROM faucet_claims WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                # Convert timestamp to unix time
                return time.mktime(time.strptime(result[0], '%Y-%m-%d %H:%M:%S'))
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get last faucet claim for user {user_id}: {e}")
            return None
    
    def record_dice_game(self, user_id: int, coin_symbol: str, bet_amount: float,
                        roll_result: int, payout_multiplier: float, winnings: float) -> bool:
        """Record a dice game result"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            net_result = winnings - bet_amount
            
            cursor.execute('''
                INSERT INTO dice_games 
                (user_id, coin_symbol, bet_amount, roll_result, payout_multiplier, winnings, net_result)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, coin_symbol, bet_amount, roll_result, payout_multiplier, winnings, net_result))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded dice game: user {user_id}, roll {roll_result}, net {net_result}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record dice game: {e}")
            return False
    
    def get_leaderboard_data(self, timeframe: str = 'week') -> Dict[str, List[Dict]]:
        """Get leaderboard data for various categories"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate date filter
            if timeframe == 'week':
                date_filter = "datetime('now', '-7 days')"
            elif timeframe == 'month':
                date_filter = "datetime('now', '-30 days')"
            else:
                date_filter = "datetime('now', '-7 days')"
            
            # Top tippers
            cursor.execute(f'''
                SELECT u.username, COUNT(*) as tip_count, SUM(t.amount) as total_amount
                FROM tips t
                JOIN users u ON t.from_user_id = u.user_id
                WHERE t.created_at > {date_filter} AND t.status = 'completed'
                GROUP BY t.from_user_id
                ORDER BY tip_count DESC, total_amount DESC
                LIMIT 10
            ''')
            top_tippers = [dict(row) for row in cursor.fetchall()]
            
            # Rain masters
            cursor.execute(f'''
                SELECT u.username, COUNT(*) as rain_count, SUM(r.total_amount) as total_amount
                FROM rain_events r
                JOIN users u ON r.sender_id = u.user_id
                WHERE r.created_at > {date_filter}
                GROUP BY r.sender_id
                ORDER BY rain_count DESC, total_amount DESC
                LIMIT 10
            ''')
            rain_masters = [dict(row) for row in cursor.fetchall()]
            
            # Most active users
            cursor.execute(f'''
                SELECT u.username, 
                       (u.total_tips_sent + u.total_tips_received + u.total_rain_sent) as activity_score
                FROM users u
                WHERE u.last_active > {date_filter} AND u.is_active = TRUE
                ORDER BY activity_score DESC
                LIMIT 10
            ''')
            most_active = [dict(row) for row in cursor.fetchall()]
            
            # Lucky dice players
            cursor.execute(f'''
                SELECT u.username, SUM(d.net_result) as total_winnings, COUNT(*) as games_played
                FROM dice_games d
                JOIN users u ON d.user_id = u.user_id
                WHERE d.created_at > {date_filter}
                GROUP BY d.user_id
                HAVING total_winnings > 0
                ORDER BY total_winnings DESC
                LIMIT 10
            ''')
            lucky_players = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'top_tippers': top_tippers,
                'rain_masters': rain_masters,
                'most_active': most_active,
                'lucky_players': lucky_players
            }
            
        except Exception as e:
            logger.error(f"Failed to get leaderboard data: {e}")
            return {
                'top_tippers': [],
                'rain_masters': [],
                'most_active': [],
                'lucky_players': []
            }
    
    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Basic user info
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user_info = dict(cursor.fetchone() or {})
            
            # Tip statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as tips_sent,
                    COALESCE(SUM(amount), 0) as total_tipped
                FROM tips 
                WHERE from_user_id = ? AND status = 'completed'
            ''', (user_id,))
            tip_stats = dict(cursor.fetchone() or {})
            
            # Rain statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as rains_sent,
                    COALESCE(SUM(total_amount), 0) as total_rained
                FROM rain_events 
                WHERE sender_id = ?
            ''', (user_id,))
            rain_stats = dict(cursor.fetchone() or {})
            
            # Dice statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as games_played,
                    COALESCE(SUM(net_result), 0) as total_winnings,
                    COALESCE(AVG(net_result), 0) as avg_result
                FROM dice_games 
                WHERE user_id = ?
            ''', (user_id,))
            dice_stats = dict(cursor.fetchone() or {})
            
            # Faucet statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as claims_made,
                    COALESCE(SUM(amount), 0) as total_claimed
                FROM faucet_claims 
                WHERE user_id = ?
            ''', (user_id,))
            faucet_stats = dict(cursor.fetchone() or {})
            
            conn.close()
            
            return {
                'user_info': user_info,
                'tips': tip_stats,
                'rain': rain_stats,
                'dice': dice_stats,
                'faucet': faucet_stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats for {user_id}: {e}")
            return {}
    
    def log_security_event(self, user_id: int, event_type: str, event_data: Dict = None,
                          ip_address: str = None, user_agent: str = None, risk_score: int = 0) -> bool:
        """Log security events"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            event_data_json = json.dumps(event_data) if event_data else None
            
            cursor.execute('''
                INSERT INTO security_logs 
                (user_id, event_type, event_data, ip_address, user_agent, risk_score)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, event_type, event_data_json, ip_address, user_agent, risk_score))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False
    
    def update_user_activity(self, user_id: int) -> bool:
        """Update user's last activity timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update activity for user {user_id}: {e}")
            return False
    
    def _generate_referral_code(self, user_id: int) -> str:
        """Generate unique referral code"""
        base_string = f"tipbot_{user_id}_{int(time.time())}"
        hash_object = hashlib.md5(base_string.encode())
        return hash_object.hexdigest()[:8].upper()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = TRUE')
            stats['total_users'] = cursor.fetchone()[0]
            
            # Total tips
            cursor.execute('SELECT COUNT(*) FROM tips WHERE status = "completed"')
            stats['total_tips'] = cursor.fetchone()[0]
            
            # Total rain events
            cursor.execute('SELECT COUNT(*) FROM rain_events')
            stats['total_rains'] = cursor.fetchone()[0]
            
            # Total dice games
            cursor.execute('SELECT COUNT(*) FROM dice_games')
            stats['total_dice_games'] = cursor.fetchone()[0]
            
            # Total faucet claims
            cursor.execute('SELECT COUNT(*) FROM faucet_claims')
            stats['total_faucet_claims'] = cursor.fetchone()[0]
            
            # Active users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active > datetime('now', '-1 day') AND is_active = TRUE
            ''')
            stats['active_users_24h'] = cursor.fetchone()[0]
            
            conn.close()
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {}
    
    def get_last_faucet_claim(self, user_id: int) -> Optional[float]:
        """Get timestamp of last faucet claim"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp FROM faucet_claims 
                WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT 1
            """, (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error getting last faucet claim: {e}")
            return None
    
    def record_faucet_claim(self, user_id: int):
        """Record a faucet claim"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO faucet_claims (user_id, amount, coin, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, 0.0, "MIXED"))
            
            # Update user stats
            cursor.execute("""
                UPDATE users SET faucet_claims = faucet_claims + 1
                WHERE user_id = ?
            """, (user_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error recording faucet claim: {e}")
    
    def get_user_stats(self, user_id: int) -> dict:
        """Get user statistics for the new bot"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get basic user info
            cursor.execute("""
                SELECT tips_sent, tips_received, rain_participated, 
                       faucet_claims, dice_games, referrals
                FROM users WHERE user_id = ?
            """, (user_id,))
            
            result = cursor.fetchone()
            if not result:
                conn.close()
                return {}
            
            stats = {
                'tips_sent': result[0] or 0,
                'tips_received': result[1] or 0,
                'rain_participated': result[2] or 0,
                'faucet_claims': result[3] or 0,
                'dice_games': result[4] or 0,
                'referrals': result[5] or 0
            }
            
            # Calculate days active
            cursor.execute("""
                SELECT COUNT(DISTINCT DATE(last_active)) FROM users 
                WHERE user_id = ? AND last_active IS NOT NULL
            """, (user_id,))
            result = cursor.fetchone()
            stats['days_active'] = result[0] if result else 0
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {}