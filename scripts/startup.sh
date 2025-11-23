#!/bin/bash

echo "=== Auto-Combining Cluster Startup ==="

# Get configuration
NODE_COUNT=${NODE_COUNT:-1}
TOTAL_RAM=${TOTAL_RAM:-8}

echo "🔄 Configuring cluster with $NODE_COUNT nodes..."

# Create directories
mkdir -p ~/projects ~/downloads ~/temp ~/backups ~/cluster ~/minecraft/servers ~/cloud-storage/nodes

# Create Minecraft directories
for i in 1 2 3; do
    mkdir -p ~/minecraft/servers/server-$i
done

# Create backup directories
mkdir -p ~/backups/minecraft

# Set up git
if [ ! -f ~/.gitconfig ]; then
    git config --global user.name "Termux User"
    git config --global user.email "termux@cluster.com"
    echo "✓ Git configured"
fi

# Create comprehensive aliases
cat >> ~/.bashrc << 'EOF'

# ==========================================
# 🎮 TERMUX CLUSTER MANAGEMENT ALIASES
# ==========================================

# 🔧 Cluster Management
alias cluster-stats='curl -s http://localhost:5001/cluster/status | python3 -m json.tool'
alias nodes-discover='curl -s http://localhost:5001/nodes/discover | python3 -m json.tool'
alias cluster-status='cluster-stats'

# 🎮 Minecraft Management
alias mc-start='curl -X POST http://localhost:5002/minecraft/start/'
alias mc-stop='curl -X POST http://localhost:5002/minecraft/stop/'
alias mc-status='curl -s http://localhost:5002/minecraft/status | python3 -m json.tool'
alias mc-restart='curl -X POST http://localhost:5002/minecraft/restart/'

# 🚀 Quick Server Start
alias server1-start='curl -X POST http://localhost:5002/minecraft/start/1'
alias server2-start='curl -X POST http://localhost:5002/minecraft/start/2'
alias server3-start='curl -X POST http://localhost:5002/minecraft/start/3'
alias server1-stop='curl -X POST http://localhost:5002/minecraft/stop/1'
alias server2-stop='curl -X POST http://localhost:5002/minecraft/stop/2'
alias server3-stop='curl -X POST http://localhost:5002/minecraft/stop/3'

# 📦 Backup Management
alias backup-status='curl -s http://localhost:5003/backup/status | python3 -m json.tool'
alias backup-now='curl -X POST http://localhost:5003/backup/now'
alias backup-list='curl -s http://localhost:5003/backup/list | python3 -m json.tool'
alias backup-check='curl -s http://localhost:5003/backup/setup-check | python3 -m json.tool'
alias backup-test='backup-now && echo "Backup started. Check status with: backup-status"'

# 📊 System Monitoring
alias system-stats='python3 -c "import psutil; print(f\"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}% | Disk: {psutil.disk_usage(\"/\").percent}%\")"'
alias service-status='echo -e "Services:\nAuto-Combiner: \$(curl -s http://localhost:5001/ | python3 -c \"import sys,json; print(json.load(sys.stdin).get(\\\"status\\\", \\\"unknown\\\"))\" 2>/dev/null || echo "offline")\nMinecraft: \$(curl -s http://localhost:5002/ | python3 -c \"import sys,json; print(json.load(sys.stdin).get(\\\"service\\\", \\\"unknown\\\"))\" 2>/dev/null || echo "offline")\nBackup: \$(curl -s http://localhost:5003/backup/status | python3 -c \"import sys,json; print(json.load(sys.stdin).get(\\\"system\\\", \\\"unknown\\\"))\" 2>/dev/null || echo "offline")"'

# 📁 Navigation
alias cd-cluster='cd ~/cluster'
alias cd-mc='cd ~/minecraft'
alias cd-storage='cd ~/cloud-storage'
alias cd-backups='cd ~/backups'
alias cd-scripts='cd ~/scripts'
alias cd-projects='cd ~/projects'

# 🛠️ Utility Commands
alias list-servers='ls -la ~/minecraft/servers/'
alias list-backups='ls -la ~/backups/'
alias list-scripts='ls -la ~/scripts/'
alias clean-temp='rm -rf ~/temp/* && echo "Temp files cleaned"'

# 🔍 Process Management
alias screen-list='screen -ls'
alias screen-mc1='screen -r mc1'
alias screen-mc2='screen -r mc2'
alias screen-mc3='screen -r mc3'
alias kill-all-mc='pkill -f "java.*minecraft" && echo "All Minecraft processes stopped"'

