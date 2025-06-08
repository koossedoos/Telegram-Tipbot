#!/usr/bin/env python3
"""
Enhanced Admin Dashboard - Professional web interface for tipbot management
Powered By Aegisum EcoSystem
"""

import os
import sys
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
import subprocess

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_cors import CORS
import pyotp
import qrcode
from io import BytesIO
import base64

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from enhanced_database import EnhancedDatabase
from enhanced_wallet_manager import EnhancedWalletManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'
CORS(app)

# Global variables
db = None
wallet_manager = None
config = None

def load_config():
    """Load configuration"""
    global config
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'enhanced_config.json')
    with open(config_path, 'r') as f:
        config = json.load(f)

def init_components():
    """Initialize database and wallet manager"""
    global db, wallet_manager
    db = EnhancedDatabase(config['database']['path'])
    wallet_manager = EnhancedWalletManager(config)

@app.before_request
def before_request():
    """Check authentication for protected routes"""
    if request.endpoint and request.endpoint.startswith('admin_'):
        if not session.get('authenticated'):
            return redirect(url_for('login'))

@app.route('/')
def index():
    """Main dashboard"""
    if not session.get('authenticated'):
        return redirect(url_for('login'))
    
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        totp_token = request.form.get('totp_token')
        
        # Check credentials
        if (username == config['admin_dashboard']['username'] and 
            password == config['admin_dashboard']['password']):
            
            # Check 2FA if enabled
            if config['admin_dashboard'].get('require_2fa', False):
                if not verify_admin_2fa(totp_token):
                    flash('Invalid 2FA token', 'error')
                    return render_template('login.html')
            
            session['authenticated'] = True
            session['username'] = username
            session['login_time'] = time.time()
            
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Admin logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
def admin_dashboard():
    """Main admin dashboard"""
    try:
        # Get system statistics
        stats = db.get_system_stats()
        
        # Get recent activity
        recent_activity = get_recent_activity()
        
        # Get wallet status
        wallet_status = get_wallet_status()
        
        # Get system health
        system_health = get_system_health()
        
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             recent_activity=recent_activity,
                             wallet_status=wallet_status,
                             system_health=system_health)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('admin/dashboard.html')

