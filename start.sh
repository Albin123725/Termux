#!/bin/bash

echo "=========================================="
echo "   🎮 TERMUX CLUSTER - Render Deployment"
echo "=========================================="

# Run startup script
if [ -f ~/scripts/startup.sh ]; then
    ~/scripts/startup.sh
fi

# Set default values
NODE_COUNT=${NODE_COUNT:-1}
TOTAL_RAM=${TOTAL_RAM:-8}

echo "🔧 Configuration:"
echo "   Nodes: $NODE_COUNT"
echo "   RAM: ${TOTAL_RAM}GB"

# Create directories
mkdir -p ~/cluster ~/minecraft/servers ~/cloud-storage/nodes ~/backups/minecraft

if [ "$SERVICE_TYPE" = "worker" ]; then
    echo "🚀 Starting Worker Node..."
    python3 ~/scripts/worker.py
else
    echo "🚀 Starting Main Cluster Terminal..."
    
    # Start web terminal
    echo "🌐 Starting web terminal..."
    ttyd -p 10000 -W bash &
    
    sleep 3
    
    # Start cluster services
    echo "🔄 Starting cluster services..."
    
    # Auto-combiner
    echo "   🔄 Auto-Combiner (Port 5001)..."
    python3 ~/scripts/auto-combiner.py &
    sleep 2
    
    # Minecraft manager
    echo "   🎮 Minecraft Manager (Port 5002)..."
    python3 ~/scripts/adaptive-minecraft.py &
    sleep 2
    
    # Backup system
    echo "   📦 Backup System (Port 5003)..."
    
    # Setup Google Drive credentials first
    if [ -f ~/scripts/google-drive-auth.py ]; then
        echo "   🔐 Setting up Google Drive credentials..."
        python3 ~/scripts/google-drive-auth.py
    fi
    
    # Start backup manager
    python3 ~/scripts/backup-manager.py &
    sleep 2
    
    # Start auto-backup in background (5-minute intervals)
    echo "   💾 Starting auto-backup (5-minute intervals)..."
    python3 ~/scripts/auto-backup.py &
    sleep 2
    
    # Cluster monitor
    echo "   📊 Cluster Monitor..."
    python3 ~/scripts/cluster-monitor.py &
    
    # Calculate Minecraft servers
    if [ $NODE_COUNT -ge 4 ]; then
        MC_SERVERS=3
    elif [ $NODE_COUNT -ge 2 ]; then
        MC_SERVERS=2
    else
        MC_SERVERS=1
    fi
    
    echo ""
    echo "✅ CLUSTER READY!"
    echo "🌐 Web Terminal: Port 10000"
    echo "🧠 Nodes: $NODE_COUNT"
    echo "💾 RAM: ${TOTAL_RAM}GB"
    echo "🎮 Minecraft: $MC_SERVERS servers available"
    echo "📦 Auto-Backup: Every 5 minutes to Google Drive"
    echo ""
    echo "🔧 Services Running:"
    echo "   ✅ Web Terminal (Port 10000)"
    echo "   ✅ Auto-Combiner (Port 5001)"
    echo "   ✅ Minecraft Manager (Port 5002)"
    echo "   ✅ Backup Manager (Port 5003)"
    echo "   ✅ Auto-Backup (5-minute intervals)"
    echo "   ✅ Cluster Monitor"
    echo ""
    echo "🎮 Minecraft Commands:"
    echo "   mc-start 1/2/3    - Start Minecraft server"
    echo "   mc-stop 1/2/3     - Stop Minecraft server"
    echo "   mc-status         - Check server status"
    echo ""
    echo "📦 Backup Commands:"
    echo "   backup-status     - Check backup system"
    echo "   backup-now        - Trigger immediate backup"
    echo "   backup-list       - List all backups"
    echo ""
    echo "📊 Cluster Commands:"
    echo "   cluster-stats     - Show cluster resources"
    echo "   nodes-discover    - Discover available nodes"
    echo ""
    echo "🔗 Access URLs:"
    echo "   Web Terminal: https://$(hostname).onrender.com"
    echo "   Minecraft: Ports 25565, 25566, 25567"
    echo "   Backup API: Port 5003"
    
    # Keep container running
    tail -f /dev/null
fi
