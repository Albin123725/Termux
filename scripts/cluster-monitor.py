#!/usr/bin/env python3
import time
import psutil
import requests
import json

class ClusterMonitor:
    def __init__(self):
        self.combiner_url = "http://localhost:5001"
        self.minecraft_url = "http://localhost:5002"
        
    def get_system_stats(self):
        """Get system statistics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': time.time(),
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'used_percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'used_percent': disk.percent
            },
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'cores': psutil.cpu_count()
            }
        }
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while True:
            try:
                # Get cluster status
                cluster_status = requests.get(f"{self.combiner_url}/cluster/status").json()
                minecraft_status = requests.get(f"{self.minecraft_url}/minecraft/status").json()
                system_stats = self.get_system_stats()
                
                # Save to cluster log
                log_entry = {
                    'cluster': cluster_status,
                    'minecraft': minecraft_status,
                    'system': system_stats
                }
                
                with open('/home/termux/cluster/monitor.log', 'a') as f:
                    f.write(json.dumps(log_entry) + '\n')
                
                print(f"📊 Monitor: {cluster_status['resource_pool']['total_nodes']} nodes | "
                      f"RAM: {system_stats['memory']['available_gb']}GB free | "
                      f"MC: {len([s for s in minecraft_status['servers'].values() if s['status'] == 'running'])} running")
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(120)

if __name__ == '__main__':
    print("📊 Cluster Monitor Started")
    monitor = ClusterMonitor()
    monitor.monitor_loop()