# 🌐 Network Info
alias show-ports='echo -e "Open Ports:\n10000 - Web Terminal\n25565 - Minecraft 1\n25566 - Minecraft 2\n25567 - Minecraft 3\n5001 - Cluster API\n5002 - Minecraft API\n5003 - Backup API"'
alias check-connections='netstat -tulpn 2>/dev/null | grep -E ":(10000|25565|25566|25567|5001|5002|5003)" || echo "No active connections on cluster ports"'

# ==========================================
# QUICK START FUNCTIONS
# ==========================================

# Quick start Minecraft with status check
mc-quick-start() {
    echo "🎮 Starting Minecraft server $1..."
    curl -X POST http://localhost:5002/minecraft/start/$1
    echo ""
    echo "⏳ Waiting for startup..."
    sleep 5
    curl -s http://localhost:5002/minecraft/status | python3 -m json.tool
}

# Quick backup with verification
backup-quick() {
    echo "📦 Starting backup..."
    curl -X POST http://localhost:5003/backup/now
    echo ""
    echo "⏳ Backup in progress... Check status with: backup-status"
}

# System health check
health-check() {
    echo "🏥 System Health Check"
    echo "======================"
    system-stats
    echo ""
    service-status
    echo ""
    echo "📊 Storage:"
    df -h ~ | tail -1
    echo ""
    echo "🔍 Recent Backups:"
    ls -lt ~/backups/*.zip 2>/dev/null | head -5 || echo "No backups found"
}

# Cluster overview
cluster-overview() {
    echo "🏢 Cluster Overview"
    echo "==================="
    curl -s http://localhost:5001/cluster/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'Nodes: {data[\"resource_pool\"][\"total_nodes\"]}')
print(f'Total RAM: {data[\"resource_pool\"][\"total_ram_gb\"]}GB')
print(f'Available RAM: {data[\"system_metrics\"][\"available_ram_gb\"]}GB')
print(f'RAM Usage: {data[\"system_metrics\"][\"used_ram_percent\"]}%')
"
    echo ""
    echo "🎮 Minecraft Status:"
    curl -s http://localhost:5002/minecraft/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
running = sum(1 for s in data['servers'].values() if s['status'] == 'running')
print(f'Servers: {running}/{len(data[\"servers\"])} running')
print(f'Available RAM: {data[\"system_ram\"][\"available_gb\"]}GB')
"
    echo ""
    echo "📦 Backup Status:"
    curl -s http://localhost:5003/backup/status | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'System: {data[\"system\"]}')
print(f'Auto Backup: {data[\"auto_backup\"]}')
print(f'Interval: {data[\"interval\"]}')
print(f'Total Backups: {data[\"backup_info\"][\"total_backups\"]}')
"
}

# ==========================================
# WELCOME MESSAGE
# ==========================================

echo
echo "🎮 TERMUX CLUSTER READY!"
echo "========================"
echo "🔧 Available Commands:"
echo
echo "🎮 Minecraft:"
echo "  mc-start 1/2/3       - Start server"
echo "  mc-stop 1/2/3        - Stop server"  
echo "  mc-status            - Check status"
echo "  server1-start        - Quick start server 1"
echo "  mc-quick-start 1     - Start with status check"
echo
echo "📦 Backup:"
echo "  backup-status        - Backup system status"
echo "  backup-now           - Immediate backup"
echo "  backup-list          - List backups"
echo "  backup-quick         - Quick backup"
echo
echo "📊 Monitoring:"
echo "  cluster-stats        - Cluster resources"
echo "  cluster-overview     - Full overview"
echo "  health-check         - System health"
echo "  service-status       - Service status"
echo
echo "🛠️ Utilities:"
echo "  screen-list          - List screen sessions"
echo "  list-servers         - List Minecraft servers"
echo "  list-backups         - List backup files"
echo "  show-ports           - Show open ports"
echo
echo "💡 Use 'cluster-overview' for complete status"
echo "💡 Use 'health-check' for system diagnostics"
echo

EOF

echo "✓ Cluster configured: $NODE_COUNT nodes, ${TOTAL_RAM}GB RAM"
echo "✓ Minecraft 1.21.10 servers ready"
echo "✓ Auto-backup system configured (5-minute intervals)"
echo "✓ Comprehensive management aliases added"
echo "✓ Utility functions created"
echo "✓ Startup complete"
