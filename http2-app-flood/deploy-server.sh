#!/bin/bash
# HTTP/2 Flood Lab - Server-Only Deployment Script
# Deploy victim servers locally or on GCP without attacks

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Load GCP configuration if available, otherwise use defaults
if [ -f "gcp.env" ]; then
    print_info "Loading GCP configuration from gcp.env"
    source gcp.env
    VM_NAME="$GCP_VM_NAME"
    ZONE="$GCP_ZONE"
else
    print_info "gcp.env not found, using hardcoded defaults"
    print_info "Run './gcp-setup-infrastructure.sh' to create proper configuration"
    VM_NAME="http2-flood-lab"
    ZONE="us-central1-a"
fi

usage() {
    echo "HTTP/2 Flood Lab - Server-Only Deployment"
    echo ""
    echo "Usage: $0 --local|--gcp <part-A|part-B|--stop> [options]"
    echo ""
    echo "Targets:"
    echo "  --local             Deploy server on local Docker"
    echo "  --gcp               Deploy server on GCP VM"
    echo ""
    echo "Commands:"
    echo "  part-A              Deploy single-worker victim server"
    echo "  part-B              Deploy multi-worker victim server"
    echo "  --stop              Stop containers + shutdown VM instance (VM still exists but powered off)"
    echo "  --destruct-vm   (GCP only) COMPLETELY REMOVE cloud infrastructure - requires re-running gcp-setup-infrastructure.sh"
    echo ""
    echo "Environment Variables (options):"
    echo "  SCENARIO=<name>     CPU scenario: default_scenario, captcha, crypto, gaming, antibot, webservice, content"
    echo "  WORKLOAD=<1-5>      CPU workload intensity (default: 5)"
    echo ""
    echo "Examples:"
    echo "  $0 --local part-A          # Deploy local single-worker server"
    echo "  $0 --gcp part-B            # Deploy GCP multi-worker server"
    echo "  SCENARIO=captcha $0 --local part-A   # Local server with CAPTCHA scenario"
    echo "  $0 --local --stop          # Stop local servers"
    echo "  $0 --gcp --stop            # Stop containers + shutdown VM"
    echo "  $0 --gcp --destruct-vm    # Remove entire cloud infrastructure"
    echo ""
    exit 1
}

# HTTP/2 health check function
check_http2_server() {
    local target_url=$1
    local max_attempts=10
    local attempt=1
    
    print_info "Checking HTTP/2 server health at $target_url"
    
    while [ $attempt -le $max_attempts ]; do
        if curl --http2-prior-knowledge \
                --connect-timeout 5 \
                --max-time 10 \
                --fail \
                --silent \
                "${target_url}/health" > /dev/null 2>&1; then
            print_success "HTTP/2 server is healthy and ready"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts failed, retrying in 3 seconds..."
        sleep 3
        ((attempt++))
    done
    
    print_error "HTTP/2 server health check failed after $max_attempts attempts"
    return 1
}

# Parse command-line arguments
POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        *=*)
            export "$1"
            shift
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

# Restore positional arguments
set -- "${POSITIONAL_ARGS[@]}"

