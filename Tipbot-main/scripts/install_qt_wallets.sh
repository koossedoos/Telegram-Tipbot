#!/bin/bash
# Community Tipbot - QT Wallet Installation Script
# Powered By Aegisum EcoSystem

set -e

echo "🚀 Community Tipbot - QT Wallet Installer"
echo "Powered By Aegisum EcoSystem"
echo "========================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Create wallets directory
WALLET_DIR="$HOME/wallets"
mkdir -p "$WALLET_DIR"
cd "$WALLET_DIR"

print_header "Creating wallet installation directory: $WALLET_DIR"

# Function to download and install a wallet
install_wallet() {
    local coin_name="$1"
    local download_url="$2"
    local binary_name="$3"
    local qt_binary_name="$4"
    
    print_header "Installing $coin_name wallet..."
    
    if [ -z "$download_url" ]; then
        print_warning "$coin_name download URL not provided. Please install manually."
        echo "  1. Download $coin_name wallet from official website"
        echo "  2. Extract to $WALLET_DIR/$coin_name/"
        echo "  3. Make binaries executable: chmod +x $WALLET_DIR/$coin_name/*"
        echo "  4. Add to PATH or create symlinks"
        echo
        return
    fi
    
    # Create coin directory
    mkdir -p "$coin_name"
    cd "$coin_name"
    
    # Download wallet
    print_status "Downloading $coin_name wallet..."
    if command -v wget >/dev/null 2>&1; then
        wget -O "${coin_name}-wallet.tar.gz" "$download_url" || {
            print_error "Failed to download $coin_name wallet"
            cd ..
            return 1
        }
    elif command -v curl >/dev/null 2>&1; then
        curl -L -o "${coin_name}-wallet.tar.gz" "$download_url" || {
            print_error "Failed to download $coin_name wallet"
            cd ..
            return 1
        }
    else
        print_error "Neither wget nor curl found. Please install one of them."
        cd ..
        return 1
    fi
    
    # Extract wallet
    print_status "Extracting $coin_name wallet..."
    if [[ "$download_url" == *.zip ]]; then
        unzip -q "${coin_name}-wallet.zip" || unzip -q "${coin_name}-wallet.tar.gz"
    else
        tar -xzf "${coin_name}-wallet.tar.gz" 2>/dev/null || tar -xf "${coin_name}-wallet.tar.gz"
    fi
    
    # Make binaries executable
    find . -name "$binary_name" -exec chmod +x {} \; 2>/dev/null || true
    find . -name "$qt_binary_name" -exec chmod +x {} \; 2>/dev/null || true
    find . -name "${coin_name}d" -exec chmod +x {} \; 2>/dev/null || true
    
    # Create symlinks
    if [ -f "$binary_name" ]; then
        ln -sf "$WALLET_DIR/$coin_name/$binary_name" "$HOME/.local/bin/$binary_name" 2>/dev/null || true
        print_status "$coin_name CLI installed: $binary_name"
    fi
    
    if [ -f "$qt_binary_name" ]; then
        ln -sf "$WALLET_DIR/$coin_name/$qt_binary_name" "$HOME/.local/bin/$qt_binary_name" 2>/dev/null || true
        print_status "$coin_name QT installed: $qt_binary_name"
    fi
    
    cd ..
    print_status "$coin_name installation completed!"
    echo
}

# Create local bin directory
mkdir -p "$HOME/.local/bin"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    export PATH="$HOME/.local/bin:$PATH"
    print_status "Added $HOME/.local/bin to PATH"
fi

print_header "Installing cryptocurrency wallets..."
echo

# Install AEGS (Aegisum)
print_header "🔸 AEGS (Aegisum) Wallet"
echo "Please download Aegisum wallet from: https://aegisum.com"
echo "Recommended: Download the latest release for your platform"
install_wallet "aegisum" "" "aegisum-cli" "aegisum-qt"

# Install SHIC (ShibaCoin)
print_header "🔸 SHIC (ShibaCoin) Wallet"
echo "Please download ShibaCoin wallet from the official repository"
echo "Look for releases on GitHub or official website"
install_wallet "shibacoin" "" "shibacoin-cli" "shibacoin-qt"

# Install PEPE (PepeCoin)
print_header "🔸 PEPE (PepeCoin) Wallet"
echo "Please download PepeCoin wallet from the official repository"
echo "Look for releases on GitHub or official website"
install_wallet "pepecoin" "" "pepecoin-cli" "pepecoin-qt"

# Install ADVC (AdvCoin)
print_header "🔸 ADVC (AdvCoin) Wallet"
echo "Please download AdvCoin wallet from the official repository"
echo "Look for releases on GitHub or official website"
install_wallet "advc" "" "advc-cli" "advc-qt"

# Create wallet management script
print_header "Creating wallet management scripts..."

cat > "$WALLET_DIR/start_wallets.sh" << 'EOF'
#!/bin/bash
# Start all wallet daemons

echo "🚀 Starting wallet daemons..."

# Start AEGS daemon
if command -v aegisumd >/dev/null 2>&1; then
    echo "Starting Aegisum daemon..."
    aegisumd -daemon
fi

# Start SHIC daemon
if command -v shibacoind >/dev/null 2>&1; then
    echo "Starting ShibaCoin daemon..."
    shibacoind -daemon
fi

# Start PEPE daemon
if command -v pepecoind >/dev/null 2>&1; then
    echo "Starting PepeCoin daemon..."
    pepecoind -daemon
fi

