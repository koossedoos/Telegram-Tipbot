# 🔧 Community Tipbot - Troubleshooting Guide

## 🚨 Quick Diagnostic Commands

### Check Everything Status
```bash
# Run this first to check overall status
./manage_bot.sh status

# Check if all processes are running
ps aux | grep -E "(bot.py|app.py|transaction_monitor)"

# Check logs for errors
tail -20 logs/bot.log
tail -20 logs/admin.log
tail -20 logs/error.log
```

---

## 🔍 Common Issues & Solutions

### 1. ❌ Bot Not Responding to Commands

**Symptoms:** Bot doesn't reply to `/start` or other commands

**Diagnosis:**
```bash
# Check if bot process is running
ps aux | grep bot.py

# Check bot logs
tail -f logs/bot.log

# Test Telegram token
curl -s "https://api.telegram.org/bot$BOT_TOKEN/getMe"
```

**Solutions:**
```bash
# Restart bot
./manage_bot.sh restart

# If token invalid, reconfigure
python3 configure_bot.py

# Check network connectivity
ping api.telegram.org
```

### 2. ❌ Coin Daemon Connection Failed

**Symptoms:** "Failed to connect to coin daemon" errors

**Diagnosis:**
```bash
# Check if daemon is running
ps aux | grep -E "(aegisum|shibacoin|pepecoin|advc)"

# Test CLI connection
aegisum-cli getinfo
shibacoin-cli getinfo
pepecoin-cli getinfo
advc-cli getinfo
```

**Solutions:**
```bash
# Start missing daemons
aegisum-cli -daemon
shibacoin-cli -daemon
pepecoin-cli -daemon
advc-cli -daemon

# Check config files
cat ~/.aegisum/aegisum.conf
cat ~/.shibacoin/shibacoin.conf

# Wait for sync
aegisum-cli getblockchaininfo
```

### 3. ❌ Database Errors

**Symptoms:** SQLite errors, "database locked" messages

**Diagnosis:**
```bash
# Check database file
ls -la data/tipbot.db

# Check database integrity
sqlite3 data/tipbot.db "PRAGMA integrity_check;"

# Check for locks
lsof data/tipbot.db
```

**Solutions:**
```bash
# Stop all services
./manage_bot.sh stop

# Backup database
cp data/tipbot.db data/tipbot.db.backup

# Restart services
./manage_bot.sh start

# If corrupted, reinitialize
python3 -c "from src.database import Database; Database('data/tipbot.db').init_db()"
```

### 4. ❌ Admin Dashboard Not Accessible

**Symptoms:** Can't access web dashboard

**Diagnosis:**
```bash
# Check if Flask app is running
ps aux | grep app.py

# Check port binding
netstat -tlnp | grep 5000

# Check firewall
sudo ufw status
```

**Solutions:**
```bash
# Restart dashboard
pkill -f app.py
python3 admin_dashboard/app.py &

# Check firewall rules
sudo ufw allow 5000

# Test locally
curl http://localhost:5000
```

### 5. ❌ Transaction Monitoring Issues

**Symptoms:** No deposit/withdrawal notifications

**Diagnosis:**
```bash
# Check monitor process
ps aux | grep transaction_monitor

# Check monitor logs
tail -f logs/transaction_monitor.log

# Test coin connectivity
aegisum-cli listunspent
```

**Solutions:**
```bash
# Restart monitor
pkill -f transaction_monitor
python3 src/transaction_monitor.py &

# Check coin sync status
aegisum-cli getblockchaininfo
```

### 6. ❌ Permission Errors

**Symptoms:** "Permission denied" errors

**Diagnosis:**
```bash
# Check file permissions
ls -la *.sh scripts/*.sh

# Check ownership
ls -la data/ logs/ config/
```

**Solutions:**
```bash
# Fix script permissions
chmod +x *.sh scripts/*.sh configure_bot.py

# Fix directory ownership
chown -R $USER:$USER .

# Fix data directory permissions
chmod 755 data/ logs/ config/
```

### 7. ❌ Memory/Resource Issues

**Symptoms:** Bot crashes, "out of memory" errors

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -10

# Check disk space
df -h
```

**Solutions:**
```bash
# Restart services to free memory
./manage_bot.sh restart

# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Add swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 🔧 Advanced Diagnostics