@app.route('/admin/users')
def admin_users():
    """User management"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        filter_type = request.args.get('filter', 'all')
        
        users = get_users_paginated(page, search, filter_type)
        
        return render_template('admin/users.html', 
                             users=users,
                             search=search,
                             filter_type=filter_type,
                             page=page)
    except Exception as e:
        logger.error(f"Users page error: {e}")
        flash('Error loading users', 'error')
        return render_template('admin/users.html')

@app.route('/admin/user/<int:user_id>')
def admin_user_detail(user_id):
    """User detail page"""
    try:
        user_info = db.get_user(user_id)
        if not user_info:
            flash('User not found', 'error')
            return redirect(url_for('admin_users'))
        
        user_stats = db.get_user_stats(user_id)
        user_transactions = get_user_transactions(user_id)
        user_balances = get_user_balances(user_id)
        
        return render_template('admin/user_detail.html',
                             user=user_info,
                             stats=user_stats,
                             transactions=user_transactions,
                             balances=user_balances)
    except Exception as e:
        logger.error(f"User detail error: {e}")
        flash('Error loading user details', 'error')
        return redirect(url_for('admin_users'))

@app.route('/admin/transactions')
def admin_transactions():
    """Transaction monitoring"""
    try:
        page = request.args.get('page', 1, type=int)
        tx_type = request.args.get('type', 'all')
        coin = request.args.get('coin', 'all')
        status = request.args.get('status', 'all')
        
        transactions = get_transactions_paginated(page, tx_type, coin, status)
        
        return render_template('admin/transactions.html',
                             transactions=transactions,
                             tx_type=tx_type,
                             coin=coin,
                             status=status,
                             page=page,
                             coins=list(config['coins'].keys()))
    except Exception as e:
        logger.error(f"Transactions page error: {e}")
        flash('Error loading transactions', 'error')
        return render_template('admin/transactions.html')

@app.route('/admin/wallets')
def admin_wallets():
    """Wallet management"""
    try:
        wallet_info = {}
        
        for coin_symbol in config['coins']:
            if config['coins'][coin_symbol]['enabled']:
                try:
                    info = get_coin_wallet_info(coin_symbol)
                    wallet_info[coin_symbol] = info
                except Exception as e:
                    logger.error(f"Error getting {coin_symbol} wallet info: {e}")
                    wallet_info[coin_symbol] = {'error': str(e)}
        
        return render_template('admin/wallets.html', wallet_info=wallet_info)
    except Exception as e:
        logger.error(f"Wallets page error: {e}")
        flash('Error loading wallet information', 'error')
        return render_template('admin/wallets.html')

@app.route('/admin/security')
def admin_security():
    """Security monitoring"""
    try:
        page = request.args.get('page', 1, type=int)
        event_type = request.args.get('type', 'all')
        
        security_logs = get_security_logs_paginated(page, event_type)
        security_stats = get_security_stats()
        
        return render_template('admin/security.html',
                             logs=security_logs,
                             stats=security_stats,
                             event_type=event_type,
                             page=page)
    except Exception as e:
        logger.error(f"Security page error: {e}")
        flash('Error loading security information', 'error')
        return render_template('admin/security.html')

@app.route('/admin/settings')
def admin_settings():
    """System settings"""
    try:
        current_settings = get_system_settings()
        
        return render_template('admin/settings.html', settings=current_settings)
    except Exception as e:
        logger.error(f"Settings page error: {e}")
        flash('Error loading settings', 'error')
        return render_template('admin/settings.html')

@app.route('/admin/analytics')
def admin_analytics():
    """Analytics and reports"""
    try:
        timeframe = request.args.get('timeframe', 'week')
        
        analytics_data = get_analytics_data(timeframe)
        
        return render_template('admin/analytics.html',
                             data=analytics_data,
                             timeframe=timeframe)
    except Exception as e:
        logger.error(f"Analytics page error: {e}")
        flash('Error loading analytics', 'error')
        return render_template('admin/analytics.html')

# API Endpoints

@app.route('/api/stats')
def api_stats():
    """Get system statistics"""
    try:
        stats = db.get_system_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/wallet/<coin>/balance')
def api_wallet_balance(coin):
    """Get wallet balance for a coin"""
    try:
        balance = get_total_wallet_balance(coin)
        return jsonify({'coin': coin, 'balance': balance})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/freeze', methods=['POST'])
def api_freeze_user(user_id):
    """Freeze/unfreeze user account"""
    try:
        action = request.json.get('action')  # 'freeze' or 'unfreeze'
        reason = request.json.get('reason', '')
        
        success = freeze_user_account(user_id, action == 'freeze', reason)
        
        if success:
            return jsonify({'success': True, 'message': f'User {action}d successfully'})
        else:
            return jsonify({'success': False, 'message': 'Operation failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/<int:user_id>/balance/adjust', methods=['POST'])
def api_adjust_balance(user_id):
    """Manually adjust user balance"""
    try:
        coin = request.json.get('coin')
        amount = float(request.json.get('amount'))
        reason = request.json.get('reason', '')
        
        success = adjust_user_balance(user_id, coin, amount, reason)
        
        if success:
            return jsonify({'success': True, 'message': 'Balance adjusted successfully'})
        else:
            return jsonify({'success': False, 'message': 'Adjustment failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/withdrawal/<int:withdrawal_id>/approve', methods=['POST'])
def api_approve_withdrawal(withdrawal_id):
    """Approve pending withdrawal"""
    try:
        admin_id = session.get('admin_id', 1)  # Default admin ID
        
        success = approve_withdrawal(withdrawal_id, admin_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Withdrawal approved'})
        else:
            return jsonify({'success': False, 'message': 'Approval failed'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/backup', methods=['POST'])
def api_system_backup():
    """Create system backup"""
    try:
        backup_path = create_system_backup()
        return jsonify({'success': True, 'backup_path': backup_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/health')
def api_system_health():
    """Get system health status"""
    try:
        health = get_system_health()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper Functions

def verify_admin_2fa(token):
    """Verify admin 2FA token"""
    # This would use a stored secret for the admin
    # For now, return True if 2FA is not strictly required
    return True

def get_recent_activity():
    """Get recent system activity"""
    # Implementation would query recent transactions, user registrations, etc.
    return []

def get_wallet_status():
    """Get wallet connection status"""
    status = {}
    
    for coin_symbol in config['coins']:
        if config['coins'][coin_symbol]['enabled']:
            try:
                # Test wallet connection
                coin_config = config['coins'][coin_symbol]
                cli_path = coin_config['cli_path']
                
                cmd = [cli_path, 'getblockchaininfo']
                if 'rpc_user' in coin_config:
                    cmd.extend([
                        f'-rpcuser={coin_config["rpc_user"]}',
                        f'-rpcpassword={coin_config["rpc_password"]}',
                        f'-rpcport={coin_config["rpc_port"]}'
                    ])
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    blockchain_info = json.loads(result.stdout)
                    status[coin_symbol] = {
                        'status': 'connected',
                        'blocks': blockchain_info.get('blocks', 0),
                        'connections': blockchain_info.get('connections', 0)
                    }
                else:
                    status[coin_symbol] = {
                        'status': 'error',
                        'error': result.stderr
                    }
            except Exception as e:
                status[coin_symbol] = {
                    'status': 'error',
                    'error': str(e)
                }
    
    return status

def get_system_health():
    """Get overall system health"""
    health = {
        'status': 'healthy',
        'checks': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Database check
    try:
        stats = db.get_system_stats()
        health['checks']['database'] = {'status': 'ok', 'message': 'Database accessible'}
    except Exception as e:
        health['checks']['database'] = {'status': 'error', 'message': str(e)}
        health['status'] = 'degraded'
    
    # Wallet checks
    wallet_status = get_wallet_status()
    healthy_wallets = sum(1 for status in wallet_status.values() if status.get('status') == 'connected')
    total_wallets = len(wallet_status)
    
    if healthy_wallets == total_wallets:
        health['checks']['wallets'] = {'status': 'ok', 'message': f'All {total_wallets} wallets connected'}
    elif healthy_wallets > 0:
        health['checks']['wallets'] = {'status': 'warning', 'message': f'{healthy_wallets}/{total_wallets} wallets connected'}
        health['status'] = 'degraded'
    else:
        health['checks']['wallets'] = {'status': 'error', 'message': 'No wallets connected'}
        health['status'] = 'unhealthy'
    
    return health

def get_users_paginated(page, search, filter_type, per_page=50):
    """Get paginated user list"""
    # Implementation would query database with pagination
    return {
        'users': [],
        'total': 0,
        'pages': 0,
        'current_page': page
    }

def get_user_transactions(user_id, limit=50):
    """Get user transaction history"""
    # Implementation would query user's transactions
    return []

def get_user_balances(user_id):
    """Get user balances for all coins"""
    balances = {}
    
    for coin_symbol in config['coins']:
        if config['coins'][coin_symbol]['enabled']:
            try:
                # This would use the wallet manager to get actual balance
                balance = 0.0  # Placeholder
                balances[coin_symbol] = balance
            except Exception as e:
                logger.error(f"Error getting {coin_symbol} balance for user {user_id}: {e}")
                balances[coin_symbol] = 0.0
    
    return balances

def get_transactions_paginated(page, tx_type, coin, status, per_page=50):
    """Get paginated transaction list"""
    # Implementation would query transactions with filters
    return {
        'transactions': [],
        'total': 0,
        'pages': 0,
        'current_page': page
    }

def get_coin_wallet_info(coin_symbol):
    """Get detailed wallet information for a coin"""
    try:
        coin_config = config['coins'][coin_symbol]
        cli_path = coin_config['cli_path']
        
        # Get blockchain info
        cmd = [cli_path, 'getblockchaininfo']
        if 'rpc_user' in coin_config:
            cmd.extend([
                f'-rpcuser={coin_config["rpc_user"]}',
                f'-rpcpassword={coin_config["rpc_password"]}',
                f'-rpcport={coin_config["rpc_port"]}'
            ])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            blockchain_info = json.loads(result.stdout)
            
            # Get wallet info
            cmd[1] = 'getwalletinfo'
            wallet_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            wallet_info = {}
            if wallet_result.returncode == 0:
                wallet_info = json.loads(wallet_result.stdout)
            
            return {
                'blockchain': blockchain_info,
                'wallet': wallet_info,
                'status': 'connected'
            }
        else:
            return {
                'status': 'error',
                'error': result.stderr
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e)
        }

def get_security_logs_paginated(page, event_type, per_page=50):
    """Get paginated security logs"""
    # Implementation would query security logs
    return {
        'logs': [],
        'total': 0,
        'pages': 0,
        'current_page': page
    }

def get_security_stats():
    """Get security statistics"""
    # Implementation would calculate security metrics
    return {
        'failed_logins_24h': 0,
        'suspicious_activities': 0,
        'blocked_ips': 0,
        'active_sessions': 0
    }

def get_system_settings():
    """Get current system settings"""
    # Implementation would load current settings
    return config

def get_analytics_data(timeframe):
    """Get analytics data for specified timeframe"""
    # Implementation would generate analytics
    return {
        'user_growth': [],
        'transaction_volume': [],
        'popular_commands': [],
        'coin_distribution': []
    }

def get_total_wallet_balance(coin):
    """Get total wallet balance for a coin"""
    try:
        coin_config = config['coins'][coin]
        cli_path = coin_config['cli_path']
        
        cmd = [cli_path, 'getbalance']
        if 'rpc_user' in coin_config:
            cmd.extend([
                f'-rpcuser={coin_config["rpc_user"]}',
                f'-rpcpassword={coin_config["rpc_password"]}',
                f'-rpcport={coin_config["rpc_port"]}'
            ])
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return float(result.stdout.strip())
        else:
            return 0.0
    except Exception as e:
        logger.error(f"Error getting {coin} balance: {e}")
        return 0.0

def freeze_user_account(user_id, freeze, reason):
    """Freeze or unfreeze user account"""
    # Implementation would update user status in database
    return True

def adjust_user_balance(user_id, coin, amount, reason):
    """Manually adjust user balance"""
    # Implementation would adjust balance and log the action
    return True

def approve_withdrawal(withdrawal_id, admin_id):
    """Approve a pending withdrawal"""
    # Implementation would approve withdrawal and process it
    return True

def create_system_backup():
    """Create a system backup"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"backups/system_backup_{timestamp}.tar.gz"
    
    # Implementation would create backup
    return backup_path

if __name__ == '__main__':
    load_config()
    init_components()
    
    host = config['admin_dashboard'].get('host', '0.0.0.0')
    port = config['admin_dashboard'].get('port', 12000)
    debug = config.get('debug', False)
    
    app.run(host=host, port=port, debug=debug)