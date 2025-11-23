#!/usr/bin/env python3
import subprocess
import os
import time
import psutil
import requests
from flask import Flask, jsonify

app = Flask(__name__)

class AdaptiveMinecraft:
    def __init__(self):
        self.combiner_url = "http://localhost:5001"
        self.version = "1.21.10"
        self.update_config()
        
    def update_config(self):
        """Get adaptive configuration from combiner"""
        try:
            response = requests.get(f"{self.combiner_url}/resources/adaptive", timeout=5)
            config = response.json()
            self.adaptive_config = config['minecraft']
            self.setup_servers()
            return True
        except:
            # Fallback configuration
            self.adaptive_config = {
                'max_servers': 1,
                'ram_per_server': 6,
                'strategy': 'fallback'
            }
            self.setup_servers()
            return False
    
    def setup_servers(self):
        """Setup servers based on adaptive configuration"""
        self.servers = {}
        
        for i in range(1, self.adaptive_config['max_servers'] + 1):
            ram_config = self.get_ram_config(i)
            self.servers[str(i)] = {
                'port': 25564 + i,
                'memory_xmx': f"{ram_config['xmx']}G",
                'memory_xms': f"{ram_config['xms']}G",
                'status': 'stopped',
                'screen_session': f'mc-adaptive-{i}',
                'directory': f'/home/termux/minecraft/servers/server-{i}',
                'strategy': self.adaptive_config['strategy']
            }
    
    def get_ram_config(self, server_id):
        """Get RAM configuration based on adaptive strategy"""
        base_ram = self.adaptive_config['ram_per_server']
        
        if self.adaptive_config['strategy'] == 'high-performance':
            return {'xmx': base_ram, 'xms': 2}
        elif self.adaptive_config['strategy'] == 'balanced':
            return {'xmx': base_ram, 'xms': 1}
        else:  # single-node or fallback
            return {'xmx': 6, 'xms': 2}
    
    def download_server(self, server_dir):
        """Download Minecraft server"""
        server_jar = f"{server_dir}/minecraft_server.jar"
        if not os.path.exists(server_jar):
            print(f"📥 Downloading Minecraft {self.version}...")
            try:
                subprocess.run([
                    "wget", "-O", server_jar,
                    "https://piston-data.mojang.com/v1/objects/7b40b8b0c3b6b3d8b0b8b0c3b6b3d8b0b8b0c3b6/minecraft_server.1.21.10.jar"
                ], check=True, capture_output=True)
            except:
                # Try alternative URL
                subprocess.run([
                    "wget", "-O", server_jar,
                    "https://piston-data.mojang.com/v1/objects/7b40b8b0c3b6b3d8b0b8b0c3b6b3d8b0b8b0c3b6/server.jar"
                ], capture_output=True)
        
        # Auto-accept EULA
        eula_file = f"{server_dir}/eula.txt"
        if not os.path.exists(eula_file):
            with open(eula_file, 'w') as f:
                f.write("eula=true\n")
    
    def can_start_server(self, server_id):
        """Check if server can start with current resources"""
        server_ram = int(self.servers[server_id]['memory_xmx'].replace('G', ''))
        memory = psutil.virtual_memory()
        available_gb = memory.available / (1024**3)
        
        # Adaptive threshold based on strategy
        if self.adaptive_config['strategy'] == 'high-performance':
            return available_gb >= server_ram
        else:
            return available_gb >= (server_ram + 1)  # Extra buffer
    
    def start_server(self, server_id):
        if not self.update_config():
            return {"success": False, "error": "Failed to get adaptive configuration"}
            
        if server_id not in self.servers:
            return {"success": False, "error": f"Server {server_id} not available"}
            
        if not self.can_start_server(server_id):
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            required_gb = int(self.servers[server_id]['memory_xmx'].replace('G', ''))
            
            return {
                "success": False,
                "error": f"Not enough RAM. Available: {available_gb:.1f}GB, Required: {required_gb}GB",
                "adaptive_config": self.adaptive_config
            }
        
        try:
            server_data = self.servers[server_id]
            server_dir = server_data['directory']
            os.makedirs(server_dir, exist_ok=True)
            
            # Download server
            self.download_server(server_dir)
            
            # Create adaptive start script
            start_script = f"{server_dir}/start.sh"
            with open(start_script, 'w') as f:
                f.write(f"""#!/bin/bash
cd {server_dir}
echo "🎮 Adaptive Minecraft Server {server_id}"
echo "💾 RAM: {server_data['memory_xmx']} (Auto-configured)"
echo "⚡ Strategy: {server_data['strategy']}"
echo "🌐 Port: {server_data['port']}"
java -Xmx{server_data['memory_xmx']} -Xms{server_data['memory_xms']} -jar minecraft_server.jar nogui
""")
            os.chmod(start_script, 0o755)
            
            # Start server
            subprocess.run([
                "screen", "-dmS", server_data['screen_session'], "bash", start_script
            ], check=True)
            
            self.servers[server_id]['status'] = 'running'
            
            return {
                "success": True,
                "message": f"Minecraft Server {server_id} started (Adaptive Mode)",
                "server": server_data,
                "adaptive_config": self.adaptive_config
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def stop_server(self, server_id):
        if server_id in self.servers:
            try:
                screen_session = self.servers[server_id]['screen_session']
                subprocess.run([
                    "screen", "-S", screen_session, "-X", "stuff", "stop\\n"
                ], capture_output=True)
                time.sleep(5)
                subprocess.run([
                    "screen", "-S", screen_session, "-X", "quit"
                ], capture_output=True)
                self.servers[server_id]['status'] = 'stopped'
                return {"success": True, "message": f"Server {server_id} stopped"}
            except:
                return {"success": False, "error": "Failed to stop server"}
        return {"success": False, "error": "Server not found"}
    
    def get_status(self):
        self.update_config()
        memory = psutil.virtual_memory()
        
        # Check server status
        for server_id in self.servers:
            result = subprocess.run(["screen", "-ls"], capture_output=True, text=True)
            if self.servers[server_id]['screen_session'] in result.stdout:
                self.servers[server_id]['status'] = 'running'
            else:
                self.servers[server_id]['status'] = 'stopped'
        
        return {
            "adaptive_system": {
                "enabled": True,
                "config": self.adaptive_config,
                "server_count": len(self.servers)
            },
            "resources": {
                "available_ram_gb": round(memory.available / (1024**3), 2),
                "total_ram_gb": round(memory.total / (1024**3), 2),
                "ram_percent": memory.percent
            },
            "servers": self.servers,
            "version": self.version
        }

mc_manager = AdaptiveMinecraft()

@app.route('/')
def home():
    return jsonify({
        "service": "Adaptive Minecraft Manager",
        "version": "1.21.10",
        "adaptive": True
    })

@app.route('/minecraft/status')
def minecraft_status():
    return jsonify(mc_manager.get_status())

@app.route('/minecraft/start/<server_id>', methods=['POST'])
def start_minecraft(server_id):
    return jsonify(mc_manager.start_server(server_id))

@app.route('/minecraft/stop/<server_id>', methods=['POST'])
def stop_minecraft(server_id):
    return jsonify(mc_manager.stop_server(server_id))

if __name__ == '__main__':
    print("🎮 Adaptive Minecraft Manager Started")
    print("⚡ Auto-combining mode: ACTIVE")
    mc_manager.update_config()
    app.run(host='0.0.0.0', port=5002, threaded=True)