# Check arguments
if [ $# -lt 2 ]; then
    usage
fi

TARGET=$1
COMMAND=$2
SCENARIO=${SCENARIO:-default_scenario}
WORKLOAD=${WORKLOAD:-5}

# Validate target
if [[ "$TARGET" != "--local" && "$TARGET" != "--gcp" ]]; then
    print_error "Invalid target: $TARGET"
    usage
fi

#
# LOCAL DEPLOYMENT
#
if [ "$TARGET" = "--local" ]; then
    # Handle --stop command for local deployment
    if [ "$COMMAND" = "--stop" ]; then
        print_info "Stopping local victim servers..."
        
        # Detect which servers are currently running
        ACTIVE_SERVERS=""
        if docker ps --format "{{.Names}}" | grep -q "dev-victim-server"; then
            ACTIVE_SERVERS="$ACTIVE_SERVERS part-A"
        fi
        if docker ps --format "{{.Names}}" | grep -q "prod-victim-server"; then
            ACTIVE_SERVERS="$ACTIVE_SERVERS part-B"
        fi
        
        if [ -n "$ACTIVE_SERVERS" ]; then
            for server in $ACTIVE_SERVERS; do
                print_info "Stopping $server victim server..."
                cd "$server"
                docker-compose stop 2>/dev/null || true
                cd ..
            done
            print_success "Local victim servers stopped successfully!"
        else
            print_info "No active victim servers found."
        fi
        
        exit 0
    fi
    
    # Validate local command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid local command: $COMMAND"
        print_error "Local deployment supports part-A, part-B, and --stop"
        usage
    fi
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if port 8080 is available
    if lsof -Pi :8080 -sTCP:LISTEN -t > /dev/null 2>&1; then
        print_warning "Port 8080 is already in use. Stopping existing containers..."
        # Stop any existing victim servers
        for part in part-A part-B; do
            if [ -d "$part" ]; then
                cd "$part"
                docker-compose down --remove-orphans 2>/dev/null || true
                cd ..
            fi
        done
    fi
    
    print_info "Deploying HTTP/2 Victim Server - $COMMAND (LOCAL)"
    print_info "Configuration: Scenario=$SCENARIO, Server Workload=$WORKLOAD"
    
    # Set environment variables for docker-compose
    export SCENARIO
    export WORKLOAD
    
    # Deploy the specified server
    print_info "Building and starting victim server..."
    cd "$COMMAND"
    
    if docker-compose up -d --build; then
        # Health check
        if check_http2_server "http://localhost:8080"; then
            print_success "Local victim server deployment completed successfully!"
            print_success "Server is running at: http://localhost:8080"
            echo
            echo "=================================================="
            print_info "Server Monitoring Commands:"
            if [ "$COMMAND" = "part-A" ]; then
                echo "  docker exec dev-victim-server sh -c \"awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp\""
            else
                echo "  docker exec prod-victim-server sh -c \"awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp\""
            fi
            echo "  docker stats --no-stream"
            echo "  curl --http2-prior-knowledge --no-progress-meter -o /dev/null -w \"Time: %{time_total}s\n\" http://localhost:8080"
            echo "  curl --http2-prior-knowledge http://localhost:8080/health"
            echo "=================================================="
            echo
            print_info "To stop the server: bash deploy-server.sh --local --stop"
            print_info "To attack this server: bash deploy-attack.sh --local $COMMAND"
            echo
        else
            print_error "Server deployment failed health check!"
            exit 1
        fi
    else
        print_error "Local server deployment failed!"
        exit 1
    fi

#
# GCP DEPLOYMENT
#
elif [ "$TARGET" = "--gcp" ]; then
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi

    # --- IAP Tunneling Logic ---
    # Check gcp.env for DEPLOYMENT_MODE. Default to empty if not set.
    DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-} 
    GCLOUD_SSH_FLAGS=""
    if [[ "$DEPLOYMENT_MODE" == *"Protected"* ]]; then
        print_info "Protected mode detected. Using IAP for SSH/SCP."
        GCLOUD_SSH_FLAGS="--tunnel-through-iap"
    fi
    # ---
    
    # Handle --stop and --destruct-vm commands
    if [ "$COMMAND" = "--stop" ]; then
        DESTRUCT_VM=false
    elif [ "$COMMAND" = "--destruct-vm" ]; then
        DESTRUCT_VM=true
    fi
    
    if [ "$COMMAND" = "--stop" ] || [ "$COMMAND" = "--destruct-vm" ]; then
        
        # Check if VM exists
        if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
            print_error "VM '$VM_NAME' not found!"
            print_info "Nothing to stop."
            exit 0
        fi
        
        VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(status)')
        if [ "$VM_STATUS" != "RUNNING" ] && [ "$DESTRUCT_VM" = false ]; then
            print_info "VM is already stopped."
            exit 0
        fi
        
        print_info "Stopping GCP victim servers..."
        # Only try to stop containers if VM is RUNNING
        if [ "$VM_STATUS" = "RUNNING" ]; then
            gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS --command="
                cd "$HOME"http2-flood-lab 2>/dev/null || { echo 'No servers deployed'; exit 0; }
                for part in part-A part-B; do
                    if [ -d \$part ]; then
                        echo \"Stopping \$part victim server...\"
                        cd \$part
                        docker-compose -f docker-compose.server.yml stop || true
                        cd ..
                    fi
                done
                echo 'Victim servers stopped'
            " 2>/dev/null || print_warning "Could not connect to VM (may be stopped). Proceeding with cleanup."
        fi
        
        if [ "$DESTRUCT_VM" = true ]; then
            print_warning "EXTERMINATING complete cloud infrastructure for this lab..."
            print_info "Deleting VM instance..."
            gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet

            # Check if we were in protected mode
            if [[ "$DEPLOYMENT_MODE" == *"Protected"* ]]; then
                print_info "Protected mode detected. Deleting LB, NAT, and related resources..."
                
                # --- Must re-define resource names from setup script ---
                IG_NAME="${VM_NAME}-ig"
                HC_NAME="${VM_NAME}-hc"
                BES_NAME="${VM_NAME}-bes"
                UM_NAME="${VM_NAME}-url-map"
                TP_NAME="${VM_NAME}-target-proxy"
                LB_IP_NAME="${VM_NAME}-lb-ip"
                FW_RULE_NAME="${VM_NAME}-fw-rule"
                ROUTER_NAME="${VM_NAME}-router"
                NAT_NAME="${VM_NAME}-nat-gateway"
                FIREWALL_RULE_LB="allow-lb-to-vm"
                FIREWALL_RULE_SSH_IAP="allow-ssh-via-iap"
                # ---

                # Delete LB (must be in this order)
                print_info "Deleting Load Balancer (Forwarding Rule)..."
                gcloud compute forwarding-rules delete $FW_RULE_NAME --global --quiet 2>/dev/null || true
                print_info "Deleting Target Proxy..."
                gcloud compute target-http-proxies delete $TP_NAME --quiet 2>/dev/null || true
                print_info "Deleting URL Map..."
                gcloud compute url-maps delete $UM_NAME --quiet 2>/dev/null || true
                print_info "Deleting Backend Service..."
                gcloud compute backend-services delete $BES_NAME --global --quiet 2>/dev/null || true
                print_info "Deleting Health Check..."
                gcloud compute health-checks delete $HC_NAME --quiet 2>/dev/null || true
                print_info "Deleting Instance Group..."
                gcloud compute instance-groups unmanaged delete $IG_NAME --zone=$ZONE --quiet 2>/dev/null || true
                print_info "Deleting Global Static IP..."
                gcloud compute addresses delete $LB_IP_NAME --global --quiet 2>/dev/null || true
                
                # Delete NAT (must be in this order)
                print_info "Deleting Cloud NAT..."
                gcloud compute routers nats delete $NAT_NAME --router=$ROUTER_NAME --region=$REGION --quiet 2>/dev/null || true
                print_info "Deleting Cloud Router..."
                gcloud compute routers delete $ROUTER_NAME --region=$REGION --quiet 2>/dev/null || true

                # Delete Firewall Rules
                print_info "Deleting firewall rules..."
                gcloud compute firewall-rules delete $FIREWALL_RULE_LB --quiet 2>/dev/null || true
                gcloud compute firewall-rules delete $FIREWALL_RULE_SSH_IAP --quiet 2>/dev/null || true
            else
                print_info "Direct mode detected. Deleting firewall rule..."
                # Note: FIREWALL_RULE_NAME is from gcp.env
                FIREWALL_RULE="${FIREWALL_RULE_NAME:-allow-http2-lab-direct}"
                gcloud compute firewall-rules delete "$FIREWALL_RULE" --quiet 2>/dev/null || true
            fi
            
            print_success "Cloud infrastructure completely removed!"
            print_info "To recreate: ./gcp-setup-infrastructure.sh [PROJECT_ID]"
        else
            print_info "Shutting down VM instance (VM still exists but powered off)..."
            gcloud compute instances stop $VM_NAME --zone=$ZONE
            print_success "VM shutdown complete. Use 'gcloud compute instances start $VM_NAME --zone=$ZONE' to restart."
        fi
        exit 0
    fi
    
    # Validate GCP deployment command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid GCP command: $COMMAND"
        usage
    fi
    
    # Check if VM exists and is accessible
    if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
        print_error "VM '$VM_NAME' not found in zone '$ZONE'!"
        if [ -f "gcp.env" ]; then
            print_error "Configuration loaded from gcp.env may be outdated."
            print_info "Try regenerating: ./gcp-setup-infrastructure.sh"
        else
            print_info "Run './gcp-setup-infrastructure.sh' first to create the infrastructure."
        fi
        exit 1
    fi
    
    # Check if VM is running
    VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(status)')
    if [ "$VM_STATUS" != "RUNNING" ]; then
        print_info "Starting VM..."
        gcloud compute instances start $VM_NAME --zone=$ZONE
        print_info "Waiting for VM to be ready..."
        sleep 30
    fi
    
    print_info "Deploying HTTP/2 Victim Server - $COMMAND (GCP)"
    print_info "Configuration: Scenario=$SCENARIO, Server Workload=$WORKLOAD"
    
    # Get VM external IP (prioritize gcp.env, fallback to gcloud query)
    if [ -n "$TARGET_IP" ] && [ "$TARGET_IP" != "" ]; then
        EXTERNAL_IP="$TARGET_IP"
        TARGET_PORT=${TARGET_PORT:-8080} # Default to 8080 if not in gcp.env
        print_info "Using Target from gcp.env: http://$EXTERNAL_IP:$TARGET_PORT"
    else
        print_info "TARGET_IP not set in gcp.env, querying VM directly..."
        EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
        TARGET_PORT="8080" # Set port for direct mode
    fi
    
    # Create deployment archive (server files only)
    print_info "Preparing server files for upload..."
    TAR_FILE="/tmp/http2-flood-server-$(date +%s).tar.gz"
    tar -czf $TAR_FILE \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='__pycache__' \
        --exclude='gcp-*.sh' \
        --exclude='deploy*.sh' \
        --exclude='attacks/' \
        victims/ $COMMAND/
    
    # Upload server files to VM
    print_info "Uploading server files to VM..."
    gcloud compute scp $TAR_FILE $VM_NAME:"$HOME"/http2-flood-server-update.tar.gz --zone=$ZONE $GCLOUD_SSH_FLAGS


    # Deploy server on VM
    print_info "Deploying victim server on VM..."
    # Note: This remote script is a bit messy (mixing docker-compose and docker compose)
    # But we will preserve its logic.
    DEPLOY_SCRIPT="
        set -e
        # Helper function to run docker-compose with compatibility
        dc() {
            if command -v docker-compose >/dev/null 2>&1; then
                sudo docker-compose \"\$@\"
            else
                sudo docker compose \"\$@\"
            fi
        }

        cd \$HOME

        # Create/Clear directory
        mkdir -p http2-flood-lab
        cd http2-flood-lab
        
        # Kill existing victim servers (ensures clean state)
        for part in part-A part-B; do
            if [ -d \$part ]; then
                echo \"Stopping \$part victim server...\"
                cd \$part
                # Use the 'down' command for a full cleanup
                dc -f docker-compose.yml down --remove-orphans 2>/dev/null || true
                cd ..
            fi
        done
        
        # Extract new server files
        echo \"Extracting new server files...\"
        tar -xzf \$HOME/http2-flood-server-update.tar.gz -C \$HOME/http2-flood-lab
        
        # Set environment variables
        export SCENARIO='$SCENARIO'
        export WORKLOAD='$WORKLOAD'
        
        # Deploy the victim server
        echo \"Deploying $COMMAND...\"
        cd $COMMAND
        dc -f docker-compose.yml up -d --build
        
        echo 'Victim server deployment completed!'
        echo 'Checking container status...'
        sleep 5
        dc ps
    "
    
    # Execute deployment on VM
    if gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS --command="$DEPLOY_SCRIPT"; then
        # Health check
        if check_http2_server "http://$EXTERNAL_IP:$TARGET_PORT"; then
            print_success "GCP victim server deployment completed successfully!"
            echo ""
            print_success "Server is running at: http://$EXTERNAL_IP:$TARGET_PORT"
            print_info "Health check: curl --http2-prior-knowledge http://$EXTERNAL_IP:$TARGET_PORT/health"
            echo ""
            echo "=================================================="
            print_info "GCP Server Monitoring Commands:"
            echo "  curl --http2-prior-knowledge --no-progress-meter -o /dev/null -w \"Time: %{time_total}s\n\" http://$EXTERNAL_IP:$TARGET_PORT"
            echo "  gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS --command=\"docker stats --no-stream\""
            if [[ "$COMMAND" == *"part-A"* ]]; then
                echo "  gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS --command=\"docker exec dev-victim-server sh -c \\\"awk 'NR>1 && \\\$4==\\\"01\\\" {count++} END {print count+0}' /proc/net/tcp\\\"\""
            else
                echo "  gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS --command=\"docker exec prod-victim-server sh -c \\\"awk 'NR>1 && \\\$4==\\\"01\\\" {count++} END {print count+0}' /proc/net/tcp\\\"\""
            fi
            echo "=================================================="
            echo ""
            print_info "Control Commands:"
            echo "  ./deploy-server.sh --gcp --stop        # Stop victim servers"
            echo "  ./deploy-server.sh --gcp --destruct-vm   # Completely delete VM + firewall"
            echo ""
            print_info "To attack this server:"
            echo "  ./deploy-attack.sh --gcp $COMMAND      # From local to GCP server"
        else
            print_error "Server deployment failed health check!"
            exit 1
        fi
    else
        print_error "GCP server deployment failed!"
        print_info "Check VM logs: gcloud compute ssh $VM_NAME --zone=$ZONE $GCLOUD_SSH_FLAGS"
        exit 1
    fi
    
    # Clean up local temp file
    rm -f $TAR_FILE
    
    print_info "Server deployment complete. VM will auto-shutdown in 2 hours if idle."

fi