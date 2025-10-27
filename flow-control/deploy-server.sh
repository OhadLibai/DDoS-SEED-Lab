#!/bin/bash
# HTTP/2 Flow Control Lab - Unified Server Deployment
# Deploys containerized Apache servers for attack testingde
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load GCP configuration if available, otherwise use defaults
if [ -f "gcp.env" ]; then
    echo -e "${BLUE}[INFO]${NC} Loading GCP configuration from gcp.env"
    source gcp.env
    INFRASTRUCTURE_NAME="$GCP_VM_NAME"
    ZONE="$GCP_ZONE"
    PROJECT="$GCP_PROJECT_ID"
else
    echo -e "${BLUE}[INFO]${NC} gcp.env not found, using hardcoded defaults"
    echo -e "${BLUE}[INFO]${NC} Run './setup-gcp.sh' to create proper configuration"
    INFRASTRUCTURE_NAME="http2-lab-infrastructure"
    ZONE="us-central1-a"
    PROJECT=""
fi

show_help() {
    cat << EOF
HTTP/2 Flow Control Lab - Server Deployment

Usage: $0 [local|gcp] [attack-type] [OPTIONS]

Arguments:  
  local|gcp          Deployment target (GCP uses gcp.env config)
  attack-type        zero-window, slow-incremental, or adaptive-slow

Options:
  --stop             Stop VM instance (restartable)
  --destruct-vm   (GCP only) COMPLETELY REMOVE cloud infrastructure  
                     (requires re-running ./setup-gcp.sh)
  --logs             Show Apache container logs
  --status           Show container status, CPU/memory, active connections
  --help, -h         Show this help

Examples:
  $0 local zero-window                    # Deploy local server
  $0 gcp zero-window                      # Deploy GCP server
  $0 gcp zero-window --stop               # Stop GCP server
  $0 gcp zero-window --destruct-vm     # Destroy GCP infrastructure
  $0 local zero-window --logs             # Show server logs

Attack Types:
  zero-window        Apache 2.4.55 - Basic HTTP/2 flow control attack
  slow-incremental   Apache 2.4.62 - Sustained resource exhaustion
  adaptive-slow      Apache 2.4.62 - Advanced attack intelligence
EOF
}

validate_attack_type() {
    local attack_type="$1"
    
    if [ ! -d "attacks/$attack_type" ]; then
        echo -e "${RED}❌ Attack type not found: $attack_type${NC}"
        echo "Available attacks: zero-window, slow-incremental, adaptive-slow"
        exit 1
    fi
    
    if [ ! -f "attacks/$attack_type/docker-compose.yml" ]; then
        echo -e "${RED}❌ Docker compose file not found: attacks/$attack_type/docker-compose.yml${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Validated attack type: $attack_type${NC}"
}

check_prerequisites_local() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first.${NC}"
        exit 1
    fi
}

check_prerequisites_gcp() {
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud not found. Please install Google Cloud CLI first.${NC}"
        exit 1
    fi
    
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        echo -e "${RED}❌ Not authenticated with gcloud. Run: gcloud auth login${NC}"
        exit 1
    fi
    
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID${NC}"
        exit 1
    fi
}