### Full System Check
```bash
#!/bin/bash
echo "=== COMMUNITY TIPBOT DIAGNOSTIC ==="
echo "Date: $(date)"
echo

echo "1. System Resources:"
echo "Memory: $(free -h | grep Mem)"
echo "Disk: $(df -h / | tail -1)"
echo "Load: $(uptime)"
echo

echo "2. Bot Processes:"
ps aux | grep -E "(bot.py|app.py|transaction_monitor)" | grep -v grep
echo

echo "3. Coin Daemons:"
ps aux | grep -E "(aegisum|shibacoin|pepecoin|advc)" | grep -v grep
echo

echo "4. Network Connectivity:"
ping -c 1 api.telegram.org >/dev/null && echo "Telegram: OK" || echo "Telegram: FAILED"
echo

echo "5. Database Status:"
ls -la data/tipbot.db 2>/dev/null && echo "Database: EXISTS" || echo "Database: MISSING"
echo

echo "6. Configuration:"
ls -la config/config.json 2>/dev/null && echo "Config: EXISTS" || echo "Config: MISSING"
echo

echo "7. Recent Errors:"
tail -5 logs/error.log 2>/dev/null || echo "No error log found"
```

### Log Analysis
```bash
# Check for common error patterns
grep -i "error\|exception\|failed" logs/bot.log | tail -10
grep -i "connection\|timeout" logs/bot.log | tail -10
grep -i "database\|sqlite" logs/bot.log | tail -10
```

### Performance Monitoring
```bash
# Monitor resource usage
watch -n 5 'ps aux | grep -E "(bot.py|app.py)" | grep -v grep'

# Monitor log activity
tail -f logs/bot.log logs/admin.log logs/transaction_monitor.log
```

---

## 🚀 Recovery Procedures

### Complete Restart
```bash
# Stop everything
./manage_bot.sh stop
pkill -f "python3.*bot"
pkill -f "python3.*app"

# Wait 10 seconds
sleep 10

# Start everything
./manage_bot.sh start
```

### Reset Configuration
```bash
# Backup current config
cp config/config.json config/config.json.backup

# Reconfigure from scratch
python3 configure_bot.py
```

### Database Recovery
```bash
# Stop services
./manage_bot.sh stop

# Backup current database
cp data/tipbot.db data/tipbot.db.$(date +%Y%m%d)

# Reinitialize database
python3 -c "from src.database import Database; Database('data/tipbot.db').init_db()"

# Restart services
./manage_bot.sh start
```

### Emergency Wallet Recovery
```bash
# Export all private keys (BACKUP FIRST!)
for coin in aegisum shibacoin pepecoin advc; do
    echo "=== $coin ==="
    ${coin}-cli dumpwallet /tmp/${coin}_wallet_backup.txt
done

# Import to new wallet if needed
# ${coin}-cli importwallet /tmp/${coin}_wallet_backup.txt
```

---

## 📞 Getting Help

### Log Collection for Support
```bash
# Create support package
tar -czf tipbot_support_$(date +%Y%m%d).tar.gz \
    logs/ \
    config/config.json \
    data/tipbot.db \
    --exclude="*.log.*"

echo "Support package created: tipbot_support_$(date +%Y%m%d).tar.gz"
```

### Contact Information
- **Repository:** https://github.com/mikekoosssss/Tipbot
- **Issues:** Create GitHub issue with logs
- **Documentation:** Check all .md files in repository

---

## ✅ Health Check Script

Save this as `health_check.sh`:
```bash
#!/bin/bash
HEALTH_OK=true

# Check bot process
if ! pgrep -f "bot.py" > /dev/null; then
    echo "❌ Bot process not running"
    HEALTH_OK=false
fi

# Check admin dashboard
if ! pgrep -f "app.py" > /dev/null; then
    echo "❌ Admin dashboard not running"
    HEALTH_OK=false
fi

# Check database
if [ ! -f "data/tipbot.db" ]; then
    echo "❌ Database file missing"
    HEALTH_OK=false
fi

# Check coin daemons
for coin in aegisum shibacoin pepecoin advc; do
    if ! ${coin}-cli getinfo >/dev/null 2>&1; then
        echo "❌ $coin daemon not responding"
        HEALTH_OK=false
    fi
done

if $HEALTH_OK; then
    echo "✅ All systems operational"
    exit 0
else
    echo "❌ Issues detected - check logs"
    exit 1
fi
```

Run with: `chmod +x health_check.sh && ./health_check.sh`

*Powered by Aegisum Ecosystem* ⚡