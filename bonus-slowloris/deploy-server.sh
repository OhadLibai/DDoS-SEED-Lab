#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
if [ -f "gcp.env" ]; then
    FILE=gcp.env && cp -- "$FILE" "$FILE.bak" \
    && sed -E '
        # Remove ANSI color codes
        s/\x1b\[[0-9;]*[mGKH]//g
        # Remove timestamps like [2025-10-04 10:30:15]
        s/\[[0-9]{4}-[0-9]{2}-[0-9]{2}[^]]*\]//g
        # Remove any leading whitespace/control characters
        s/^[[:space:][:cntrl:]]+//
        # Extract variable assignments: VAR=anything: value -> VAR=value
        s/^([A-Za-z_][A-Za-z0-9_]*)=.*:[[:space:]]*([^[:space:]].*)$/\1=\2/
        # Also handle simple VAR=value (no colon)
        s/^([A-Za-z_][A-Za-z0-9_]*)=([^[:space:]].*)/\1=\2/
    ' "$FILE" \
    | grep -E '^[[:space:]]*#|^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' \
    > "$FILE.clean" \
    && mv -- "$FILE.clean" "$FILE"
fi

if [ -f ".gcp-config" ]; then
    FILE=.gcp-config && cp -- "$FILE" "$FILE.bak" \
    && sed -E '
        s/\x1b\[[0-9;]*[mGKH]//g
        s/\[[0-9]{4}-[0-9]{2}-[0-9]{2}[^]]*\]//g
        s/^[[:space:][:cntrl:]]+//
        s/^([A-Za-z_][A-Za-z0-9_]*)=.*:[[:space:]]*([^[:space:]].*)$/\1=\2/
        s/^([A-Za-z_][A-Za-z0-9_]*)=([^[:space:]].*)/\1=\2/
    ' "$FILE" \
    | grep -E '^[[:space:]]*#|^[[:space:]]*[A-Za-z_][A-Za-z0-9_]*=' \
    > "$FILE.clean" \
    && mv -- "$FILE.clean" "$FILE"
fi


# Load GCP configuration if available, otherwise use defaults
if [ -f "gcp.env" ]; then
    echo -e "${BLUE}[INFO]${NC} Loading GCP configuration from gcp.env"
    source gcp.env
    VM_NAME="$GCP_VM_NAME"
    ZONE="$GCP_ZONE"
    PROJECT="$GCP_PROJECT_ID"
else
    echo -e "${BLUE}[INFO]${NC} gcp.env not found, using hardcoded defaults"
    echo -e "${BLUE}[INFO]${NC} Run './setup-gcp-infrastructure.sh' to create proper configuration"
    VM_NAME="slowloris-victim"
    ZONE="us-central1-a"
    PROJECT=""
fi

# Function to display usage
usage() {
    echo "Usage: $0 [SERVER_TYPE] [TARGET] [OPTIONS]"
    echo ""
    echo "SERVER_TYPE:"
    echo "  old       - Apache 2.2.14 (vulnerable to basic slowloris)"
    echo "  latest    - Apache latest (for advanced attacks)"
    echo ""
    echo "TARGET:"
    echo "  local     - Deploy server locally in container"
    echo "  gcp       - Deploy server on GCP VM"
    echo ""
    echo "OPTIONS:"
    echo "  --port PORT         Override default port (default: 8080)"
    echo "  --logs              Follow server container logs after deployment"
    echo "  --stop              Stop server containers/VM"
    echo "  --destruct-vm       Completely destroy GCP VM and resources"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 old local"
    echo "  $0 latest gcp --port 9090"
    echo "  $0 --stop"
    echo "  $0 --destruct-vm"
}

# Function to log messages
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

log_error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

# Function to stop local server containers
stop_local_servers() {
    log "Stopping local server containers..." >&2

    # Use a more robust regex filter to find the server containers
    containers=$(docker ps -q --filter "name=^slowloris-.*-server$" 2>/dev/null || true)
    
    if [ -n "$containers" ]; then
        docker stop $containers
        docker rm $containers # Also remove the containers after stopping
        log_success "Server containers stopped and removed" >&2
    else
        log_warning "No running server containers found" >&2
    fi
}

# Function to stop GCP VM
stop_gcp_vm() {
    local vm_name="$VM_NAME"
    local zone="$ZONE"
    local project="$PROJECT"
    
    if [ -z "$project" ]; then
        project=$(gcloud config get-value project 2>/dev/null)
    fi
    
    if [ -z "$project" ]; then
        log_error "No GCP project configured"
        return 1
    fi
    
    log "Stopping GCP VM: $vm_name in zone $zone..."
    
    if gcloud compute instances describe "$vm_name" --zone="$zone" >/dev/null 2>&1; then
        gcloud compute instances stop "$vm_name" --zone="$zone" --quiet
        log_success "GCP VM stopped"
    else
        log_warning "VM $vm_name not found or already stopped"
    fi
}

