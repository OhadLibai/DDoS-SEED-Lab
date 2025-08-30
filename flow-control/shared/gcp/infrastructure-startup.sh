#!/bin/bash
# GCP Infrastructure Startup Script
# Sets up reusable environment for all HTTP/2 attack labs

set -e

# Update system and install base tools
apt-get update
apt-get install -y docker.io docker-compose python3 python3-pip curl htop at jq

# Start Docker service
systemctl enable docker
systemctl start docker

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Create lab directories structure
mkdir -p /opt/http2-labs/{shared,zero-window,slow-incremental,adaptive-slow}
mkdir -p /opt/http2-labs/shared/{scripts,monitoring,logs}

# Install Python dependencies for all labs
pip3 install h2 requests

# Install web-based terminal for browser access
curl -L https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 -o /usr/local/bin/ttyd
chmod +x /usr/local/bin/ttyd

# Create web terminal service
cat > /etc/systemd/system/web-terminal.service << EOF
[Unit]
Description=Web Terminal Service
After=network.target

[Service]
ExecStart=/usr/local/bin/ttyd -p 8080 -W /opt/http2-labs bash
Restart=always
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
EOF

systemctl enable web-terminal
systemctl start web-terminal

# Create lab management scripts
cat > /opt/http2-labs/shared/deploy-lab.sh << 'DEPLOY_EOF'
#!/bin/bash
# Lab deployment script - called by individual attack deploy scripts

LAB_NAME="$1"
APACHE_VERSION="$2"
ATTACK_SCRIPT="$3"
DEFAULT_CONNECTIONS="$4"

if [ -z "$LAB_NAME" ]; then
    echo "Usage: $0 <lab-name> <apache-version> <attack-script> <connections>"
    exit 1
fi

echo "=== Deploying $LAB_NAME ==="

# Stop any existing lab containers
docker-compose -f /opt/http2-labs/current-lab.yml down 2>/dev/null || true

# Create docker-compose for this lab
cat > /opt/http2-labs/current-lab.yml << EOF
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
    labels:
      - "lab.name=$LAB_NAME"
      - "lab.apache.version=$APACHE_VERSION"

networks:
  default:
    driver: bridge
EOF

# Create HTML content
mkdir -p /opt/http2-labs/html
cat > /opt/http2-labs/html/index.html << EOF
<html><body><h1>$LAB_NAME Target Server</h1><p>Apache $APACHE_VERSION - HTTP/2 Enabled</p><p>Status: Ready for attack</p></body></html>
EOF

# Create large test file
dd if=/dev/zero of=/opt/http2-labs/html/large-test.jpg bs=1M count=10 2>/dev/null

# Start lab environment
cd /opt/http2-labs
docker-compose -f current-lab.yml up -d

echo "✅ $LAB_NAME deployed successfully"
echo "🎯 Apache $APACHE_VERSION running on port 80"
echo "📊 Attack script: $ATTACK_SCRIPT"
echo "🔗 Target: http://localhost (from inside instance)"

# Auto-start attack if script is available
if [ -f "/opt/http2-labs/shared/scripts/$ATTACK_SCRIPT" ]; then
    echo "🚀 Starting attack automatically..."
    sleep 5  # Wait for Apache to be ready
    python3 "/opt/http2-labs/shared/scripts/$ATTACK_SCRIPT" localhost --port 80 --connections "$DEFAULT_CONNECTIONS" --verbose > "/opt/http2-labs/shared/logs/${LAB_NAME}-attack.log" 2>&1 &
    ATTACK_PID=$!
    echo "⚡ Attack started (PID: $ATTACK_PID)"
    echo "📊 View logs: tail -f /opt/http2-labs/shared/logs/${LAB_NAME}-attack.log"
else
    echo "⚠️  Attack script not found: $ATTACK_SCRIPT"
    echo "📝 Copy scripts to continue: scp scripts/*.py ubuntu@IP:/opt/http2-labs/shared/scripts/"
fi
DEPLOY_EOF

chmod +x /opt/http2-labs/shared/deploy-lab.sh

# Create monitoring script
cat > /opt/http2-labs/shared/monitor.sh << 'MONITOR_EOF'
#!/bin/bash
echo "=== HTTP/2 Attack Lab Live Monitoring ==="
echo "Time: $(date)"
echo ""
echo "=== Docker Containers ==="
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "=== Active Connections on Port 80 ==="
ss -tuln | grep :80 | wc -l | xargs echo "Connections:"
echo ""
echo "=== Server Response Test ==="
curl -w "Response Time: %{time_total}s\n" -s -o /dev/null http://localhost/ || echo "Server not responding"
echo ""
echo "=== System Resources ==="
free -h | grep Mem
df -h | grep -E "/$"
echo "Load: $(uptime | awk -F'load average:' '{print $2}')"
echo ""
echo "=== Recent Attack Logs ==="
ls -la /opt/http2-labs/shared/logs/*.log 2>/dev/null | tail -3 || echo "No attack logs found"
MONITOR_EOF

chmod +x /opt/http2-labs/shared/monitor.sh

# Create cleanup script
cat > /opt/http2-labs/shared/cleanup.sh << 'CLEANUP_EOF'
#!/bin/bash
echo "=== Cleaning up HTTP/2 Attack Lab ==="
docker-compose -f /opt/http2-labs/current-lab.yml down 2>/dev/null || true
docker system prune -f
pkill -f "python3.*attack" || true
rm -f /opt/http2-labs/shared/logs/*.log
echo "✅ Cleanup complete"
CLEANUP_EOF

chmod +x /opt/http2-labs/shared/cleanup.sh

# Auto-shutdown after 4 hours (cost control)
echo "sudo shutdown -h now" | at now + 4 hours

# Create welcome message
cat > /etc/motd << 'MOTD_EOF'
🎯 HTTP/2 Flow Control Attack Lab Infrastructure

Available Commands:
• /opt/http2-labs/shared/monitor.sh     - Live monitoring
• /opt/http2-labs/shared/cleanup.sh     - Clean up lab
• docker ps                              - Show containers
• tail -f /opt/http2-labs/shared/logs/*.log  - View attack logs

Web Access:
• http://EXTERNAL_IP:8080               - Web terminal
• http://EXTERNAL_IP                    - Apache target server

Current Lab Status:
• Ready for attack deployment
• Use deploy scripts from Cloud Shell or local machine

MOTD_EOF

echo "🎯 HTTP/2 Lab Infrastructure setup complete!"
echo "External IP: $(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google')"
echo "Web Terminal: http://$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip -H 'Metadata-Flavor: Google'):8080"