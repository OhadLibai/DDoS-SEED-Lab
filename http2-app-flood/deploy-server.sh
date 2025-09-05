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
    print_warning "gcp.env not found, using hardcoded defaults"
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
    echo "  --destruct-vm    (GCP only) COMPLETELY REMOVE cloud infrastructure - requires re-running gcp-setup-infrastructure.sh"
    echo ""
    echo "Environment Variables:"
    echo "  SCENARIO=<name>     CPU scenario: default_scenario, captcha, crypto, gaming, antibot, webservice, content"
    echo "  WORKLOAD=<1-5>      CPU workload intensity (default: 5)"
    echo ""
    echo "Examples:"
    echo "  $0 --local part-A                    # Deploy local single-worker server"
    echo "  $0 --gcp part-B                      # Deploy GCP multi-worker server"
    echo "  SCENARIO=captcha $0 --local part-A   # Local server with CAPTCHA scenario"
    echo "  $0 --local --stop                    # Stop local servers"
    echo "  $0 --gcp --stop                      # Stop containers + shutdown VM"
    echo "  $0 --gcp --destruct-vm            # Remove entire cloud infrastructure"
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
        if [ "$VM_STATUS" != "RUNNING" ]; then
            print_info "VM is already stopped."
            exit 0
        fi
        
        print_info "Stopping GCP victim servers..."
        gcloud compute ssh $VM_NAME --zone=$ZONE --command="
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
        " 2>/dev/null || print_warning "Could not connect to VM"
        
        if [ "$DESTRUCT_VM" = true ]; then
            print_warning "EXTERMINATING complete cloud infrastructure for this lab..."
            print_info "Deleting VM instance..."
            gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
            
            print_info "Deleting firewall rule..."
            FIREWALL_RULE="${FIREWALL_RULE_NAME:-allow-http2-lab}"
            gcloud compute firewall-rules delete "$FIREWALL_RULE" --quiet 2>/dev/null || true
            
            print_success "Cloud infrastructure completely removed!"
            print_info "To recreate: ./gcp-setup-infrastructure.sh YOUR_PROJECT_ID"
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
        print_info "Using TARGET_IP from gcp.env: $EXTERNAL_IP"
    else
        print_info "TARGET_IP not set in gcp.env, querying VM directly..."
        EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
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
    gcloud compute scp $TAR_FILE $VM_NAME:"$HOME"/http2-flood-server-update.tar.gz --zone=$ZONE


    # Deploy server on VM
    print_info "Deploying victim server on VM..."
    DEPLOY_SCRIPT="
        set -e
        # Helper function to run docker-compose with compatibility
        dc() {
            if command -v docker-compose >/dev/null 2>&1; then
                sudo docker-compose "\$@"
            else
                sudo docker compose "\$@"
            fi
        }

        cd \$HOME

        # Kill existing victim servers (ensures clean state)
        if [ -d http2-flood-lab ]; then
            cd http2-flood-lab
            for part in part-A part-B; do
                if [ -d \$part ]; then
                    echo \"Stopping \$part victim server...\"
                    cd \$part
                    docker compose -f docker-compose.server.yml down --remove-orphans || true
                    cd ..
                fi
            done
            cd \$HOME
        fi
        
        # Extract new server files
        tar -xzf http2-flood-server-update.tar.gz
        cd "$part"
        
        # Set environment variables
        export SCENARIO='$SCENARIO'
        export WORKLOAD='$WORKLOAD'
        
        # Deploy the victim server
        cd $COMMAND
        dc -f docker-compose.yml down --remove-orphans
        dc -f docker-compose.yml up -d --build
        
        echo 'Victim server deployment completed!'
        echo 'Checking container status...'
        sleep 5
        sudo docker-compose ps
    "
    
    # Execute deployment on VM
    if gcloud compute ssh $VM_NAME --zone=$ZONE --command="$DEPLOY_SCRIPT"; then
        # Health check
        if check_http2_server "http://$EXTERNAL_IP:8080"; then
            print_success "GCP victim server deployment completed successfully!"
            echo ""
            print_success "Server is running at: http://$EXTERNAL_IP:8080"
            print_info "Health check: curl --http2-prior-knowledge http://$EXTERNAL_IP:8080/health"
            echo ""
            echo "=================================================="
            print_info "GCP Server Monitoring Commands:"
            echo "  curl --http2-prior-knowledge --no-progress-meter -o /dev/null -w \"Time: %{time_total}s\n\" http://$EXTERNAL_IP:8080"
            echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"docker stats --no-stream\""
            if [[ "$COMMAND" == *"part-A"* ]]; then
                echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"docker exec dev-victim-server sh -c \\\"awk 'NR>1 && \\\$4==\\\"01\\\" {count++} END {print count+0}' /proc/net/tcp\\\"\""
            else
                echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command=\"docker exec prod-victim-server sh -c \\\"awk 'NR>1 && \\\$4==\\\"01\\\" {count++} END {print count+0}' /proc/net/tcp\\\"\""
            fi
            echo "=================================================="
            echo ""
            print_info "Control Commands:"
            echo "  ./deploy-server.sh --gcp --stop       # Stop victim servers"
            echo "  ./deploy-server.sh --gcp --destruct-vm  # Completely delete VM + firewall"
            echo ""
            print_info "To attack this server:"
            echo "  ./deploy-attack.sh --gcp $COMMAND     # From local to GCP server"
            echo "  ./deploy-attack.sh --local $COMMAND   # If running locally"
        else
            print_error "Server deployment failed health check!"
            exit 1
        fi
    else
        print_error "GCP server deployment failed!"
        print_info "Check VM logs: gcloud compute ssh $VM_NAME --zone=$ZONE"
        exit 1
    fi
    
    # Clean up local temp file
    rm -f $TAR_FILE
    
    print_info "Server deployment complete. VM will auto-shutdown in 2 hours if idle."

fi