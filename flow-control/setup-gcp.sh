#!/bin/bash

# 🚀 HTTP/2 Flow Control Attack Lab - One-Click GCP Setup
# Creates a complete free-tier GCP environment for all HTTP/2 attack labs
# 
# This script creates:
# - f1-micro VM instance (free tier eligible)
# - Firewall rules for HTTP/HTTPS and SSH
# - Docker + Docker Compose installation
# - Auto-shutdown after 4 hours (cost protection)
# - Ready-to-use HTTP/2 attack environment

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

LAB_INFRASTRUCTURE_NAME="http2-lab-infrastructure"
REGION="us-central1"
ZONE="us-central1-a"
MACHINE_TYPE="f1-micro"

show_banner() {
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${PURPLE}🚀 HTTP/2 Flow Control Attack Lab - GCP Setup${NC}            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}Creates a complete free-tier GCP environment for:${NC}           ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} • Zero-Window HTTP/2 attacks                                ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} • Slow-Incremental resource exhaustion                     ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} • Adaptive-Slow intelligent attacks                        ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}✓ Free tier compatible (f1-micro instance)${NC}                 ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}✓ Auto-shutdown after 4 hours (cost protection)${NC}            ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}✓ Real internet testing capabilities${NC}                       ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_help() {
    cat << EOF
HTTP/2 Flow Control Attack Lab - GCP Setup

Usage: $0 [OPTIONS]

Options:
  --project-id PROJECT_ID    Specify GCP project ID (optional)
  --help, -h                Show this help message

Examples:
  $0                                    # Interactive setup
  $0 --project-id my-http2-lab         # Setup with specific project

Prerequisites:
  • Google Cloud CLI (gcloud) installed and authenticated
  • GCP project created via Google Cloud Console
  • Billing enabled (free tier only, no charges expected)

What this script creates:
  • f1-micro VM instance (always free eligible)
  • HTTP/HTTPS and SSH firewall rules
  • Docker and Docker Compose installation
  • Complete HTTP/2 attack lab environment

After setup, you can immediately start attacking:
  ./deploy-server.sh gcp zero-window
  ./deploy-attack.sh zero-window YOUR_INSTANCE_IP --connections 512

Configuration:
  Creates gcp.env file for persistent settings across deployments
EOF
}

check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check gcloud
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ Google Cloud CLI not found${NC}"
        echo ""
        echo -e "${YELLOW}Please install gcloud CLI:${NC}"
        echo "• Visit: https://cloud.google.com/sdk/docs/install"
        echo "• Or run in Google Cloud Shell (recommended)"
        exit 1
    fi
    echo -e "${GREEN}  ✓ Google Cloud CLI found${NC}"
    
    # Check authentication
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ Not authenticated with Google Cloud${NC}"
        echo ""
        echo -e "${YELLOW}Please authenticate first:${NC}"
        echo "  gcloud auth login"
        exit 1
    fi
    echo -e "${GREEN}  ✓ Google Cloud authentication active${NC}"
    
    echo ""
}

detect_or_set_project() {
    local provided_project_id="$1"
    
    if [ -n "$provided_project_id" ]; then
        PROJECT_ID="$provided_project_id"
        echo -e "${BLUE}🎯 Using provided project ID: ${GREEN}$PROJECT_ID${NC}"
    else
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [ -z "$PROJECT_ID" ]; then
            echo -e "${YELLOW}⚠️  No GCP project configured${NC}"
            echo ""
            echo -e "${CYAN}Available projects:${NC}"
            gcloud projects list --format="table(projectId,name,projectNumber)" | head -10
            echo ""
            read -p "Enter your GCP project ID: " PROJECT_ID
            
            if [ -z "$PROJECT_ID" ]; then
                echo -e "${RED}❌ Project ID required${NC}"
                exit 1
            fi
        else
            echo -e "${BLUE}🎯 Using configured project: ${GREEN}$PROJECT_ID${NC}"
        fi
    fi
    
    # Set the project
    gcloud config set project "$PROJECT_ID" --quiet
    echo -e "${GREEN}  ✓ Project set successfully${NC}"
    echo ""
}

