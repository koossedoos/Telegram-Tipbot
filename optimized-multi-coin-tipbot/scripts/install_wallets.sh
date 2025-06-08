#!/bin/bash
# Optimized Multi-Coin Tipbot - Wallet Installation Script
# Only installs: Aegisum, ADVC, ShibaCoin, PepeCoin
# Powered By Aegisum EcoSystem

set -e

echo "🚀 Optimized Multi-Coin Tipbot - Wallet Installation"
echo "===================================================="
echo "Installing wallets for: AEGS, ADVC, SHIC, PEPE"
echo

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

# Create directories
print_status "Creating wallet directories..."
mkdir -p ~/wallets/downloads
mkdir -p ~/wallets/backups
mkdir -p ~/.aegisum ~/.advc ~/.shibacoin ~/.pepecoin

# Function to create wallet configuration
create_wallet_config() {
    local coin_name=$1
    local config_dir=$2
    local rpc_port=$3
    local rpc_user=$4
    
    print_status "Creating $coin_name configuration..."
    
    # Generate random RPC password
    rpc_password=$(openssl rand -base64 32)
    
    cat > "$config_dir/${coin_name,,}.conf" << EOF
# $coin_name Configuration for Tipbot
rpcuser=$rpc_user
rpcpassword=$rpc_password
rpcallowip=127.0.0.1
rpcport=$rpc_port
server=1
daemon=1
txindex=1
listen=1

# Logging
debug=0
printtoconsole=0

# Network
maxconnections=50
timeout=5000

# Memory pool
maxmempool=300

# Fees
mintxfee=0.00001
minrelaytxfee=0.00001

# Wallet
keypool=1000
walletnotify=echo "New transaction: %s" >> ~/wallets/notifications.log
EOF

    print_success "$coin_name configuration created at $config_dir/${coin_name,,}.conf"
    echo "RPC Password for $coin_name: $rpc_password" >> ~/wallets/rpc_passwords.txt
    print_warning "RPC Password saved to ~/wallets/rpc_passwords.txt"
}

# Install wallet configurations
print_status "Creating wallet configurations..."

# AEGS (Aegisum) - Primary coin
create_wallet_config "AEGS" "$HOME/.aegisum" "8332" "aegisumrpc"

# ADVC (AdventureCoin)
create_wallet_config "ADVC" "$HOME/.advc" "8335" "advcrpc"

# SHIC (ShibaCoin)
create_wallet_config "SHIC" "$HOME/.shibacoin" "8333" "shibacoirpc"

# PEPE (PepeCoin)
create_wallet_config "PEPE" "$HOME/.pepecoin" "8334" "pepecoirpc"

# Create systemd service files
print_status "Creating systemd service files..."

create_systemd_service() {
    local coin_name=$1
    local daemon_name=$2
    local cli_name=$3
    
    cat > "/tmp/${coin_name,,}d.service" << EOF
[Unit]
Description=$coin_name Daemon for Tipbot
After=network.target
Wants=network.target

[Service]
Type=forking
User=$USER
Group=$USER
ExecStart=/usr/local/bin/$daemon_name -daemon
ExecStop=/usr/local/bin/$cli_name stop
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=30
TimeoutStopSec=60
TimeoutStartSec=60
KillMode=mixed

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created: /tmp/${coin_name,,}d.service"
}

create_systemd_service "AEGS" "aegisumd" "aegisum-cli"
create_systemd_service "ADVC" "advcd" "advc-cli"
create_systemd_service "SHIC" "shibacoind" "shibacoin-cli"
create_systemd_service "PEPE" "pepecoind" "pepecoin-cli"

# Create optimized wallet management script
print_status "Creating wallet management script..."

cat > ~/wallets/manage_wallets.sh << 'EOF'
#!/bin/bash
# Optimized Wallet Management Script
# Manages: AEGS, ADVC, SHIC, PEPE

