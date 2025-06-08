# Server Requirements and Cleanup Guide

## 🖥️ Ubuntu Server Requirements for Your Tipbot

### Minimum Requirements (Basic Operation)
- **CPU:** 4 cores @ 2.0 GHz
- **RAM:** 8GB DDR4
- **Storage:** 200GB SSD
- **Network:** 100 Mbps
- **OS:** Ubuntu 20.04 LTS or newer

### Recommended Requirements (Optimal Performance)
- **CPU:** 8 cores @ 3.0 GHz (Intel i7/AMD Ryzen 7)
- **RAM:** 16GB DDR4
- **Storage:** 500GB NVMe SSD
- **Network:** 1 Gbps
- **OS:** Ubuntu 22.04 LTS

### Enterprise Requirements (High Volume)
- **CPU:** 16 cores @ 3.5 GHz (Intel i9/AMD Ryzen 9)
- **RAM:** 32GB DDR4
- **Storage:** 1TB NVMe SSD
- **Network:** 10 Gbps
- **OS:** Ubuntu 22.04 LTS

## 💾 Storage Requirements by Blockchain

### Current Blockchain Sizes (Estimated)
| Coin | Full Node | Pruned Node | Growth Rate |
|------|-----------|-------------|-------------|
| **AEGS** (Aegisum) | ~50GB | ~5GB | ~2GB/month |
| **ADVC** (AdventureCoin) | ~30GB | ~3GB | ~1GB/month |
| **SHIC** (ShibaCoin) | ~40GB | ~4GB | ~1.5GB/month |
| **PEPE** (PepeCoin) | ~35GB | ~3.5GB | ~1.2GB/month |

### Storage Allocation Plan
```
/home/tipbot/
├── wallets/                    # 200GB (blockchain data)
│   ├── .aegisum/              # 50GB
│   ├── .advc/                 # 30GB  
│   ├── .shibacoin/            # 40GB
│   └── .pepecoin/             # 35GB
├── tipbot/                    # 10GB (bot code & data)
├── backups/                   # 50GB (wallet backups)
└── logs/                      # 10GB (log files)
```

## 🧹 Cleanup: Remove Unnecessary Wallet Cores

### What to Remove from Your Current Setup

#### ❌ Remove These Wallet Cores (Not Needed):
```bash
# Bitcoin Core
sudo systemctl stop bitcoind
sudo systemctl disable bitcoind
sudo rm -rf ~/.bitcoin
sudo rm /usr/local/bin/bitcoin*

# Litecoin Core  
sudo systemctl stop litecoind
sudo systemctl disable litecoind
sudo rm -rf ~/.litecoin
sudo rm /usr/local/bin/litecoin*

# Dash Core
sudo systemctl stop dashd
sudo systemctl disable dashd
sudo rm -rf ~/.dashcore
sudo rm /usr/local/bin/dash*

# Viacoin Core
sudo systemctl stop viacoind
sudo systemctl disable viacoind
sudo rm -rf ~/.viacoin
sudo rm /usr/local/bin/viacoin*

# Any other unused coins
sudo rm -rf ~/.dogecoin ~/.monero ~/.ethereum
```

#### ✅ Keep Only These (Your 4 Coins):
- **Aegisum** (`aegisumd`, `aegisum-cli`)
- **AdventureCoin** (`advcd`, `advc-cli`)
- **ShibaCoin** (`shibacoind`, `shibacoin-cli`)
- **PepeCoin** (`pepecoind`, `pepecoin-cli`)

### Cleanup Script
```bash
#!/bin/bash
# Cleanup unnecessary wallet cores

echo "🧹 Cleaning up unnecessary wallet cores..."

# Stop all services
sudo systemctl stop bitcoind litecoind dashd viacoind 2>/dev/null || true

# Disable services
sudo systemctl disable bitcoind litecoind dashd viacoind 2>/dev/null || true

# Remove service files
sudo rm -f /etc/systemd/system/{bitcoin,litecoin,dash,viacoin}*.service

# Remove binaries
sudo rm -f /usr/local/bin/{bitcoin,litecoin,dash,viacoin}*

# Remove data directories (BACKUP FIRST!)
read -p "⚠️  Remove blockchain data? This will delete all synced data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf ~/.bitcoin ~/.litecoin ~/.dashcore ~/.viacoin
    echo "✅ Removed unnecessary blockchain data"
fi

# Reload systemd
sudo systemctl daemon-reload

echo "🎉 Cleanup completed!"
echo "💾 Estimated space freed: ~500GB"
```

