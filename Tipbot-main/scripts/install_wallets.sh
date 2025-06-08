#!/bin/bash
# Community Tipbot - Wallet Installation Script
# Powered By Aegisum EcoSystem

set -e

echo "🚀 Community Tipbot - Wallet Installation Script"
echo "================================================"

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
mkdir -p ~/.aegisum ~/.shibacoin ~/.pepecoin ~/.advc

# Function to download and install wallet
install_wallet() {
    local coin_name=$1
    local download_url=$2
    local cli_name=$3
    local daemon_name=$4
    
    print_status "Installing $coin_name wallet..."
    
    cd ~/wallets/downloads
    
    # Download wallet (placeholder URLs - replace with actual URLs)
    if [[ $coin_name == "AEGS" ]]; then
        print_warning "Please download Aegisum wallet manually from https://aegisum.com"
        print_warning "Extract and copy binaries to /usr/local/bin/"
        return
    fi
    
    # For other coins, you would add actual download URLs here
    print_warning "Please download $coin_name wallet manually and extract to /usr/local/bin/"
}

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
# $coin_name Configuration
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
EOF

    print_success "$coin_name configuration created at $config_dir/${coin_name,,}.conf"
    print_warning "RPC Password: $rpc_password"
    print_warning "Please update your bot config with this password!"
}

# Install wallets
print_status "Starting wallet installation process..."

# AEGS (Aegisum)
install_wallet "AEGS" "" "aegisum-cli" "aegisumd"
create_wallet_config "AEGS" "$HOME/.aegisum" "8332" "aegisumrpc"

# SHIC (ShibaCoin)
install_wallet "SHIC" "" "shibacoin-cli" "shibacoind"
create_wallet_config "SHIC" "$HOME/.shibacoin" "8333" "shibacoirpc"

# PEPE (PepeCoin)
install_wallet "PEPE" "" "pepecoin-cli" "pepecoind"
create_wallet_config "PEPE" "$HOME/.pepecoin" "8334" "pepecoirpc"

# ADVC (AdvCoin)
install_wallet "ADVC" "" "advc-cli" "advcd"
create_wallet_config "ADVC" "$HOME/.advc" "8335" "advcrpc"

# Create systemd service files
print_status "Creating systemd service files..."

create_systemd_service() {
    local coin_name=$1
    local daemon_name=$2
    local cli_name=$3
    
    cat > "/tmp/${coin_name,,}d.service" << EOF
[Unit]
Description=$coin_name Daemon
After=network.target

[Service]
Type=forking
User=$USER
ExecStart=/usr/local/bin/$daemon_name -daemon
ExecStop=/usr/local/bin/$cli_name stop
Restart=always
RestartSec=30
TimeoutStopSec=60

[Install]
WantedBy=multi-user.target
EOF

    print_success "Service file created: /tmp/${coin_name,,}d.service"
    print_warning "Please copy to /etc/systemd/system/ as root:"
    print_warning "sudo cp /tmp/${coin_name,,}d.service /etc/systemd/system/"
}

create_systemd_service "AEGS" "aegisumd" "aegisum-cli"
create_systemd_service "SHIC" "shibacoind" "shibacoin-cli"
create_systemd_service "PEPE" "pepecoind" "pepecoin-cli"
create_systemd_service "ADVC" "advcd" "advc-cli"

# Create wallet management script
print_status "Creating wallet management script..."

cat > ~/wallets/manage_wallets.sh << 'EOF'
#!/bin/bash
# Wallet Management Script

case "$1" in
    start)
        echo "Starting all wallet daemons..."
        aegisumd -daemon
        shibacoind -daemon
        pepecoind -daemon
        advcd -daemon
        ;;
    stop)
        echo "Stopping all wallet daemons..."
        aegisum-cli stop
        shibacoin-cli stop
        pepecoin-cli stop
        advc-cli stop
        ;;
    status)
        echo "Checking wallet status..."
        echo "AEGS:" && aegisum-cli getblockchaininfo | grep blocks
        echo "SHIC:" && shibacoin-cli getblockchaininfo | grep blocks
        echo "PEPE:" && pepecoin-cli getblockchaininfo | grep blocks
        echo "ADVC:" && advc-cli getblockchaininfo | grep blocks
        ;;
    backup)
        echo "Creating wallet backups..."
        mkdir -p ~/wallets/backups/$(date +%Y%m%d)
        cp ~/.aegisum/wallet.dat ~/wallets/backups/$(date +%Y%m%d)/aegisum_wallet.dat
        cp ~/.shibacoin/wallet.dat ~/wallets/backups/$(date +%Y%m%d)/shibacoin_wallet.dat
        cp ~/.pepecoin/wallet.dat ~/wallets/backups/$(date +%Y%m%d)/pepecoin_wallet.dat
        cp ~/.advc/wallet.dat ~/wallets/backups/$(date +%Y%m%d)/advc_wallet.dat
        echo "Backups created in ~/wallets/backups/$(date +%Y%m%d)/"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|backup}"
        exit 1
        ;;
esac
EOF

chmod +x ~/wallets/manage_wallets.sh
print_success "Wallet management script created: ~/wallets/manage_wallets.sh"

# Create wallet info script
cat > ~/wallets/wallet_info.sh << 'EOF'
#!/bin/bash
# Wallet Information Script

echo "=== Community Tipbot Wallet Information ==="
echo

for coin in aegisum shibacoin pepecoin advc; do
    cli_name="${coin}-cli"
    if [[ $coin == "advc" ]]; then
        cli_name="advc-cli"
    fi
    
    echo "--- ${coin^^} ---"
    if command -v $cli_name &> /dev/null; then
        echo "CLI: Available"
        if $cli_name getblockchaininfo &> /dev/null; then
            blocks=$($cli_name getblockchaininfo | grep '"blocks"' | cut -d: -f2 | tr -d ' ,')
            connections=$($cli_name getnetworkinfo | grep '"connections"' | cut -d: -f2 | tr -d ' ,')
            balance=$($cli_name getbalance 2>/dev/null || echo "0")
            echo "Status: Running"
            echo "Blocks: $blocks"
            echo "Connections: $connections"
            echo "Balance: $balance"
        else
            echo "Status: Not running"
        fi
    else
        echo "CLI: Not found"
    fi
    echo
done

echo "Powered By Aegisum EcoSystem"
EOF

chmod +x ~/wallets/wallet_info.sh
print_success "Wallet info script created: ~/wallets/wallet_info.sh"

print_success "Wallet installation script completed!"
echo
print_warning "Next steps:"
print_warning "1. Download and install wallet binaries manually"
print_warning "2. Copy systemd service files to /etc/systemd/system/ as root"
print_warning "3. Update bot configuration with RPC passwords"
print_warning "4. Start wallet daemons: ~/wallets/manage_wallets.sh start"
print_warning "5. Wait for blockchain synchronization"
print_warning "6. Test with: ~/wallets/wallet_info.sh"
echo
print_status "Powered By Aegisum EcoSystem"