# Start ADVC daemon
if command -v advcd >/dev/null 2>&1; then
    echo "Starting AdvCoin daemon..."
    advcd -daemon
fi

echo "✅ Wallet daemons started!"
echo "Wait a few minutes for synchronization to begin."
EOF

cat > "$WALLET_DIR/stop_wallets.sh" << 'EOF'
#!/bin/bash
# Stop all wallet daemons

echo "🛑 Stopping wallet daemons..."

# Stop AEGS daemon
if command -v aegisum-cli >/dev/null 2>&1; then
    echo "Stopping Aegisum daemon..."
    aegisum-cli stop 2>/dev/null || true
fi

# Stop SHIC daemon
if command -v shibacoin-cli >/dev/null 2>&1; then
    echo "Stopping ShibaCoin daemon..."
    shibacoin-cli stop 2>/dev/null || true
fi

# Stop PEPE daemon
if command -v pepecoin-cli >/dev/null 2>&1; then
    echo "Stopping PepeCoin daemon..."
    pepecoin-cli stop 2>/dev/null || true
fi

# Stop ADVC daemon
if command -v advc-cli >/dev/null 2>&1; then
    echo "Stopping AdvCoin daemon..."
    advc-cli stop 2>/dev/null || true
fi

echo "✅ Wallet daemons stopped!"
EOF

cat > "$WALLET_DIR/wallet_status.sh" << 'EOF'
#!/bin/bash
# Check wallet daemon status

echo "📊 Wallet Status Check"
echo "====================="

check_wallet() {
    local cli_cmd="$1"
    local coin_name="$2"
    
    if command -v "$cli_cmd" >/dev/null 2>&1; then
        echo -n "$coin_name: "
        if $cli_cmd getblockcount >/dev/null 2>&1; then
            local blocks=$($cli_cmd getblockcount 2>/dev/null)
            local connections=$($cli_cmd getconnectioncount 2>/dev/null)
            echo "✅ Running (Blocks: $blocks, Connections: $connections)"
        else
            echo "❌ Not running or not synced"
        fi
    else
        echo "$coin_name: ⚠️  CLI not found"
    fi
}

check_wallet "aegisum-cli" "AEGS (Aegisum)"
check_wallet "shibacoin-cli" "SHIC (ShibaCoin)"
check_wallet "pepecoin-cli" "PEPE (PepeCoin)"
check_wallet "advc-cli" "ADVC (AdvCoin)"

echo
echo "💡 Tips:"
echo "  - Use ./start_wallets.sh to start all daemons"
echo "  - Use ./stop_wallets.sh to stop all daemons"
echo "  - Wait for synchronization before using the tipbot"
EOF

# Make scripts executable
chmod +x "$WALLET_DIR"/*.sh

print_status "Wallet management scripts created:"
print_status "  - start_wallets.sh: Start all wallet daemons"
print_status "  - stop_wallets.sh: Stop all wallet daemons"
print_status "  - wallet_status.sh: Check wallet status"

# Create desktop entries for QT wallets
print_header "Creating desktop entries for QT wallets..."

DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

create_desktop_entry() {
    local coin_name="$1"
    local qt_binary="$2"
    local display_name="$3"
    
    if [ -f "$WALLET_DIR/$coin_name/$qt_binary" ]; then
        cat > "$DESKTOP_DIR/$coin_name.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$display_name
Comment=$display_name Wallet
Exec=$WALLET_DIR/$coin_name/$qt_binary
Icon=applications-internet
Terminal=false
Categories=Network;Finance;
EOF
        print_status "Desktop entry created for $display_name"
    fi
}

create_desktop_entry "aegisum" "aegisum-qt" "Aegisum Wallet"
create_desktop_entry "shibacoin" "shibacoin-qt" "ShibaCoin Wallet"
create_desktop_entry "pepecoin" "pepecoin-qt" "PepeCoin Wallet"
create_desktop_entry "advc" "advc-qt" "AdvCoin Wallet"

# Final instructions
print_header "Installation Summary"
echo
print_status "Wallet installation directory: $WALLET_DIR"
print_status "Management scripts location: $WALLET_DIR/*.sh"
print_status "Desktop entries created in: $DESKTOP_DIR"
echo

print_warning "IMPORTANT NEXT STEPS:"
echo "1. 📥 Download wallet binaries manually from official sources:"
echo "   - AEGS: https://aegisum.com"
echo "   - SHIC: Official ShibaCoin repository"
echo "   - PEPE: Official PepeCoin repository"
echo "   - ADVC: Official AdvCoin repository"
echo
echo "2. 📁 Extract wallet files to respective directories:"
echo "   - $WALLET_DIR/aegisum/"
echo "   - $WALLET_DIR/shibacoin/"
echo "   - $WALLET_DIR/pepecoin/"
echo "   - $WALLET_DIR/advc/"
echo
echo "3. 🔧 Make binaries executable:"
echo "   chmod +x $WALLET_DIR/*/aegisum*"
echo "   chmod +x $WALLET_DIR/*/shibacoin*"
echo "   chmod +x $WALLET_DIR/*/pepecoin*"
echo "   chmod +x $WALLET_DIR/*/advc*"
echo
echo "4. 🚀 Start wallet daemons:"
echo "   cd $WALLET_DIR && ./start_wallets.sh"
echo
echo "5. ✅ Check wallet status:"
echo "   cd $WALLET_DIR && ./wallet_status.sh"
echo
echo "6. ⚙️ Configure tipbot with correct CLI paths in config.json"
echo

print_status "QT Wallet installation script completed!"
print_status "Powered By Aegisum EcoSystem"