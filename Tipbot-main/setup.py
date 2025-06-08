#!/usr/bin/env python3
"""
Community Tipbot - Setup and Configuration Script
Powered By Aegisum EcoSystem
"""

import os
import sys
import json
import secrets
import subprocess
from pathlib import Path
from cryptography.fernet import Fernet

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🤖 Community Tipbot Setup")
    print("Powered By Aegisum EcoSystem")
    print("=" * 60)
    print()

def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    print("✅ Python version check passed")

def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "data",
        "data/wallets",
        "data/backups",
        "admin_dashboard/templates",
        "admin_dashboard/static/css",
        "admin_dashboard/static/js"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")

def install_dependencies():
    """Install Python dependencies"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def generate_encryption_key():
    """Generate encryption key"""
    return Fernet.generate_key().decode()

def generate_secure_password():
    """Generate secure password"""
    return secrets.token_urlsafe(32)

def setup_configuration():
    """Setup configuration file"""
    config_path = "config/config.json"
    example_path = "config/config.example.json"
    
    if os.path.exists(config_path):
        response = input("Configuration file exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("ℹ️ Keeping existing configuration")
            return
    
    # Load example configuration
    with open(example_path, 'r') as f:
        config = json.load(f)
    
    print("\n📝 Configuration Setup")
    print("-" * 30)
    
    # Bot token
    bot_token = input("Enter your Telegram bot token: ").strip()
    if not bot_token:
        print("❌ Bot token is required")
        sys.exit(1)
    config['bot']['token'] = bot_token
    
    # Admin user ID
    admin_id = input("Enter your Telegram user ID: ").strip()
    if admin_id.isdigit():
        config['bot']['admin_users'] = [int(admin_id)]
    else:
        print("❌ Invalid user ID")
        sys.exit(1)
    
    # Generate encryption key
    config['security']['encryption_key'] = generate_encryption_key()
    
    # Generate admin dashboard password
    admin_password = generate_secure_password()
    config['admin_dashboard']['password'] = admin_password
    
    # Generate RPC passwords
    for coin in config['coins']:
        config['coins'][coin]['rpc_password'] = generate_secure_password()
    
    # Save configuration
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print("✅ Configuration created")
    print(f"🔑 Admin dashboard password: {admin_password}")
    print("⚠️  Save this password securely!")

def create_systemd_services():
    """Create systemd service files"""
    user = os.getenv('USER', 'tipbot')
    working_dir = os.getcwd()
    
    # Bot service
    bot_service = f"""[Unit]
Description=Community Tipbot
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}
Environment=PATH={working_dir}/venv/bin
ExecStart={working_dir}/venv/bin/python start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Dashboard service
    dashboard_service = f"""[Unit]
Description=Community Tipbot Admin Dashboard
After=network.target

[Service]
Type=simple
User={user}
WorkingDirectory={working_dir}/admin_dashboard
Environment=PATH={working_dir}/venv/bin
ExecStart={working_dir}/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    # Write service files to temp directory
    with open('/tmp/community-tipbot.service', 'w') as f:
        f.write(bot_service)
    
    with open('/tmp/tipbot-dashboard.service', 'w') as f:
        f.write(dashboard_service)
    
    print("✅ Systemd service files created in /tmp/")
    print("   Copy them to /etc/systemd/system/ as root:")
    print("   sudo cp /tmp/community-tipbot.service /etc/systemd/system/")
    print("   sudo cp /tmp/tipbot-dashboard.service /etc/systemd/system/")

def create_startup_scripts():
    """Create startup scripts"""
    
    # Start script
    start_script = """#!/bin/bash
# Community Tipbot - Start Script

cd "$(dirname "$0")"

echo "🚀 Starting Community Tipbot..."

# Activate virtual environment
source venv/bin/activate

# Start bot
python3 start_bot.py
"""
    
    # Stop script
    stop_script = """#!/bin/bash
# Community Tipbot - Stop Script

echo "🛑 Stopping Community Tipbot..."

# Find and kill bot processes
pkill -f "start_bot.py"
pkill -f "admin_dashboard/app.py"

echo "✅ Bot stopped"
"""
    
    # Status script
    status_script = """#!/bin/bash
# Community Tipbot - Status Script

echo "📊 Community Tipbot Status"
echo "=========================="

# Check bot process
if pgrep -f "start_bot.py" > /dev/null; then
    echo "✅ Bot: Running"
else
    echo "❌ Bot: Not running"
fi

# Check dashboard process
if pgrep -f "admin_dashboard/app.py" > /dev/null; then
    echo "✅ Dashboard: Running"
else
    echo "❌ Dashboard: Not running"
fi

# Check log files
if [ -f "logs/bot.log" ]; then
    echo "📝 Bot log: $(wc -l < logs/bot.log) lines"
else
    echo "📝 Bot log: Not found"
fi

# Check database
if [ -f "data/tipbot.db" ]; then
    echo "💾 Database: Present"
else
    echo "💾 Database: Not found"
fi
"""
    
    # Write scripts
    scripts = {
        'start.sh': start_script,
        'stop.sh': stop_script,
        'status.sh': status_script
    }
    
    for script_name, script_content in scripts.items():
        with open(script_name, 'w') as f:
            f.write(script_content)
        os.chmod(script_name, 0o755)
    
    print("✅ Startup scripts created")

def test_configuration():
    """Test configuration"""
    try:
        # Test config loading
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        
        # Basic validation
        required_fields = ['bot', 'coins', 'features', 'database']
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        if not config['bot'].get('token'):
            print("❌ Bot token is required")
            return False
        
        print("✅ Configuration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def print_next_steps():
    """Print next steps"""
    print("\n🎉 Setup Complete!")
    print("=" * 40)
    print()
    print("Next steps:")
    print("1. Install cryptocurrency wallets:")
    print("   ./scripts/install_wallets.sh")
    print()
    print("2. Start the bot:")
    print("   ./start.sh")
    print()
    print("3. Access admin dashboard:")
    print("   http://your-server-ip:12000")
    print()
    print("4. Test the bot:")
    print("   Send /start to your bot on Telegram")
    print()
    print("📚 Documentation:")
    print("   - QUICKSTART.md - Quick start guide")
    print("   - INSTALL.md - Detailed installation")
    print("   - CONFIG.md - Configuration options")
    print("   - FEATURES.md - Feature overview")
    print()
    print("🔧 Management commands:")
    print("   ./start.sh - Start bot")
    print("   ./stop.sh - Stop bot")
    print("   ./status.sh - Check status")
    print()
    print("Powered By Aegisum EcoSystem")

def main():
    """Main setup function"""
    print_banner()
    
    try:
        check_python_version()
        create_directories()
        install_dependencies()
        setup_configuration()
        create_systemd_services()
        create_startup_scripts()
        
        if test_configuration():
            print_next_steps()
        else:
            print("❌ Setup completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()