COINS=("aegisum" "advc" "shibacoin" "pepecoin")
CLI_NAMES=("aegisum-cli" "advc-cli" "shibacoin-cli" "pepecoin-cli")
DAEMON_NAMES=("aegisumd" "advcd" "shibacoind" "pepecoind")

case "$1" in
    start)
        echo "🚀 Starting all wallet daemons..."
        for i in "${!DAEMON_NAMES[@]}"; do
            echo "Starting ${COINS[$i]}..."
            ${DAEMON_NAMES[$i]} -daemon
            sleep 2
        done
        echo "✅ All daemons started"
        ;;
    stop)
        echo "🛑 Stopping all wallet daemons..."
        for i in "${!CLI_NAMES[@]}"; do
            echo "Stopping ${COINS[$i]}..."
            ${CLI_NAMES[$i]} stop 2>/dev/null || true
        done
        echo "✅ All daemons stopped"
        ;;
    restart)
        echo "🔄 Restarting all wallet daemons..."
        $0 stop
        sleep 5
        $0 start
        ;;
    status)
        echo "📊 Checking wallet status..."
        echo "================================"
        for i in "${!CLI_NAMES[@]}"; do
            echo "--- ${COINS[$i]^^} ---"
            if ${CLI_NAMES[$i]} getblockchaininfo &>/dev/null; then
                blocks=$(${CLI_NAMES[$i]} getblockchaininfo | grep '"blocks"' | cut -d: -f2 | tr -d ' ,')
                connections=$(${CLI_NAMES[$i]} getnetworkinfo | grep '"connections"' | cut -d: -f2 | tr -d ' ,')
                balance=$(${CLI_NAMES[$i]} getbalance 2>/dev/null || echo "0")
                echo "Status: ✅ Running"
                echo "Blocks: $blocks"
                echo "Connections: $connections"
                echo "Balance: $balance"
            else
                echo "Status: ❌ Not running"
            fi
            echo
        done
        ;;
    backup)
        echo "💾 Creating wallet backups..."
        backup_dir="~/wallets/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        for coin in "${COINS[@]}"; do
            if [ -f "$HOME/.${coin}/wallet.dat" ]; then
                cp "$HOME/.${coin}/wallet.dat" "$backup_dir/${coin}_wallet.dat"
                echo "✅ Backed up ${coin} wallet"
            else
                echo "⚠️  No wallet.dat found for ${coin}"
            fi
        done
        
        echo "📁 Backups created in: $backup_dir"
        ;;
    sync)
        echo "🔄 Checking synchronization status..."
        for i in "${!CLI_NAMES[@]}"; do
            if ${CLI_NAMES[$i]} getblockchaininfo &>/dev/null; then
                sync_progress=$(${CLI_NAMES[$i]} getblockchaininfo | grep '"verificationprogress"' | cut -d: -f2 | tr -d ' ,')
                sync_percent=$(echo "$sync_progress * 100" | bc -l | cut -d. -f1)
                echo "${COINS[$i]^^}: ${sync_percent}% synced"
            else
                echo "${COINS[$i]^^}: Not running"
            fi
        done
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|backup|sync}"
        echo
        echo "Commands:"
        echo "  start   - Start all wallet daemons"
        echo "  stop    - Stop all wallet daemons"
        echo "  restart - Restart all wallet daemons"
        echo "  status  - Show detailed status of all wallets"
        echo "  backup  - Create backup of all wallet.dat files"
        echo "  sync    - Check blockchain synchronization progress"
        exit 1
        ;;
esac
EOF

chmod +x ~/wallets/manage_wallets.sh
print_success "Wallet management script created: ~/wallets/manage_wallets.sh"

# Create wallet monitoring script
cat > ~/wallets/monitor_wallets.sh << 'EOF'
#!/bin/bash
# Wallet Monitoring Script

COINS=("aegisum" "advc" "shibacoin" "pepecoin")
CLI_NAMES=("aegisum-cli" "advc-cli" "shibacoin-cli" "pepecoin-cli")