## 🔧 Node Requirements Analysis

### Do You Need More Nodes?

#### Current Setup Assessment:
- **4 blockchain nodes** (AEGS, ADVC, SHIC, PEPE)
- **1 tipbot application**
- **1 admin dashboard**

#### Recommendations:

**✅ Single Server Setup (Recommended for Start)**
```
Ubuntu Server (16GB RAM, 8 cores, 500GB SSD)
├── 4 Blockchain Nodes (same server)
├── Tipbot Application  
├── Admin Dashboard
└── Database
```

**🔄 Multi-Server Setup (For High Volume)**
```
Server 1: Blockchain Nodes (32GB RAM, 16 cores, 1TB SSD)
├── Aegisum Node
├── ADVC Node  
├── ShibaCoin Node
└── PepeCoin Node

Server 2: Application Server (16GB RAM, 8 cores, 200GB SSD)
├── Tipbot Application
├── Admin Dashboard
├── Database
└── Load Balancer
```

**🌐 Distributed Setup (Enterprise)**
```
Server 1: Aegisum + ADVC Nodes
Server 2: SHIC + PEPE Nodes  
Server 3: Tipbot Application
Server 4: Database + Backups
```

### Network Requirements

#### Bandwidth Usage:
- **Initial Sync:** 50-100 Mbps (one-time)
- **Normal Operation:** 10-20 Mbps
- **Peak Usage:** 50 Mbps

#### Port Requirements:
```
Aegisum:     8332 (RPC), 8333 (P2P)
ADVC:        8335 (RPC), 8336 (P2P)  
ShibaCoin:   8333 (RPC), 8334 (P2P)
PepeCoin:    8334 (RPC), 8335 (P2P)
Tipbot:      12000 (Dashboard)
```

## 🛡️ Security Recommendations

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8332:8336/tcp  # Blockchain RPC
sudo ufw allow 12000/tcp      # Admin dashboard
sudo ufw deny 8333:8336/tcp   # Block P2P from external
```

### System Hardening
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash tipbot
sudo usermod -aG sudo tipbot

# Secure SSH
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Install fail2ban
sudo apt install fail2ban
```

## 📊 Monitoring Setup

### System Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor resources
htop                    # CPU/RAM usage
iotop                   # Disk I/O
nethogs                 # Network usage
df -h                   # Disk space
```

### Blockchain Monitoring
```bash
# Check sync status
~/wallets/monitor_wallets.sh

# Check connections
aegisum-cli getnetworkinfo
advc-cli getnetworkinfo  
shibacoin-cli getnetworkinfo
pepecoin-cli getnetworkinfo
```

## 🚀 Deployment Recommendation

### For Your Use Case, I Recommend:

**🎯 Single Server Setup:**
- **Server:** Ubuntu 22.04 LTS
- **Specs:** 16GB RAM, 8 cores, 500GB NVMe SSD
- **Network:** 1 Gbps connection
- **Setup:** All 4 nodes + tipbot on same server

**Why Single Server?**
- ✅ Cost effective
- ✅ Easier management  
- ✅ Lower latency between components
- ✅ Sufficient for moderate usage
- ✅ Can scale later if needed

**When to Scale to Multiple Servers:**
- 📈 >1000 active users
- 📈 >10,000 tips per day
- 📈 >100GB daily transaction volume
- 📈 Need 99.9% uptime

## 💡 Next Steps

1. **Clean up current server** using cleanup script
2. **Install only your 4 wallet cores**
3. **Deploy optimized tipbot** from `/workspace/optimized-tipbot/`
4. **Monitor resource usage** for 1-2 weeks
5. **Scale if needed** based on actual usage

---
**Powered By Aegisum EcoSystem**