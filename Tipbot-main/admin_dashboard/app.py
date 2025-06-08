#!/usr/bin/env python3
"""
Admin Dashboard - Web interface for bot administration
Powered By Aegisum EcoSystem
"""

import json
import os
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import sqlite3
import logging

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import format_amount, format_time_ago, get_powered_by_text

app = Flask(__name__)
app.secret_key = 'change_this_secret_key_in_production'
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdminDashboard:
    def __init__(self, config_path="../config/config.json"):
        self.config = self.load_config(config_path)
        self.db_path = os.path.join("..", self.config['database']['path'])
    
    def load_config(self, config_path):
        """Load configuration"""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def get_db_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_statistics(self):
        """Get dashboard statistics"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            stats['total_users'] = cursor.fetchone()[0]
            
            # Active users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_active > datetime('now', '-1 day')
            ''')
            stats['active_users_24h'] = cursor.fetchone()[0]
            
            # Total tips
            cursor.execute('SELECT COUNT(*) FROM tips')
            stats['total_tips'] = cursor.fetchone()[0]
            
            # Tips today
            cursor.execute('''
                SELECT COUNT(*) FROM tips 
                WHERE date(created_at) = date('now')
            ''')
            stats['tips_today'] = cursor.fetchone()[0]
            
            # Total rain events
            cursor.execute('SELECT COUNT(*) FROM rain')
            stats['total_rain'] = cursor.fetchone()[0]
            
            # Total withdrawals
            cursor.execute('SELECT COUNT(*) FROM withdrawals')
            stats['total_withdrawals'] = cursor.fetchone()[0]
            
            # Pending withdrawals
            cursor.execute('''
                SELECT COUNT(*) FROM withdrawals 
                WHERE status = 'pending'
            ''')
            stats['pending_withdrawals'] = cursor.fetchone()[0]
            
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
                    'total_amount': row[2]
                }
            
            stats['coin_stats'] = coin_stats
            
            conn.close()
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}
    
    def get_recent_activity(self, limit=20):
        """Get recent activity"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            # Recent tips
            cursor.execute('''
                SELECT 'tip' as type, t.created_at, t.coin_symbol, t.amount,
                       u1.username as from_user, u2.username as to_user
                FROM tips t
                LEFT JOIN users u1 ON t.from_user_id = u1.user_id
                LEFT JOIN users u2 ON t.to_user_id = u2.user_id
                ORDER BY t.created_at DESC
                LIMIT ?
            ''', (limit,))
            
            activities = []
            for row in cursor.fetchall():
                activities.append(dict(row))
            
            conn.close()
            return activities
            
        except Exception as e:
            logger.error(f"Failed to get recent activity: {e}")
            return []
    
    def get_user_list(self, page=1, per_page=50):
        """Get paginated user list"""
        try:
            conn = self.get_db_connection()
            cursor = conn.cursor()
            
            offset = (page - 1) * per_page
            
            cursor.execute('''
                SELECT user_id, username, created_at, last_active,
                       (SELECT COUNT(*) FROM tips WHERE from_user_id = users.user_id) as tips_sent,
                       (SELECT COUNT(*) FROM tips WHERE to_user_id = users.user_id) as tips_received
                FROM users
                ORDER BY last_active DESC
                LIMIT ? OFFSET ?
            ''', (per_page, offset))
            
            users = [dict(row) for row in cursor.fetchall()]
            
            # Get total count
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'users': users,
                'total': total_users,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_users + per_page - 1) // per_page
            }
            
        except Exception as e:
            logger.error(f"Failed to get user list: {e}")
            return {'users': [], 'total': 0, 'page': 1, 'per_page': per_page, 'total_pages': 0}

dashboard = AdminDashboard()

@app.route('/')
def index():
    """Dashboard home page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    stats = dashboard.get_statistics()
    recent_activity = dashboard.get_recent_activity()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_activity=recent_activity,
                         config=dashboard.config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_config = dashboard.config.get('admin_dashboard', {})
        correct_username = admin_config.get('username', 'admin')
        correct_password = admin_config.get('password', 'change_this_password')
        
        if username == correct_username and password == correct_password:
            session['authenticated'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.pop('authenticated', None)
    flash('Successfully logged out!', 'info')
    return redirect(url_for('login'))

@app.route('/users')
def users():
    """Users management page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    page = request.args.get('page', 1, type=int)
    user_data = dashboard.get_user_list(page=page)
    
    return render_template('users.html', user_data=user_data)

@app.route('/settings')
def settings():
    """Settings page"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    return render_template('settings.html', config=dashboard.config)

@app.route('/api/stats')
def api_stats():
    """API endpoint for statistics"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    return jsonify(dashboard.get_statistics())

@app.route('/api/activity')
def api_activity():
    """API endpoint for recent activity"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    limit = request.args.get('limit', 20, type=int)
    return jsonify(dashboard.get_recent_activity(limit))

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API endpoint for configuration"""
    if not session.get('authenticated'):
        return jsonify({'error': 'Not authenticated'}), 401
    
    if request.method == 'GET':
        return jsonify(dashboard.config)
    
    elif request.method == 'POST':
        try:
            # Update configuration (simplified)
            new_config = request.json
            
            # Save to file
            config_path = "../config/config.json"
            with open(config_path, 'w') as f:
                json.dump(new_config, f, indent=2)
            
            dashboard.config = new_config
            
            return jsonify({'success': True, 'message': 'Configuration updated'})
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory and basic templates
    os.makedirs('templates', exist_ok=True)
    
    # Get configuration
    admin_config = dashboard.config.get('admin_dashboard', {})
    host = admin_config.get('host', '0.0.0.0')
    port = admin_config.get('port', 12000)
    
    app.run(host=host, port=port, debug=True)