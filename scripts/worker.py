#!/usr/bin/env python3
from flask import Flask, request, jsonify
import os
import time

app = Flask(__name__)

@app.route('/')
def home():
    return {
        "node_id": os.environ.get('NODE_ID', 'worker'),
        "role": os.environ.get('NODE_ROLE', 'compute'),
        "status": "ready",
        "auto_combine": True,
        "version": "1.0"
    }

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "node_id": os.environ.get('NODE_ID', 'worker'),
        "timestamp": time.time()
    })

@app.route('/combine')
def combine():
    """Endpoint for auto-combining"""
    return jsonify({
        "available_ram_gb": 2,  # Workers contribute 2GB
        "services": ["compute", "storage"],
        "status": "ready_to_combine"
    })

if __name__ == '__main__':
    print(f"👷 Worker {os.environ.get('NODE_ID')} Started - Auto-Combine Ready")
    app.run(host='0.0.0.0', port=5000)
