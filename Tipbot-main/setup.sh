#!/bin/bash
# Community Tipbot - Complete Setup Script
# Powered By Aegisum EcoSystem

set -e

echo "🚀 Community Tipbot - Complete Setup Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as the tipbot user."
   exit 1
fi

# Check if Python 3.8+ is available
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    print_error "Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

print_success "Python version check passed: $python_version"

# Create virtual environment
print_status "Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

print_success "Python dependencies installed"

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data wallets config/backup admin_dashboard/static/uploads

# Set proper permissions
chmod 700 data wallets
chmod 755 logs admin_dashboard

print_success "Directories created with proper permissions"

# Copy example config if config doesn't exist
if [ ! -f "config/config.json" ]; then
    print_status "Creating configuration file from example..."
    cp config/config.example.json config/config.json
    print_warning "Please edit config/config.json with your settings!"
else
    print_warning "Configuration file already exists"
fi

# Generate encryption key if needed
if grep -q "GENERATE_RANDOM_KEY_HERE" config/config.json; then
    print_status "Generating encryption key..."
    encryption_key=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    sed -i "s/GENERATE_RANDOM_KEY_HERE/$encryption_key/g" config/config.json
    print_success "Encryption key generated and updated in config"
fi

# Initialize database
print_status "Initializing database..."
python3 -c "
import sys
sys.path.append('src')
from database import Database
import asyncio

async def init_db():
    db = Database('data/tipbot.db')
    await db.initialize()
    print('Database initialized successfully')

asyncio.run(init_db())
"

print_success "Database initialized"

# Create systemd service files
print_status "Creating systemd service files..."

# Bot service
cat > /tmp/community-tipbot.service << EOF
[Unit]
Description=Community Tipbot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python start_bot.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Dashboard service
cat > /tmp/tipbot-dashboard.service << EOF
[Unit]
Description=Community Tipbot Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD/admin_dashboard
Environment=PATH=$PWD/venv/bin
ExecStart=$PWD/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service files created in /tmp/"
print_warning "To install services, run as root:"
print_warning "sudo cp /tmp/community-tipbot.service /etc/systemd/system/"
print_warning "sudo cp /tmp/tipbot-dashboard.service /etc/systemd/system/"
print_warning "sudo systemctl daemon-reload"
print_warning "sudo systemctl enable community-tipbot tipbot-dashboard"

# Create management scripts
print_status "Creating management scripts..."

# Bot management script
cat > manage_bot.sh << 'EOF'
#!/bin/bash
# Community Tipbot Management Script

case "$1" in
    start)
        echo "Starting Community Tipbot..."
        source venv/bin/activate
        python3 start_bot.py
        ;;
    stop)
        echo "Stopping Community Tipbot..."
        pkill -f "python.*start_bot.py"
        ;;
    restart)
        echo "Restarting Community Tipbot..."
        $0 stop
        sleep 2
        $0 start
        ;;
    status)
        if pgrep -f "python.*start_bot.py" > /dev/null; then
            echo "Community Tipbot is running"
        else
            echo "Community Tipbot is not running"
        fi
        ;;
    logs)
        tail -f logs/bot.log
        ;;
    dashboard)
        echo "Starting Admin Dashboard..."
        source venv/bin/activate
        cd admin_dashboard
        python3 app.py
        ;;
    backup)
        echo "Creating backup..."
        backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        cp -r data config "$backup_dir/"
        echo "Backup created: $backup_dir"
        ;;
    update)
        echo "Updating Community Tipbot..."
        git pull
        source venv/bin/activate
        pip install -r requirements.txt
        echo "Update complete. Please restart the bot."
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|dashboard|backup|update}"
        echo
        echo "Commands:"
        echo "  start     - Start the bot"
        echo "  stop      - Stop the bot"
        echo "  restart   - Restart the bot"
        echo "  status    - Check bot status"
        echo "  logs      - View bot logs"
        echo "  dashboard - Start admin dashboard"
        echo "  backup    - Create backup"
        echo "  update    - Update from git"
        exit 1
        ;;
esac
EOF

chmod +x manage_bot.sh
print_success "Bot management script created: ./manage_bot.sh"

# Create configuration helper script
cat > configure_bot.py << 'EOF'
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
EOF

chmod +x configure_bot.py
print_success "Configuration helper created: ./configure_bot.py"

# Create quick start script
cat > quickstart.sh << 'EOF'
#!/bin/bash
# Community Tipbot Quick Start

echo "🚀 Community Tipbot Quick Start"
echo "==============================="

echo "1. Configure the bot..."
python3 configure_bot.py

echo
echo "2. Install wallet daemons..."
echo "Run: bash scripts/install_wallets.sh"

echo
echo "3. Start the bot..."
echo "Run: ./manage_bot.sh start"

echo
echo "4. Access admin dashboard..."
echo "Open: http://localhost:12000"

echo
echo "For full installation guide, see INSTALL.md"
echo "Powered By Aegisum EcoSystem"
EOF

chmod +x quickstart.sh
print_success "Quick start script created: ./quickstart.sh"

# Create README for first-time users
cat > QUICKSTART.md << 'EOF'
# Community Tipbot - Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### 1. Run Setup Script
```bash
bash setup.sh
```

### 2. Configure Bot
```bash
python3 configure_bot.py
```

### 3. Install Wallets
```bash
bash scripts/install_wallets.sh
```

### 4. Start Bot
```bash
./manage_bot.sh start
```

### 5. Access Dashboard
Open: http://localhost:12000

## 📋 Management Commands

```bash
./manage_bot.sh start      # Start bot
./manage_bot.sh stop       # Stop bot
./manage_bot.sh status     # Check status
./manage_bot.sh logs       # View logs
./manage_bot.sh dashboard  # Start dashboard
./manage_bot.sh backup     # Create backup
./manage_bot.sh update     # Update from git
```

## 🔧 Wallet Management

```bash
~/wallets/manage_wallets.sh start   # Start all wallets
~/wallets/manage_wallets.sh stop    # Stop all wallets
~/wallets/manage_wallets.sh status  # Check wallet status
~/wallets/wallet_info.sh            # Detailed wallet info
```

## 📚 Full Documentation

- [INSTALL.md](INSTALL.md) - Complete installation guide
- [CONFIG.md](CONFIG.md) - Configuration options
- [FEATURES.md](FEATURES.md) - Feature documentation

---
*Powered By Aegisum EcoSystem*
EOF

print_success "Quick start guide created: QUICKSTART.md"

# Final setup summary
echo
print_success "🎉 Community Tipbot setup completed!"
echo
print_status "What was installed:"
print_status "✅ Python virtual environment with dependencies"
print_status "✅ Database initialized"
print_status "✅ Configuration files created"
print_status "✅ Management scripts created"
print_status "✅ Systemd service files prepared"
echo
print_warning "Next steps:"
print_warning "1. Configure your bot: python3 configure_bot.py"
print_warning "2. Install wallet daemons: bash scripts/install_wallets.sh"
print_warning "3. Start the bot: ./manage_bot.sh start"
print_warning "4. Access dashboard: http://localhost:12000"
echo
print_status "For detailed instructions, see:"
print_status "📖 INSTALL.md - Complete installation guide"
print_status "🚀 QUICKSTART.md - Quick start guide"
echo
print_status "Powered By Aegisum EcoSystem"