echo "=== Wallet Monitoring Report ==="
echo "Generated: $(date)"
echo

total_balance_usd=0

for i in "${!CLI_NAMES[@]}"; do
    coin=${COINS[$i]}
    cli=${CLI_NAMES[$i]}
    
    echo "--- ${coin^^} ---"
    
    if $cli getblockchaininfo &>/dev/null; then
        # Get basic info
        blocks=$($cli getblockchaininfo | grep '"blocks"' | cut -d: -f2 | tr -d ' ,')
        connections=$($cli getnetworkinfo | grep '"connections"' | cut -d: -f2 | tr -d ' ,')
        balance=$($cli getbalance 2>/dev/null || echo "0")
        
        # Get memory usage
        mempool_size=$($cli getmempoolinfo | grep '"size"' | cut -d: -f2 | tr -d ' ,')
        
        echo "Status: ✅ Online"
        echo "Blocks: $blocks"
        echo "Connections: $connections"
        echo "Balance: $balance"
        echo "Mempool: $mempool_size transactions"
        
        # Check if fully synced
        sync_progress=$($cli getblockchaininfo | grep '"verificationprogress"' | cut -d: -f2 | tr -d ' ,')
        if (( $(echo "$sync_progress > 0.999" | bc -l) )); then
            echo "Sync: ✅ Fully synced"
        else
            sync_percent=$(echo "$sync_progress * 100" | bc -l | cut -d. -f1)
            echo "Sync: 🔄 ${sync_percent}% complete"
        fi
    else
        echo "Status: ❌ Offline"
    fi
    echo
done

echo "Powered By Aegisum EcoSystem"
EOF

chmod +x ~/wallets/monitor_wallets.sh
print_success "Wallet monitoring script created: ~/wallets/monitor_wallets.sh"

# Create installation completion script
cat > ~/wallets/complete_installation.sh << 'EOF'
#!/bin/bash
# Complete the wallet installation

echo "🔧 Completing wallet installation..."

# Install systemd services (requires sudo)
echo "Installing systemd services..."
for service in aegsd advcd shibacoind pepecoind; do
    if [ -f "/tmp/${service}.service" ]; then
        sudo cp "/tmp/${service}.service" "/etc/systemd/system/"
        sudo systemctl daemon-reload
        sudo systemctl enable "${service}"
        echo "✅ Installed ${service}.service"
    fi
done

echo
echo "🎉 Installation completed!"
echo
echo "Next steps:"
echo "1. Download and install wallet binaries to /usr/local/bin/"
echo "2. Update bot config with RPC passwords from ~/wallets/rpc_passwords.txt"
echo "3. Start wallets: ~/wallets/manage_wallets.sh start"
echo "4. Wait for synchronization: ~/wallets/manage_wallets.sh sync"
echo "5. Monitor status: ~/wallets/monitor_wallets.sh"
echo
echo "Powered By Aegisum EcoSystem"
EOF

chmod +x ~/wallets/complete_installation.sh

# Set secure permissions
chmod 600 ~/wallets/rpc_passwords.txt
chmod 700 ~/.aegisum ~/.advc ~/.shibacoin ~/.pepecoin

print_success "Optimized wallet installation completed!"
echo
print_warning "📋 IMPORTANT NEXT STEPS:"
print_warning "1. Download wallet binaries for your 4 coins"
print_warning "2. Copy binaries to /usr/local/bin/ (requires sudo)"
print_warning "3. Run: ~/wallets/complete_installation.sh (requires sudo)"
print_warning "4. Update bot config with RPC passwords from ~/wallets/rpc_passwords.txt"
print_warning "5. Start wallets: ~/wallets/manage_wallets.sh start"
echo
print_status "🔐 RPC passwords saved to: ~/wallets/rpc_passwords.txt"
print_status "📊 Monitor wallets with: ~/wallets/monitor_wallets.sh"
print_status "🎮 Manage wallets with: ~/wallets/manage_wallets.sh"
echo
print_success "Powered By Aegisum EcoSystem"