check_existing_infrastructure() {
    echo -e "${BLUE}🔍 Checking for existing infrastructure...${NC}"
    
    if gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$LAB_INFRASTRUCTURE_NAME"; then
        INSTANCE_IP=$(gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
        INSTANCE_STATUS=$(gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(STATUS)")
        
        echo -e "${YELLOW}⚠️  Infrastructure already exists!${NC}"
        echo -e "${BLUE}Instance Name: $LAB_INFRASTRUCTURE_NAME${NC}"
        echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
        echo -e "${BLUE}Status: $INSTANCE_STATUS${NC}"
        echo ""
        
        if [ "$INSTANCE_STATUS" = "TERMINATED" ]; then
            echo -e "${YELLOW}Instance is stopped. You can restart it with:${NC}"
            echo "  gcloud compute instances start $LAB_INFRASTRUCTURE_NAME --zone=$ZONE"
            echo ""
        fi
        
        echo -e "${GREEN}✅ Your lab environment is ready!${NC}"
        echo ""
        echo -e "${CYAN}🚀 Start attacking immediately:${NC}"
        echo "  ./deploy-server.sh gcp zero-window"
        echo "  ./deploy-attack.sh zero-window $INSTANCE_IP --connections 512"
        echo ""
        echo -e "${CYAN}📖 Or try other attacks:${NC}"
        echo "  ./deploy-server.sh gcp slow-incremental"
        echo "  ./deploy-server.sh gcp adaptive-slow"
        exit 0
    fi
    
    echo -e "${GREEN}  ✓ No existing infrastructure found, proceeding with setup${NC}"
    echo ""
}

create_infrastructure() {
    echo -e "${BLUE}🏗️  Creating GCP infrastructure...${NC}"
    echo -e "${BLUE}Instance Type: $MACHINE_TYPE (Free Tier)${NC}"
    echo -e "${BLUE}Region: $REGION${NC}"
    echo -e "${BLUE}Zone: $ZONE${NC}"
    echo ""
    
    # Enable required APIs
    echo -e "${CYAN}⚙️  Enabling required Google Cloud APIs...${NC}"
    gcloud services enable compute.googleapis.com --quiet
    echo -e "${GREEN}  ✓ Compute Engine API enabled${NC}"
    
    # Create firewall rules
    echo -e "${CYAN}🔥 Creating firewall rules...${NC}"
    
    if ! gcloud compute firewall-rules describe http2-lab-allow-http &>/dev/null; then
        gcloud compute firewall-rules create http2-lab-allow-http \
            --allow tcp:80,tcp:443 \
            --source-ranges 0.0.0.0/0 \
            --description "Allow HTTP/HTTPS for HTTP/2 lab" \
            --quiet
        echo -e "${GREEN}  ✓ HTTP/HTTPS firewall rule created${NC}"
    else
        echo -e "${GREEN}  ✓ HTTP/HTTPS firewall rule already exists${NC}"
    fi
    
    if ! gcloud compute firewall-rules describe http2-lab-allow-ssh &>/dev/null; then
        gcloud compute firewall-rules create http2-lab-allow-ssh \
            --allow tcp:22 \
            --source-ranges 0.0.0.0/0 \
            --description "Allow SSH for HTTP/2 lab management" \
            --quiet
        echo -e "${GREEN}  ✓ SSH firewall rule created${NC}"
    else
        echo -e "${GREEN}  ✓ SSH firewall rule already exists${NC}"
    fi
    
    # Create startup script
    echo -e "${CYAN}📝 Preparing instance startup script...${NC}"
    cat > /tmp/http2-lab-startup.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu
rm get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create lab directory structure
mkdir -p /opt/http2-labs/shared/docker/apache-html/html
mkdir -p /opt/http2-labs/logs

# Create HTTP/2 test page
cat > /opt/http2-labs/shared/docker/apache-html/html/index.html << 'HTML_EOF'
<!DOCTYPE html>
<html>
<head>
    <title>HTTP/2 Flow Control Attack Lab</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 40px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            padding: 40px; 
            border-radius: 8px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        .header { color: #4285f4; margin-bottom: 20px; }
        .warning { 
            color: #ea4335; 
            background: #fce8e6; 
            padding: 15px; 
            border-radius: 4px; 
            border-left: 4px solid #ea4335; 
            margin: 20px 0; 
        }
        .status { 
            background: #e8f5e8; 
            padding: 15px; 
            border-radius: 4px; 
            border-left: 4px solid #34a853; 
        }
        .code { 
            background: #f8f9fa; 
            padding: 10px; 
            border-radius: 4px; 
            font-family: monospace; 
            margin: 10px 0; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="header">🚀 HTTP/2 Flow Control Attack Lab</h1>
        <p>This is a security research environment for studying HTTP/2 protocol vulnerabilities.</p>
        
        <div class="warning">
            <strong>⚠️ Educational Use Only:</strong> This server is configured for security research and educational purposes. Use responsibly and only attack servers you own or have explicit permission to test.
        </div>
        
        <div class="status">
            <strong>✅ Server Status:</strong> Ready for HTTP/2 attacks<br>
            <strong>🔧 Protocol Support:</strong> HTTP/1.1, HTTP/2<br>
            <strong>🎯 Available Attacks:</strong> Zero-Window, Slow-Incremental, Adaptive-Slow
        </div>
        
        <h3>Attack Commands:</h3>
        <div class="code">
            ./deploy-attack.sh zero-window YOUR_IP --connections 512<br>
            ./deploy-attack.sh slow-incremental YOUR_IP --connections 256<br>
            ./deploy-attack.sh adaptive-slow YOUR_IP --connections 128
        </div>
        
        <p><strong>Instance ID:</strong> <span id="instanceId">Loading...</span></p>
        <p><strong>Timestamp:</strong> <span id="timestamp"></span></p>
    </div>
    
    <script>
        // Add some dynamic content
        document.getElementById('timestamp').textContent = new Date().toLocaleString();
        
        // Try to get instance metadata (will fail from external requests, but works from instance)
        fetch('http://metadata.google.internal/computeMetadata/v1/instance/id', {
            headers: {'Metadata-Flavor': 'Google'}
        }).then(r => r.text()).then(id => {
            document.getElementById('instanceId').textContent = id;
        }).catch(() => {
            document.getElementById('instanceId').textContent = 'External Request';
        });
    </script>
</body>
</html>
HTML_EOF

# Set proper ownership
chown -R ubuntu:ubuntu /opt/http2-labs

# Auto-shutdown after 4 hours for cost control
shutdown -h +240

# Mark startup complete
touch /tmp/startup-complete
echo "HTTP/2 Lab startup completed at $(date)" >> /var/log/startup.log
EOF
    
    echo -e "${GREEN}  ✓ Startup script prepared${NC}"
    
    # Create the VM instance
    echo -e "${CYAN}🖥️  Creating VM instance ($MACHINE_TYPE)...${NC}"
    echo -e "${YELLOW}This may take 2-3 minutes...${NC}"
    
    gcloud compute instances create $LAB_INFRASTRUCTURE_NAME \
        --zone=$ZONE \
        --machine-type=$MACHINE_TYPE \
        --network-interface=network-tier=PREMIUM,subnet=default \
        --metadata-from-file startup-script=/tmp/http2-lab-startup.sh \
        --maintenance-policy=MIGRATE \
        --provisioning-model=STANDARD \
        --image-family=ubuntu-2004-lts \
        --image-project=ubuntu-os-cloud \
        --boot-disk-size=20GB \
        --boot-disk-type=pd-standard \
        --boot-disk-device-name=$LAB_INFRASTRUCTURE_NAME \
        --no-shielded-secure-boot \
        --shielded-vtpm \
        --shielded-integrity-monitoring \
        --reservation-affinity=any \
        --quiet
    
    # Clean up temporary files
    rm -f /tmp/http2-lab-startup.sh
    
    echo -e "${GREEN}  ✓ VM instance created successfully${NC}"
    
    # Generate configuration file
    echo -e "${CYAN}📋 Creating configuration file...${NC}"
    create_gcp_config
}

# Function to create/update gcp.env configuration file
create_gcp_config() {
    local config_file="gcp.env"
    local external_ip=$(gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
    
    echo -e "${BLUE}Creating GCP configuration file: $config_file${NC}"
    cat > "$config_file" << EOF
# Flow Control Lab - GCP Configuration
# Auto-generated by setup-gcp.sh on $(date)
# Single source of truth for all GCP deployment scripts

# GCP Project Configuration
GCP_PROJECT_ID=$PROJECT_ID
GCP_ZONE=$ZONE
GCP_REGION=$REGION

# VM Configuration
GCP_VM_NAME=$LAB_INFRASTRUCTURE_NAME
GCP_MACHINE_TYPE=$MACHINE_TYPE

# Network Configuration (auto-populated)
TARGET_IP=$external_ip

# Firewall Configuration
FIREWALL_RULE_NAME=allow-http2-flow-control

# Flow Control Lab Specific Configuration
ATTACK_TYPES=zero-window,slow-incremental,adaptive-slow
DEFAULT_ATTACK_TYPE=zero-window
DEFAULT_CONNECTIONS=512

# Apache Server Configuration
APACHE_HTTP_PORT=80
APACHE_HTTPS_PORT=443

# Auto-shutdown Configuration (cost protection)
AUTO_SHUTDOWN_HOURS=4

# Metadata
CREATED_DATE=$(date -Iseconds)
LAST_UPDATED=$(date -Iseconds)
EOF
    
    echo -e "${GREEN}  ✓ GCP configuration saved to $config_file${NC}"
}

show_completion() {
    # Get instance details
    INSTANCE_IP=$(gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
    
    echo ""
    echo -e "${GREEN}🎉 Infrastructure setup complete!${NC}"
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║${NC} ${GREEN}✅ Your HTTP/2 Attack Lab is Ready!${NC}                         ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC}                                                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}Instance IP:${NC} ${YELLOW}$INSTANCE_IP${NC}                                  ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}Instance Name:${NC} $LAB_INFRASTRUCTURE_NAME                     ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}Region:${NC} $REGION (Free Tier)                              ${CYAN}║${NC}"
    echo -e "${CYAN}║${NC} ${BLUE}Config File:${NC} gcp.env (persistent settings)                ${CYAN}║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}⏰ Please wait 2-3 minutes for the instance to complete startup...${NC}"
    echo ""
    echo -e "${CYAN}🚀 Quick Start Commands:${NC}"
    echo ""
    echo -e "${GREEN}1. Deploy a server:${NC}"
    echo "   ./deploy-server.sh gcp zero-window"
    echo "   ./deploy-server.sh gcp slow-incremental"
    echo "   ./deploy-server.sh gcp adaptive-slow"
    echo ""
    echo -e "${GREEN}2. Launch attacks from your local machine:${NC}"
    echo "   ./deploy-attack.sh zero-window $INSTANCE_IP --connections 512"
    echo "   ./deploy-attack.sh slow-incremental $INSTANCE_IP --connections 256"
    echo "   ./deploy-attack.sh adaptive-slow $INSTANCE_IP --connections 128"
    echo ""
    echo -e "${GREEN}3. Monitor your attacks:${NC}"
    echo "   ./deploy-attack.sh zero-window $INSTANCE_IP --logs"
    echo "   ./deploy-server.sh gcp zero-window --status"
    echo ""
    echo -e "${CYAN}🌐 Access Methods:${NC}"
    echo "• Test server: http://$INSTANCE_IP"
    echo "• SSH access: gcloud compute ssh $LAB_INFRASTRUCTURE_NAME --zone=$ZONE"
    echo "• GCP Console: https://console.cloud.google.com/compute/instances"
    echo ""
    echo -e "${CYAN}💰 Cost Control:${NC}"
    echo "• ${GREEN}Free tier eligible${NC} (f1-micro instance)"
    echo "• ${GREEN}Auto-shutdown${NC} after 4 hours"
    echo "• ${YELLOW}Stop instance:${NC} ./deploy-server.sh gcp zero-window --stop"
    echo "• ${RED}Destroy everything:${NC} ./deploy-server.sh gcp zero-window --destruct-vm"
    echo ""
    echo -e "${PURPLE}🎯 Happy attacking! Study HTTP/2 protocol vulnerabilities responsibly.${NC}"
}

# Main execution
main() {
    # Parse command line arguments
    PROVIDED_PROJECT_ID=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --project-id)
                PROVIDED_PROJECT_ID="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Unknown option: $1${NC}"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Execute setup steps
    show_banner
    check_prerequisites
    detect_or_set_project "$PROVIDED_PROJECT_ID"
    check_existing_infrastructure
    create_infrastructure
    show_completion
}

# Run main function
main "$@"