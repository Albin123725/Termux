#!/usr/bin/env python3
import os
import json
import time
import zipfile
import datetime
import subprocess
import threading
from pathlib import Path

class AutoBackup:
    def __init__(self):
        self.backup_dir = Path('~/backups').expanduser()
        self.config_file = Path('~/.config/gdrive/backup_config.json').expanduser()
        self.interval = 300  # 5 minutes in seconds
        self.load_config()
        
    def load_config(self):
        """Load backup configuration"""
        default_config = {
            'enabled': True,
            'interval_minutes': 5,
            'keep_local_backups': 5,
            'backup_paths': [
                '~/minecraft',
                '~/cluster',
                '~/scripts',
                '~/cloud-storage'
            ]
        }
        
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save backup configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_backup_zip(self):
        """Create a backup zip file"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'cluster_backup_{timestamp}.zip'
        
        print(f"📦 Creating backup: {backup_file.name}")
        
        try:
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for path_spec in self.config['backup_paths']:
                    path = Path(path_spec).expanduser()
                    if path.exists():
                        if path.is_file():
                            zipf.write(path, path.name)
                        else:
                            for file_path in path.rglob('*'):
                                if file_path.is_file():
                                    # Skip large or temporary files
                                    if self.should_include_file(file_path):
                                        arcname = file_path.relative_to(Path.home())
                                        zipf.write(file_path, arcname)
            
            # Get file size
            file_size = backup_file.stat().st_size / (1024 * 1024)  # MB
            print(f"✅ Backup created: {backup_file.name} ({file_size:.2f} MB)")
            
            # Sync to Google Drive
            self.sync_to_gdrive(backup_file)
            
            # Clean up old backups
            self.cleanup_old_backups()
            
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False
    
    def should_include_file(self, file_path):
        """Check if file should be included in backup"""
        exclude_extensions = ['.tmp', '.log', '.cache']
        exclude_dirs = ['logs', 'cache', 'temp']
        
        if file_path.suffix in exclude_extensions:
            return False
        
        for exclude_dir in exclude_dirs:
            if exclude_dir in file_path.parts:
                return False
        
        # Skip files larger than 100MB
        if file_path.stat().st_size > 100 * 1024 * 1024:
            return False
            
        return True
    
    def sync_to_gdrive(self, backup_file):
        """Sync backup to Google Drive using rclone"""
        try:
            print("☁️  Syncing to Google Drive...")
            
            # Upload to Google Drive
            result = subprocess.run([
                'rclone', 'copy', str(backup_file), 'gdrive:Termux-Cluster-Backups/',
                '--progress', '-v'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Backup synced to Google Drive")
                return True
            else:
                print(f"❌ Rclone error: {result.stderr}")
                return False
            
        except Exception as e:
            print(f"❌ Sync error: {e}")
            return False
    
    def cleanup_old_backups(self):
        """Remove old local backup files"""
        try:
            backup_files = sorted(
                self.backup_dir.glob('cluster_backup_*.zip'),
                key=lambda x: x.stat().st_ctime
            )
            
            # Keep only the most recent backups
            keep_count = self.config.get('keep_local_backups', 5)
            if len(backup_files) > keep_count:
                for old_file in backup_files[:-keep_count]:
                    old_file.unlink()
                    print(f"🗑️  Removed old backup: {old_file.name}")
                    
        except Exception as e:
            print(f"⚠️  Cleanup error: {e}")
    
    def backup_minecraft_worlds(self):
        """Special backup for Minecraft worlds"""
        try:
            print("🎮 Backup Minecraft worlds...")
            
            # Force save on all Minecraft servers
            result = subprocess.run(['screen', '-ls'], capture_output=True, text=True)
            mc_servers = [line for line in result.stdout.split('\n') if 'mc' in line and 'Attached' not in line]
            
            for server_line in mc_servers:
                if 'mc' in server_line:
                    try:
                        screen_name = server_line.split('.')[1].split('\t')[0]
                        print(f"💾 Saving world on {screen_name}...")
                        subprocess.run([
                            'screen', '-S', screen_name, '-X', 'stuff', 'save-all\\n'
                        ], capture_output=True, timeout=5)
                        time.sleep(2)  # Wait for save to complete
                    except:
                        continue
            
            # Create Minecraft-specific backup
            minecraft_backup_dir = self.backup_dir / 'minecraft'
            minecraft_backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            minecraft_zip = minecraft_backup_dir / f'minecraft_{timestamp}.zip'
            
            minecraft_path = Path('~/minecraft').expanduser()
            if minecraft_path.exists():
                with zipfile.ZipFile(minecraft_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for server_dir in minecraft_path.glob('*'):
                        if server_dir.is_dir():
                            for world_file in server_dir.rglob('*'):
                                if world_file.is_file() and self.should_include_file(world_file):
                                    arcname = world_file.relative_to(minecraft_path)
                                    zipf.write(world_file, arcname)
                
                print(f"✅ Minecraft backup: {minecraft_zip.name}")
                
                # Sync Minecraft backup
                self.sync_to_gdrive(minecraft_zip)
            
        except Exception as e:
            print(f"❌ Minecraft backup failed: {e}")
    
    def start_auto_backup(self):
        """Start automatic backup loop"""
        print(f"🔄 Auto-backup started (every {self.interval} seconds)")
        print(f"📁 Backup paths: {self.config['backup_paths']}")
        
        backup_count = 0
        
        while True:
            try:
                if self.config.get('enabled', True):
                    backup_count += 1
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"\n🕒 Backup #{backup_count} at {current_time}")
                    
                    # Create main backup
                    self.create_backup_zip()
                    
                    # Create Minecraft worlds backup
                    self.backup_minecraft_worlds()
                    
                    print(f"✅ Backup #{backup_count} completed")
                    print(f"⏰ Next backup in {self.interval} seconds...")
                
                time.sleep(self.interval)
                
            except KeyboardInterrupt:
                print("\n🛑 Backup system stopped")
                break
            except Exception as e:
                print(f"❌ Backup loop error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying

# Global instance
backup_manager = AutoBackup()

if __name__ == '__main__':
    print("🔄 Auto-Backup System Starting...")
    backup_manager.start_auto_backup()