# Function to destroy GCP VM and resources
destroy_gcp_vm() {
    if [ ! -f "gcp.env" ]; then
        log_error "No gcp.env found. Nothing to destroy."
        log_error "Run './setup-gcp-infrastructure.sh' to create infrastructure first."
        return 1
    fi
    
    local vm_name="$VM_NAME"
    local zone="$ZONE"
    local project="$PROJECT"
    local firewall_rule="$FIREWALL_RULE_NAME"
    
    if [ -z "$project" ]; then
        project=$(gcloud config get-value project 2>/dev/null)
    fi
    
    if [ -z "$project" ]; then
        log_error "No GCP project configured"
        return 1
    fi
    
    log "Destroying GCP resources..."
    
    # Delete VM instance
    if gcloud compute instances describe "$vm_name" --zone="$zone" >/dev/null 2>&1; then
        log "Deleting VM instance: $vm_name"
        gcloud compute instances delete "$vm_name" --zone="$zone" --quiet
    fi
    
    # Delete firewall rule
    if gcloud compute firewall-rules describe "$firewall_rule" >/dev/null 2>&1; then
        log "Deleting firewall rule: $firewall_rule"
        gcloud compute firewall-rules delete "$firewall_rule" --quiet
    fi
    
    # Remove config file
    rm -f gcp.env
    
    log_success "GCP resources destroyed successfully"
}

# Function to get default port
get_default_port() {
    local target="$1"
    case "$target" in
        local) echo "8080" ;;
        gcp) echo "8080" ;;
        *) echo "8080" ;;
    esac
}

# Function to cleanup old local containers
cleanup_old_local_containers() {
    local server_type="$1"
    local container_name="slowloris-${server_type}-server"
    
    log "Cleaning up old containers..."
    
    # Remove existing container if it exists
    if docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        docker rm -f "$container_name" >/dev/null 2>&1
        log "Removed old container: $container_name"
    fi
}

# Function to build server container
build_server_container() {
    local server_type="$1"
    
    log "Building $server_type server container..."
    
    cd "victims/${server_type}-apache"
    docker build --no-cache -t "slowloris-${server_type}-server" .
    cd ../..
    
    log_success "Server container built successfully"
}

# Function to deploy local server
deploy_local_server() {
    local server_type="$1"
    local port="$2"
    local container_name="slowloris-${server_type}-server"
    
    # --- ADD THIS BLOCK ---
    local network_name="slowloris-net"
    if ! docker network ls --format "{{.Name}}" | grep -q "^${network_name}$"; then
        log "Creating docker network: $network_name"
        docker network create "$network_name"
    fi
    # --- END OF BLOCK ---

    log "Deploying local $server_type server on port $port..."
    
    # Run server container
    docker run -d \
        --name "$container_name" \
        --network "slowloris-net" \
        -p "$port:80" \
        "slowloris-${server_type}-server"
    
    # Wait for server to start
    log "Waiting for server to start..."
    sleep 3
    
    # Test server
    if curl -s --max-time 5 "http://localhost:$port" >/dev/null; then
        log_success "Local $server_type server deployed successfully on http://localhost:$port"
    else
        log_error "Server deployment failed - not responding"
        return 1
    fi
}

