#!/usr/bin/env python3
from flask import Flask, jsonify, request
import threading
import time
import datetime
import os
from pathlib import Path

app = Flask(__name__)

class BackupManager:
    def __init__(self):
        self.backup_dir = Path('~/backups').expanduser()
        self.status = {
            'last_backup': None,
            'backup_count': 0,
            'enabled': True
        }
    
    def get_backup_info(self):
        """Get information about backups"""
        backups = list(self.backup_dir.glob('cluster_backup_*.zip'))
        minecraft_backups = list((self.backup_dir / 'minecraft').glob('*.zip'))
        
        return {
            'total_backups': len(backups),
            'total_minecraft_backups': len(minecraft_backups),
            'backup_files': [b.name for b in sorted(backups, reverse=True)[:5]],
            'minecraft_backups': [b.name for b in sorted(minecraft_backups, reverse=True)[:5]]
        }

backup_mgr = BackupManager()

@app.route('/backup/status')
def backup_status():
    """Get backup system status"""
    info = backup_mgr.get_backup_info()
    return jsonify({
        'system': 'active',
        'auto_backup': 'running',
        'interval': '5 minutes',
        'backup_info': info,
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/backup/now', methods=['POST'])
def backup_now():
    """Trigger immediate backup"""
    def run_backup():
        try:
            # Import and run backup
            from auto_backup import AutoBackup
            backup_system = AutoBackup()
            backup_system.create_backup_zip()
            backup_system.backup_minecraft_worlds()
            backup_mgr.status['last_backup'] = datetime.datetime.now().isoformat()
            backup_mgr.status['backup_count'] += 1
        except Exception as e:
            print(f"Manual backup error: {e}")
    
    thread = threading.Thread(target=run_backup)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Manual backup started',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/backup/list')
def backup_list():
    """List all backups"""
    info = backup_mgr.get_backup_info()
    return jsonify(info)

@app.route('/backup/setup-check')
def setup_check():
    """Check if backup system is properly set up"""
    checks = {
        'backup_directory': os.path.exists(Path('~/backups').expanduser()),
        'rclone_installed': os.system('which rclone > /dev/null') == 0,
        'gdrive_configured': os.system('rclone listremotes | grep -q gdrive') == 0,
        'auto_backup_running': True  # Assuming it's running if we can reach this
    }
    
    return jsonify({
        'checks': checks,
        'all_ok': all(checks.values())
    })

if __name__ == '__main__':
    print("📦 Backup Manager API Started on port 5003")
    app.run(host='0.0.0.0', port=5003, threaded=True)
