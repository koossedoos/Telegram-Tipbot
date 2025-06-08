#!/usr/bin/env python3
"""
Community Tipbot Configuration Helper
Powered By Aegisum EcoSystem
"""

import json
import getpass
import sys

def load_config():
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def save_config(config):
    try:
        with open('config/config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration saved!")
    except Exception as e:
        print(f"❌ Error saving config: {e}")

def main():
    print("🤖 Community Tipbot Configuration Helper")
    print("=========================================")
    
    config = load_config()
    
    # Bot token
    current_token = config['bot'].get('token', 'YOUR_BOT_TOKEN_HERE')
    if current_token == 'YOUR_BOT_TOKEN_HERE':
        print("\n📱 Telegram Bot Configuration")
        token = input("Enter your Telegram bot token: ").strip()
        if token:
            config['bot']['token'] = token
    
    # Admin user
    print("\n👤 Admin User Configuration")
    admin_id = input("Enter your Telegram user ID (numeric): ").strip()
    if admin_id.isdigit():
        config['bot']['admin_users'] = [int(admin_id)]
    
    # Dashboard password
    print("\n🔐 Admin Dashboard Configuration")
    dashboard_password = getpass.getpass("Enter admin dashboard password: ").strip()
    if dashboard_password:
        config['admin_dashboard']['password'] = dashboard_password
    
    # Coin RPC passwords
    print("\n💰 Coin RPC Configuration")
    for coin_symbol, coin_config in config['coins'].items():
        current_password = coin_config.get('rpc_password', 'your_rpc_password')
        if current_password == 'your_rpc_password':
            password = getpass.getpass(f"Enter RPC password for {coin_symbol}: ").strip()
            if password:
                config['coins'][coin_symbol]['rpc_password'] = password
    
    save_config(config)
    
    print("\n✅ Configuration complete!")
    print("\nNext steps:")
    print("1. Install and configure wallet daemons")
    print("2. Start wallet daemons")
    print("3. Start the bot: ./manage_bot.sh start")
    print("4. Access dashboard: http://localhost:12000")
    print("\nPowered By Aegisum EcoSystem")

if __name__ == "__main__":
    main()