#!/bin/bash
# Community Tipbot Management Script
# Powered By Aegisum EcoSystem

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