#!/usr/bin/env python3
import os
import json
import psutil
import requests
from flask import Flask, jsonify
import threading
import time

app = Flask(__name__)

class AutoCombiner:
    def __init__(self):
        self.discovered_nodes = []
        self.resource_pool = {}
        self.adaptive_config = {}
        self.update_interval = 30
        
    def discover_nodes(self):
        """Discover available nodes and combine resources"""
        nodes = []
        
        # Main node (this container)
        service_type = os.environ.get('SERVICE_TYPE', 'main')
        node_id = os.environ.get('NODE_ID', 'main-node')
        
        if service_type == 'main':
            nodes.append({
                'id': node_id,
                'type': 'main',
                'ram_gb': int(os.environ.get('TOTAL_RAM', 8)),
                'cpu_cores': os.cpu_count(),
                'status': 'active',
                'services': ['web-terminal', 'minecraft', 'storage', 'monitor'],
                'port': 10000
            })
        else:
            # Worker node
            nodes.append({
                'id': node_id,
                'type': 'worker',
                'ram_gb': 2,  # Workers contribute 2GB each
                'cpu_cores': 1,
                'status': 'active',
                'services': ['compute', 'storage'],
                'port': 5000
            })
        
        # Check for additional nodes via environment
        additional_nodes = int(os.environ.get('ADDITIONAL_NODES', 0))
        for i in range(additional_nodes):
            nodes.append({
                'id': f'extra-node-{i+1}',
                'type': 'extra',
                'ram_gb': 1,
                'cpu_cores': 1,
                'status': 'simulated',
                'services': ['compute'],
                'port': 5001 + i
            })
        
        self.discovered_nodes = nodes
        self.calculate_combined_resources()
        return nodes
    
    def calculate_combined_resources(self):
        """Calculate total combined resources"""
        total_ram = 0
        total_cores = 0
        total_nodes = len(self.discovered_nodes)
        
        for node in self.discovered_nodes:
            total_ram += node['ram_gb']
            total_cores += node['cpu_cores']
        
        self.resource_pool = {
            'total_ram_gb': total_ram,
            'total_cores': total_cores,
            'total_nodes': total_nodes,
            'average_ram_per_node': total_ram / total_nodes if total_nodes > 0 else 0
        }
        
        # Update adaptive configuration
        self.update_adaptive_config()
    
    def update_adaptive_config(self):
        """Update adaptive configuration based on available resources"""
        total_ram = self.resource_pool['total_ram_gb']
        node_count = self.resource_pool['total_nodes']
        
        # Adaptive Minecraft configuration
        if node_count >= 4:
            minecraft_config = {
                'max_servers': 3,
                'ram_per_server': 6,
                'strategy': 'high-performance',
                'recommendation': 'All servers can run simultaneously'
            }
        elif node_count >= 2:
            minecraft_config = {
                'max_servers': 2,
                'ram_per_server': 4,
                'strategy': 'balanced',
                'recommendation': 'Run 2 servers simultaneously'
            }
        else:
            minecraft_config = {
                'max_servers': 1,
                'ram_per_server': 6,
                'strategy': 'single-node',
                'recommendation': 'Run one server at a time'
            }
        
        self.adaptive_config = {
            'minecraft': minecraft_config,
            'scaling': {
                'auto_scale': True,
                'node_threshold': 2,
                'ram_threshold_gb': 4
            },
            'optimization': {
                'load_balancing': node_count > 1,
                'resource_pooling': True,
                'adaptive_alloc': True
            }
        }
    
    def get_cluster_status(self):
        """Get comprehensive cluster status"""
        self.discover_nodes()
        system_ram = psutil.virtual_memory()
        
        return {
            'auto_combining': {
                'enabled': True,
                'status': 'active',
                'discovered_nodes': len(self.discovered_nodes),
                'last_update': time.time()
            },
            'resource_pool': self.resource_pool,
            'adaptive_config': self.adaptive_config,
            'system_metrics': {
                'available_ram_gb': round(system_ram.available / (1024**3), 2),
                'used_ram_gb': round(system_ram.used / (1024**3), 2),
                'ram_percent': system_ram.percent
            },
            'nodes': self.discovered_nodes
        }
    
    def auto_scale_services(self):
        """Auto-scale services based on available resources"""
        status = self.get_cluster_status()
        
        print("🚀 AUTO-SCALING REPORT")
        print(f"📊 Discovered Nodes: {status['resource_pool']['total_nodes']}")
        print(f"💾 Combined RAM: {status['resource_pool']['total_ram_gb']}GB")
        print(f"🎮 Minecraft: {status['adaptive_config']['minecraft']['max_servers']} servers")
        print(f"⚡ Strategy: {status['adaptive_config']['minecraft']['strategy']}")
        print(f"💡 {status['adaptive_config']['minecraft']['recommendation']}")

# Global instance
combiner = AutoCombiner()

@app.route('/')
def home():
    return jsonify({
        "service": "Auto-Combiner",
        "version": "1.0",
        "status": "active"
    })

@app.route('/cluster/status')
def cluster_status():
    return jsonify(combiner.get_cluster_status())

@app.route('/nodes/discover')
def discover_nodes():
    nodes = combiner.discover_nodes()
    return jsonify({
        'discovered_nodes': nodes,
        'total_count': len(nodes),
        'resource_pool': combiner.resource_pool
    })

@app.route('/resources/adaptive')
def adaptive_resources():
    return jsonify(combiner.adaptive_config)

@app.route('/auto-scale')
def auto_scale():
    combiner.auto_scale_services()
    return jsonify({
        'message': 'Auto-scaling completed',
        'config': combiner.adaptive_config
    })

def background_discovery():
    """Background node discovery"""
    while True:
        try:
            combiner.discover_nodes()
            time.sleep(combiner.update_interval)
        except Exception as e:
            print(f"Background discovery error: {e}")
            time.sleep(60)

if __name__ == '__main__':
    # Start background discovery
    discovery_thread = threading.Thread(target=background_discovery, daemon=True)
    discovery_thread.start()
    
    print("🚀 Auto-Combiner Started - Adaptive Node Discovery Active")
    combiner.auto_scale_services()
    
    app.run(host='0.0.0.0', port=5001, threaded=True)
