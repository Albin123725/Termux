#!/usr/bin/env python3
import os
import json
import subprocess
from pathlib import Path

class GoogleDriveAuth:
    def __init__(self):
        self.config_dir = Path('~/.config/gdrive').expanduser()
        self.credentials_file = self.config_dir / 'credentials.json'
        self.setup_directories()
        
    def setup_directories(self):
        """Create necessary directories"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        Path('~/backups').expanduser().mkdir(parents=True, exist_ok=True)
        Path('~/backups/minecraft').expanduser().mkdir(parents=True, exist_ok=True)
        
    def setup_rclone(self):
        """Setup rclone with Google Drive"""
        print("🔧 Setting up rclone with Google Drive...")
        
        # Create rclone config directory
        rclone_config_dir = Path('~/.config/rclone').expanduser()
        rclone_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure rclone
        config_content = f"""[gdrive]
type = drive
client_id = 740511594522-ofu7utfiedtpemu0cg9ghommdqoicbjf.apps.googleusercontent.com
client_secret = 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
scope = drive.file
root_folder_id = 
token = 
"""
        
        config_file = rclone_config_dir / 'rclone.conf'
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        print("✅ Rclone config created")
        print("💡 Run 'rclone config' to complete authentication")
        
    def save_credentials(self):
        """Save the credentials file"""
        credentials_data = {
            "installed": {
                "client_id": "740511594522-ofu7utfiedtpemu0cg9ghommdqoicbjf.apps.googleusercontent.com",
                "project_id": "termux-479006",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": "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",
                "redirect_uris": ["http://localhost"]
            }
        }
        
        with open(self.credentials_file, 'w') as f:
            json.dump(credentials_data, f, indent=2)
        
        print("✅ Google Drive credentials saved")

if __name__ == '__main__':
    auth = GoogleDriveAuth()
    auth.save_credentials()
    auth.setup_rclone()
    print("🎯 Google Drive setup complete!")
    print("🔗 Run: rclone config to authenticate")