# Function to deploy GCP server
deploy_gcp_server() {
    local server_type="$1"
    local port="$2"
    
    if [ -f "gcp.env" ]; then
        log_info "Loading GCP configuration from gcp.env"
        source gcp.env
    elif [ -f ".gcp-config" ]; then
        log_info "Loading GCP configuration from .gcp-config (deprecated - consider renaming to gcp.env)"
        source .gcp-config
    else
        log_error "No gcp.env found. Run './setup-gcp-infrastructure.sh' first to create your GCP configuration."
        log_info "The gcp.env file should contain: GCP_VM_NAME, GCP_ZONE, and GCP_PROJECT_ID"
        return 1
    fi
    
    local project=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$project" ]; then
        log_error "No GCP project configured"
        return 1
    fi
    
    log "Deploying $server_type server on GCP VM..."
    
    # Check if VM exists and is running
    local vm_status=$(gcloud compute instances describe "$VM_NAME" \
        --zone="$GCP_ZONE" \
        --format="get(status)" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$vm_status" = "NOT_FOUND" ]; then
        log_error "GCP VM not found. Run './setup-gcp-infrastructure.sh' first."
        return 1
    fi
    
    if [ "$vm_status" != "RUNNING" ]; then
        log "Starting GCP VM..."
        gcloud compute instances start "$VM_NAME" --zone="$GCP_ZONE" --quiet
        sleep 30  # Wait for VM to fully start
    fi
    
    # Get VM IP
    local vm_ip=$(gcloud compute instances describe "$VM_NAME" \
        --zone="$GCP_ZONE" \
        --format="get(networkInterfaces[0].accessConfigs[0].natIP)")
    
    if [ -z "$vm_ip" ]; then
        log_error "Could not get VM IP address"
        return 1
    fi
    
    # Create deployment script
    cat > /tmp/deploy-server-gcp.sh << EOF
#!/bin/bash
set -e

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    sudo systemctl enable docker
    sudo systemctl start docker
fi

# Remove old container
sudo docker rm -f slowloris-${server_type}-server 2>/dev/null || true

# Create Dockerfile
mkdir -p /tmp/server
cat > /tmp/server/Dockerfile << 'DOCKERFILE'
$(cat "victims/${server_type}-apache/Dockerfile")
DOCKERFILE

# Build and run container
cd /tmp/server
sudo docker build -t slowloris-${server_type}-server .
sudo docker run -d \\
    --name slowloris-${server_type}-server \\
    --network bridge \\
    -p $port:8080 \\
    slowloris-${server_type}-server

echo "Server deployed successfully"
EOF
    
    # Copy and execute deployment script on VM
    gcloud compute scp /tmp/deploy-server-gcp.sh "$VM_NAME:/tmp/" --zone="$GCP_ZONE" --quiet
    gcloud compute ssh "$VM_NAME" --zone="$GCP_ZONE" --command="chmod +x /tmp/deploy-server-gcp.sh && /tmp/deploy-server-gcp.sh" --quiet
    
    # Clean up
    rm -f /tmp/deploy-server-gcp.sh
    
    # Test server
    log "Testing server deployment..."
    sleep 5
    
    if curl -s --max-time 10 "http://$vm_ip:$port" >/dev/null; then
        log_success "GCP $server_type server deployed successfully on http://$vm_ip:$port"
        echo ""
        log_success "Server Details:"
        echo "  - IP: $vm_ip"
        echo "  - Port: $port"
        echo "  - VM Name: $VM_NAME"
        echo "  - Zone: $GCP_ZONE"
    else
        log_error "Server deployment failed - not responding on $vm_ip:$port"
        return 1
    fi
}

# Parse command line arguments
SERVER_TYPE=""
TARGET=""
PORT=""
STOP=false
DESTRUCT_VM=false
FOLLOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        old|latest)
            SERVER_TYPE="$1"
            shift
            ;;
        local|gcp)
            TARGET="$1"
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --logs)
            FOLLOW_LOGS=true
            shift
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --destruct-vm)
            DESTRUCT_VM=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
done

# Handle stop command
if [ "$STOP" = true ]; then
    stop_local_servers
    if [ "$TARGET" = "gcp" ] || command -v gcloud &> /dev/null; then
        stop_gcp_vm
    fi
    exit 0
fi

# Handle destruct VM command
if [ "$DESTRUCT_VM" = true ]; then
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed"
        exit 1
    fi
    destroy_gcp_vm
    exit 0
fi

# Validate required arguments
if [ -z "$SERVER_TYPE" ] || [ -z "$TARGET" ]; then
    log_error "Missing required arguments"
    usage
    exit 1
fi

# Set default port if not specified
if [ -z "$PORT" ]; then
    PORT=$(get_default_port "$TARGET")
fi

# Validate Docker is available for local deployment
if [ "$TARGET" = "local" ] && ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Validate gcloud is available for GCP deployment
if [ "$TARGET" = "gcp" ] && ! command -v gcloud &> /dev/null; then
    log_error "gcloud CLI is not installed"
    exit 1
fi

# Deploy based on target
case "$TARGET" in
    local)
        cleanup_old_local_containers "$SERVER_TYPE"
        build_server_container "$SERVER_TYPE"
        deploy_local_server "$SERVER_TYPE" "$PORT"
        ;;
    gcp)
        deploy_gcp_server "$SERVER_TYPE" "$PORT"
        ;;
esac

log_success "Server deployment complete!"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = true ] && [ "$TARGET" = "local" ]; then
    container_name="slowloris-${SERVER_TYPE}-server"
    echo ""
    log "Following logs for $container_name (Ctrl+C to exit)..."
    sleep 2
    docker logs -f "$container_name"
else
    echo ""
    log "Next steps:"
    echo "  1. Launch an attack: ./deploy-attack.sh [basic|advanced|cloud] $TARGET"
    echo "  2. Stop server: $0 --stop"
    if [ "$TARGET" = "gcp" ]; then
        echo "  3. Destroy GCP resources: $0 --destruct-vm"
    fi
    if [ "$FOLLOW_LOGS" = true ] && [ "$TARGET" = "gcp" ]; then
        echo ""
        log_warning "Log following not supported for GCP deployment. Use: gcloud compute ssh $VM_NAME --command='docker logs -f slowloris-$SERVER_TYPE-server'"
    fi
fi