deploy_local_server() {
    local attack_type="$1"
    
    # Get Apache version from docker-compose file
    local apache_version=$(grep "image: httpd:" "attacks/$attack_type/docker-compose.yml" | sed 's/.*httpd://' | sed 's/[[:space:]]*//')
    
    echo -e "${BLUE}🎯 Deploying Local Server: $attack_type${NC}"
    echo -e "${BLUE}Target: Apache $apache_version${NC}"
    echo ""
    
    # Clean start
    echo -e "${GREEN}Cleaning previous deployment...${NC}"
    docker-compose -f attacks/$attack_type/docker-compose.yml down 2>/dev/null || true
    docker system prune -f
    
    # Start environment using attack-specific docker-compose
    echo -e "${GREEN}Starting Apache server container...${NC}"
    docker-compose -f attacks/$attack_type/docker-compose.yml up -d --build
    
    # Wait for Apache to be ready
    echo -e "${GREEN}Waiting for Apache to start...${NC}"
    for i in {1..30}; do
        if curl -s http://localhost/ >/dev/null 2>&1; then
            break
        fi
        sleep 2
    done
    
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Apache server failed to start${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Local server deployed successfully!${NC}"
    echo -e "${BLUE}Apache server: http://localhost${NC}"
    echo -e "${BLUE}Attack with: ./deploy-attack.sh $attack_type local --connections 512${NC}"
}

deploy_gcp_server() {
    local attack_type="$1"
    
    # Get Apache version from docker-compose file
    local apache_version=$(grep "image: httpd:" "attacks/$attack_type/docker-compose.yml" | sed 's/.*httpd://' | sed 's/[[:space:]]*//')
    
    echo -e "${BLUE}🎯 Deploying GCP Server: $attack_type${NC}"
    echo -e "${BLUE}Target: Apache $apache_version on f1-micro (FREE TIER)${NC}"
    echo ""
    
    # Check if infrastructure exists
    if ! gcloud compute instances list --filter="name=$INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$INFRASTRUCTURE_NAME"; then
        echo -e "${RED}❌ Infrastructure not found!${NC}"
        echo "First run: ./setup-gcp.sh"
        exit 1
    fi
    
    INSTANCE_IP=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
    INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)
    
    echo -e "${GREEN}✅ Found infrastructure: $INFRASTRUCTURE_NAME${NC}"
    echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
    echo -e "${BLUE}Zone: $INSTANCE_ZONE${NC}"
    echo ""
    
    # Start instance if stopped
    INSTANCE_STATUS=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(STATUS)")
    if [ "$INSTANCE_STATUS" = "TERMINATED" ]; then
        echo -e "${GREEN}Starting stopped instance...${NC}"
        gcloud compute instances start $INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet
        sleep 30  # Wait for startup
    fi
    
    # Copy docker-compose file to instance and deploy
    echo -e "${GREEN}Deploying $attack_type server on GCP...${NC}"
    
    # Copy attack-specific docker-compose file to GCP instance
    # Create directory and set permissions on GCP VM
    gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet --command="
        sudo mkdir -p /opt/http2-labs
        sudo chown ubuntu:ubuntu /opt/http2-labs
        sudo chmod 755 /opt/http2-labs
    "

    # Now copy the file
    gcloud compute scp attacks/$attack_type/docker-compose.yml ubuntu@$INFRASTRUCTURE_NAME:/opt/http2-labs/docker-compose-$attack_type.yml --zone=$INSTANCE_ZONE --quiet

    # Run commands in the directory
    gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet --command="
        cd /opt/http2-labs
    "
        
        # Stop any existing containers
        docker-compose down 2>/dev/null || true
        docker system prune -f
        
        # Start the server using copied docker-compose file
        docker-compose -f $attack_type/docker-compose.yml up -d --build
        
        # Wait for Apache to be ready
        echo 'Waiting for Apache to start...'
        for i in {1..30}; do
            if curl -s http://localhost/ >/dev/null 2>&1; then
                echo 'Apache ready!'
                break
            fi
            sleep 2
        done
    
    echo ""
    echo -e "${GREEN}🎉 GCP server deployed successfully!${NC}"
    echo -e "${BLUE}Apache server: http://$INSTANCE_IP${NC}"
    echo -e "${BLUE}Attack with: ./deploy-attack.sh $attack_type $INSTANCE_IP --connections 512${NC}"
}

stop_gcp_server() {
    echo -e "${YELLOW}Stopping GCP instance...${NC}"
    
    if ! gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$INFRASTRUCTURE_NAME"; then
        echo -e "${RED}❌ Infrastructure not found!${NC}"
        exit 1
    fi
    
    INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)
    
    gcloud compute instances stop "$INFRASTRUCTURE_NAME" --zone="$INSTANCE_ZONE" --quiet
    echo -e "${GREEN}✅ Instance stopped (disk persists, can restart)${NC}"
    echo "Restart with: $0 gcp [attack-type]"
}


destruct_gcp_infrastructure() {
    echo -e "${RED}⚠️  COMPLETELY REMOVING GCP INFRASTRUCTURE${NC}"
    echo -e "${YELLOW}This will destroy everything and require re-running ./setup-gcp.sh${NC}"
    echo ""
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Cancelled."
        exit 0
    fi
    
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
    
    # Stop and delete instance
    if gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$INFRASTRUCTURE_NAME"; then
        INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)
        
        echo -e "${YELLOW}Deleting instance...${NC}"
        gcloud compute instances delete $INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet
    fi
    
    # Delete firewall rules
    echo -e "${YELLOW}Deleting firewall rules...${NC}"
    gcloud compute firewall-rules delete http2-lab-allow-http --quiet 2>/dev/null || true
    gcloud compute firewall-rules delete http2-lab-allow-ssh --quiet 2>/dev/null || true
    
    echo ""
    echo -e "${GREEN}🎉 Infrastructure completely removed!${NC}"
    echo "To restart: ./setup-gcp.sh"
}

