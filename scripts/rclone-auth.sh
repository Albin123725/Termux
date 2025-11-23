#!/bin/bash

echo "🔐 Google Drive Authentication Setup"

# Check if rclone is installed
if ! command -v rclone &> /dev/null; then
    echo "📥 Installing rclone..."
    curl -O https://downloads.rclone.org/rclone-current-linux-amd64.zip
    unzip rclone-current-linux-amd64.zip
    cd rclone-*-linux-amd64
    sudo cp rclone /usr/bin/
    sudo chmod +x /usr/bin/rclone
    sudo mkdir -p /usr/local/share/man/man1
    sudo cp rclone.1 /usr/local/share/man/man1/
    sudo mandb
    cd ..
    rm -rf rclone-*
fi

echo "🔗 Starting rclone configuration..."
echo "💡 When prompted:"
echo "   - Choose 'n' for New remote"
echo "   - Name it 'gdrive'"
echo "   - Choose '15' for Google Drive"
echo "   - Leave client_id and client_secret empty (press Enter)"
echo "   - Choose '1' for full access"
echo "   - Choose 'n' for not using advanced config"
echo "   - Choose 'n' for auto config (we'll use your existing credentials)"
echo "   - Use your Google account to authenticate"

rclone config

echo "✅ Rclone setup complete!"
echo "🔧 Testing connection..."
rclone ls gdrive:/

echo "🎉 Google Drive backup system ready!"
