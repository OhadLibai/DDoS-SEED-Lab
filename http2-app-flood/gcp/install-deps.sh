#!/bin/bash
# GCP VM Dependency Installation Script

set -e

# Redirect all output to log file
exec > /var/log/startup.log 2>&1

echo "[$(date)] Starting HTTP/2 Flood Lab setup..."

# Update system
echo "[$(date)] Updating system packages..."
apt-get update
apt-get upgrade -y

# Install Docker
echo "[$(date)] Installing Docker..."
apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io

# Install Docker Compose
echo "[$(date)] Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# Install additional tools
echo "[$(date)] Installing additional tools..."
apt-get install -y git htop curl wget at

# Add default user to docker group
echo "[$(date)] Configuring Docker permissions..."
usermod -aG docker $(whoami) 2>/dev/null || true
usermod -aG docker ubuntu 2>/dev/null || true

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Verify installations
echo "[$(date)] Verifying installations..."
docker --version
docker-compose --version

# Auto-shutdown after 2 hours (cost safety)
echo "[$(date)] Setting up auto-shutdown in 2 hours for cost protection..."
echo "sudo shutdown -h now" | at now + 2 hours

echo "[$(date)] HTTP/2 Flood Lab setup completed successfully!"
echo "[$(date)] Ready for lab deployment."
echo "[$(date)] VM will auto-shutdown in 2 hours to prevent unexpected costs."