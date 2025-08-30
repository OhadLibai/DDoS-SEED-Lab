#!/bin/bash
# Shared GCP Instance Startup Script for HTTP/2 Labs
# Template script used by all labs with parameterization

set -e

LAB_NAME="${lab_name}"
APACHE_VERSION="${apache_version}"
ATTACK_SCRIPT="${attack_script}"
DEFAULT_CONNECTIONS="${default_connections}"

# Update system
apt-get update
apt-get install -y docker.io docker-compose python3 python3-pip curl htop at

# Start Docker service
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Create lab directory
mkdir -p /opt/$LAB_NAME
cd /opt/$LAB_NAME

# Create docker-compose for specified Apache version
cat > docker-compose.yml << EOF
services:
  apache-victim:
    image: httpd:$APACHE_VERSION
    container_name: apache-$LAB_NAME-victim
    ports:
      - "80:80"
    volumes:
      - ./html:/usr/local/apache2/htdocs
    command: >
      sh -c "sed -i 's/#LoadModule http2_module/LoadModule http2_module/' /usr/local/apache2/conf/httpd.conf &&
             grep -q 'Protocols h2 h2c http/1.1' /usr/local/apache2/conf/httpd.conf || echo 'Protocols h2 h2c http/1.1' >> /usr/local/apache2/conf/httpd.conf &&
             httpd-foreground"
    restart: unless-stopped

networks:
  default:
    driver: bridge
EOF

# Create HTML content
mkdir -p html
cat > html/index.html << EOF
<html><body><h1>$LAB_NAME Target Server</h1><p>Apache $APACHE_VERSION - HTTP/2 Enabled</p></body></html>
EOF

# Create large test file
dd if=/dev/zero of=html/large-test.jpg bs=1M count=10

# Install Python dependencies
pip3 install h2 requests

# Download attack scripts from GitHub repository
# Note: In production, scripts should be embedded or downloaded from secure source
cd /opt/$LAB_NAME

# Create temporary script to download from our repository
cat > download_scripts.sh << 'DOWNLOAD_EOF'
#!/bin/bash
# Download attack scripts - Update URL to your repository
REPO_URL="https://raw.githubusercontent.com/your-username/DDOS-Sandbox/main"

echo "Downloading attack scripts..."
curl -o zero_window_attack.py "$REPO_URL/shared/scripts/zero_window_attack.py" || echo "Download failed - using local placeholder"
curl -o slow_inc_window_attack.py "$REPO_URL/shared/scripts/slow_inc_window_attack.py" || echo "Download failed - using local placeholder" 
curl -o adv_slow_inc_window_attack.py "$REPO_URL/shared/scripts/adv_slow_inc_window_attack.py" || echo "Download failed - using local placeholder"

chmod +x *.py
echo "Attack scripts downloaded to /opt/$LAB_NAME/"
DOWNLOAD_EOF

chmod +x download_scripts.sh

# For now, create a working placeholder until scripts are available
cat > $ATTACK_SCRIPT << 'SCRIPT_EOF'
#!/usr/bin/env python3
"""
Placeholder attack script - replace with actual implementation
To get real scripts:
1. Clone repository: git clone https://github.com/your-username/DDOS-Sandbox.git
2. Copy scripts: cp DDOS-Sandbox/shared/scripts/*.py /opt/$LAB_NAME/
3. Run attack: python3 $ATTACK_SCRIPT localhost --port 80 --connections $DEFAULT_CONNECTIONS
"""

print("=== HTTP/2 Attack Placeholder ===")
print("This is a placeholder script.")
print("To run real attacks, copy the actual scripts from the repository:")
print("scp shared/scripts/*.py ubuntu@INSTANCE_IP:/opt/$LAB_NAME/")
print("")
print(f"Then run: python3 {ATTACK_SCRIPT} localhost --port 80 --connections {DEFAULT_CONNECTIONS}")
SCRIPT_EOF

chmod +x $ATTACK_SCRIPT

# Start Apache
docker-compose up -d

# Auto-shutdown after 2 hours (safety)
echo "sudo shutdown -h now" | at now + 2 hours

# Create monitoring script
cat > /opt/$LAB_NAME/monitor.sh << 'EOF'
#!/bin/bash
echo "=== LAB_NAME Live Monitoring ==="
echo "Time: $(date)"
echo ""
echo "=== Docker Stats ==="
docker stats --no-stream
echo ""
echo "=== Network Connections ==="
ss -tuln | grep :80 | wc -l | xargs echo "Active connections on port 80:"
echo ""
echo "=== Server Response Test ==="
curl -w "Response Time: %{time_total}s\n" -s -o /dev/null http://localhost/
EOF

# Replace LAB_NAME placeholder
sed -i "s/LAB_NAME/$LAB_NAME/g" /opt/$LAB_NAME/monitor.sh
chmod +x /opt/$LAB_NAME/monitor.sh

echo "$LAB_NAME GCP setup complete!"
echo "Access: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google')"