show_logs() {
    local deployment="$1"
    local attack_type="$2"
    
    if [ "$deployment" = "local" ]; then
        docker-compose -f attacks/$attack_type/docker-compose.yml logs --tail=50 apache-victim
    else
        INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)
        gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet --command="
            docker logs http2-apache-$attack_type --tail=50
        "
    fi
}

show_status() {
    local deployment="$1"
    local attack_type="$2"
    
    if [ "$deployment" = "local" ]; then
        echo -e "${BLUE}Local Docker Status:${NC}"
        docker ps --filter "label=lab.attack=$attack_type" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
        echo ""
        echo -e "${BLUE}Resource Usage:${NC}"
        docker stats --no-stream --filter "label=lab.attack=$attack_type"
        echo ""
        echo -e "${BLUE}Active Connections:${NC}"
        ss -tuln | grep :80 | wc -l
    else
        INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)
        INSTANCE_IP=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
        
        echo -e "${BLUE}GCP Instance Status:${NC}"
        gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME"
        echo ""
        
        gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet --command="
            echo 'Container Status:'
            docker ps --filter 'name=http2-apache-$attack_type'
            echo ''
            echo 'Resource Usage:'
            docker stats --no-stream --filter 'name=http2-apache-$attack_type'
            echo ''
            echo 'Active Connections:'
            ss -tuln | grep :80 | wc -l
        "
    fi
}


# Main execution
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

DEPLOYMENT="$1"
ATTACK_TYPE="$2"
shift 2

# Validate deployment target
if [ "$DEPLOYMENT" != "local" ] && [ "$DEPLOYMENT" != "gcp" ]; then
    echo -e "${RED}❌ Invalid deployment target: $DEPLOYMENT${NC}"
    echo "Must be 'local' or 'gcp'"
    show_help
    exit 1
fi

# Parse flags first
STOP=false
DESTRUCT=false
SHOW_LOGS=false
SHOW_STATUS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --stop)
            STOP=true
            shift
            ;;
        --destruct-vm)
            DESTRUCT=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        --status)
            SHOW_STATUS=true
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Handle stop/destruct actions first
if [ "$STOP" = true ] && [ "$DEPLOYMENT" = "gcp" ]; then
    check_prerequisites_gcp
    stop_gcp_server
    exit 0
elif [ "$DESTRUCT" = true ] && [ "$DEPLOYMENT" = "gcp" ]; then
    check_prerequisites_gcp
    destruct_gcp_infrastructure
    exit 0
elif [ "$STOP" = true ] && [ "$DEPLOYMENT" = "local" ]; then
    echo -e "${GREEN}Stopping local containers...${NC}"
    for attack in attacks/*/docker-compose.yml; do
        [ -f "$attack" ] && docker-compose -f "$attack" down 2>/dev/null || true
    done
    echo -e "${GREEN}✅ Local containers stopped${NC}"
    exit 0
fi

# Validate attack type for deployment actions
if [ -z "$ATTACK_TYPE" ]; then
    echo -e "${RED}❌ Attack type required${NC}"
    show_help
    exit 1
fi

if [ "$ATTACK_TYPE" != "zero-window" ] && [ "$ATTACK_TYPE" != "slow-incremental" ] && [ "$ATTACK_TYPE" != "adaptive-slow" ]; then
    echo -e "${RED}❌ Invalid attack type: $ATTACK_TYPE${NC}"
    echo "Must be: zero-window, slow-incremental, or adaptive-slow"
    exit 1
fi

# Handle logs/status actions
if [ "$SHOW_LOGS" = true ]; then
    show_logs "$DEPLOYMENT" "$ATTACK_TYPE"
    exit 0
fi

if [ "$SHOW_STATUS" = true ]; then
    show_status "$DEPLOYMENT" "$ATTACK_TYPE"
    exit 0
fi

# Validate attack type and structure
validate_attack_type "$ATTACK_TYPE"

# Deploy server
if [ "$DEPLOYMENT" = "local" ]; then
    check_prerequisites_local
    deploy_local_server "$ATTACK_TYPE"
else
    check_prerequisites_gcp
    deploy_gcp_server "$ATTACK_TYPE"
fi
