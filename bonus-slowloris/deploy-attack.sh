#!/bin/bash

set -e

# Default values
DEFAULT_CONNECTIONS_BASIC=256
DEFAULT_CONNECTIONS_ADVANCED=512
DEFAULT_CONNECTIONS_CLOUD=512

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Load GCP configuration if available, otherwise use defaults
if [ -f "gcp.env" ]; then
    echo -e "${BLUE}[INFO]${NC} Loading GCP configuration from gcp.env"
    source gcp.env
    TARGET_SERVER_IP="$TARGET_IP"
    VM_NAME="$GCP_VM_NAME"
    ZONE="$GCP_ZONE"
    PROJECT="$GCP_PROJECT_ID"
else
    echo -e "${YELLOW}[WARNING]${NC} gcp.env not found, using hardcoded defaults"
    echo -e "${BLUE}[INFO]${NC} Run './setup-gcp-infrastructure.sh' to create proper configuration"
    TARGET_SERVER_IP=""
    VM_NAME="slowloris-victim"
    ZONE="us-central1-a"
    PROJECT=""
fi

# Function to display usage
usage() {
    echo "Bonus Slowloris Lab - Attack Deployment"
    echo ""  
    echo "Usage: $0 [ATTACK_TYPE] [TARGET] [OPTIONS]"
    echo ""
    echo "ATTACK_TYPE:"
    echo "  basic     - Basic slowloris attack (HTTP/1.1)"
    echo "  advanced  - Advanced slowloris with threading and adaptive pacing"
    echo "  cloud     - Cloud-optimized attack with evasion techniques"
    echo ""
    echo "TARGET:"
    echo "  local     - Attack local containerized server"
    echo "  gcp       - Attack GCP-hosted server (uses gcp.env config)"
    echo ""
    echo "OPTIONS:"
    echo "  --connections NUM    Override default connection count"
    echo "  --server-type TYPE   Force server type (old|latest) for local attacks"
    echo "  --logs              Follow attack container logs after deployment"
    echo "  --stop              Stop running attack containers"
    echo "  --help              Show this help message"
    echo ""
    echo "Default connection counts:"
    echo "  basic: $DEFAULT_CONNECTIONS_BASIC, advanced: $DEFAULT_CONNECTIONS_ADVANCED, cloud: $DEFAULT_CONNECTIONS_CLOUD"
    echo ""
    echo "Examples:"
    echo "  $0 basic local --logs"
    echo "  $0 advanced gcp --connections 300"
    echo "  $0 --stop"
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

# Function to stop attack containers
stop_attacks() {
    log "Stopping attack containers..."
    
    containers=$(docker ps -q --filter "name=slowloris-*-attack" 2>/dev/null || true)
    if [ -n "$containers" ]; then
        docker stop $containers
        log_success "Attack containers stopped and preserved for inspection"
    else
        log_warning "No running attack containers found"
    fi
}

# Function to check if target is reachable
health_check() {
    local target_ip="$1"
    local target_port="$2"
    
    log "Performing health check on $target_ip:$target_port..."
    
    # Try HTTP/1.1 connection
    if timeout 10 curl -s --max-time 5 --connect-timeout 5 \
       -H "Connection: close" \
       "http://$target_ip:$target_port/" > /dev/null 2>&1; then
        log_success "Health check passed - target is responding"
        return 0
    else
        log_error "Health check failed - target not responding on $target_ip:$target_port"
        return 1
    fi
}

# Function to get GCP VM IP
get_gcp_target_ip() {
    log "Retrieving GCP VM external IP..."
    
    # Auto-detect GCP project
    local project=$(gcloud config get-value project 2>/dev/null)
    if [ -z "$project" ]; then
        log_error "No GCP project configured. Run 'gcloud init' first."
        exit 1
    fi
    
    # Use configuration from gcp.env if available
    local vm_name="$VM_NAME"
    local zone="$ZONE"
    
    # Check if we have configured IP first
    if [ -n "$TARGET_SERVER_IP" ] && [ "$TARGET_SERVER_IP" != "0.0.0.0" ]; then
        echo "$TARGET_SERVER_IP"
        return
    fi
    
    # Fallback to querying GCP
    local ip=$(gcloud compute instances describe "$vm_name" \
        --zone="$zone" \
        --format="get(networkInterfaces[0].accessConfigs[0].natIP)" 2>/dev/null)
    
    if [ -z "$ip" ]; then
        log_error "Could not retrieve GCP VM IP. Ensure VM '$vm_name' exists and is running."
        log "Run './setup-gcp-infrastructure.sh' to create the VM first."
        exit 1
    fi
    
    log_success "Found GCP target: $ip"
    echo "$ip"
}

# Function to get local target IP with improved detection
get_local_target_ip() {
    local forced_server_type="$1"
    
    # Get list of running server containers
    local old_running=$(docker ps --format "{{.Names}}" | grep -c "^slowloris-old-server$" || echo "0")
    local latest_running=$(docker ps --format "{{.Names}}" | grep -c "^slowloris-latest-server$" || echo "0")
    
    local server_type=""
    
    if [ -n "$forced_server_type" ]; then
        # User specified server type explicitly
        server_type="$forced_server_type"
        local container_name="slowloris-${server_type}-server"
        
        if ! docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
            log_error "Specified server type '$server_type' is not running"
            log "Run './deploy-server.sh $server_type local' to start the server first"
            exit 1
        fi
        
        log "Using explicitly specified server type: $server_type"
    elif [ "$old_running" -eq 1 ] && [ "$latest_running" -eq 0 ]; then
        # Only old server running
        server_type="old"
        log "Auto-detected server type: old"
    elif [ "$old_running" -eq 0 ] && [ "$latest_running" -eq 1 ]; then
        # Only latest server running
        server_type="latest"
        log "Auto-detected server type: latest"
    elif [ "$old_running" -eq 1 ] && [ "$latest_running" -eq 1 ]; then
        # Both servers running - require user input
        log_error "Both 'old' and 'latest' servers are running. Please specify which one to target:"
        echo ""
        echo "  $0 $ATTACK_TYPE $TARGET --server-type old [other options]"
        echo "  $0 $ATTACK_TYPE $TARGET --server-type latest [other options]"
        echo ""
        echo "Running servers:"
        echo "  - slowloris-old-server"
        echo "  - slowloris-latest-server"
        exit 1
    else
        # No servers running
        log_error "No local server containers found"
        echo ""
        echo "Available server types:"
        echo "  ./deploy-server.sh old local     # Apache 2.2.14 (vulnerable)"
        echo "  ./deploy-server.sh latest local  # Modern Apache"
        exit 1
    fi
    
    # For bridge networking, use localhost with mapped port
    echo "localhost"
}

# Function to get target port based on deployment type
get_target_port() {
    local target="$1"
    case "$target" in
        local) echo "8080" ;;
        gcp) echo "8080" ;;
        *) echo "8080" ;;
    esac
}

# Function to remove old attack containers
cleanup_old_containers() {
    local attack_type="$1"
    local container_name="slowloris-${attack_type}-attack"
    
    log "Cleaning up old containers..."
    
    # Remove existing container if it exists
    if docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
        docker rm -f "$container_name" >/dev/null 2>&1
        log "Removed old container: $container_name"
    fi
}

# Function to build attack container
build_attack_container() {
    log "Building attack container..."
    cd attacks
    docker build --no-cache -t slowloris-attack -f Dockerfile.attack .
    cd ..
    log_success "Attack container built successfully"
}

# Function to run attack
run_attack() {
    local attack_type="$1"
    local target_ip="$2"
    local target_port="$3"
    local connections="$4"
    
    local container_name="slowloris-${attack_type}-attack"
    local script_name=""
    local extra_args=""
    
    # Determine script and arguments based on attack type
    case "$attack_type" in
        basic)
            script_name="slowloris.py"
            extra_args="--port $target_port"
            ;;
        advanced)
            script_name="advanced_slowloris.py"
            extra_args="--port $target_port --header-size 100 --sleep 15"
            ;;
        cloud)
            script_name="cloud_advanced_slowloris.py"
            extra_args="--port $target_port --header-size 150 --sleep 12 --adaptive --stealth"
            ;;
    esac
    
    log "Launching $attack_type attack against $target_ip:$target_port with $connections connections..."
    
    # Run attack container in detached mode
    docker run -d \
        --name "$container_name" \
        --network bridge \
        slowloris-attack \
        python "$script_name" "$target_ip" "$connections" $extra_args
    
    log_success "Attack container '$container_name' started successfully"
    log "Monitor with: docker logs -f $container_name"
}

# Function to display monitoring commands
show_monitoring_commands() {
    local attack_type="$1"
    local target="$2"
    local container_name="slowloris-${attack_type}-attack"
    
    echo ""
    log_success "Attack launched! Use these commands to monitor:"
    echo ""
    echo -e "${GREEN}# Monitor attack logs:${NC}"
    echo "docker logs -f $container_name"
    echo ""
    echo -e "${GREEN}# Check attack container status:${NC}"
    echo "docker ps --filter name=$container_name"
    echo ""
    
    if [ "$target" = "local" ]; then
        echo -e "${GREEN}# Monitor server connections (run in another terminal):${NC}"
        echo 'docker exec slowloris-*-server sh -c "awk '"'"'NR>1 && \$4==\"01\" {count++} END {print count+0}'"'"' /proc/net/tcp"'
        echo ""
        echo -e "${GREEN}# Test server response time:${NC}"
        echo "curl --no-progress-meter -o /dev/null -w \"Time: %{time_total}s\\n\" http://localhost:8080"
    else
        echo -e "${GREEN}# Test server response time:${NC}"
        echo "curl --no-progress-meter -o /dev/null -w \"Time: %{time_total}s\\n\" http://\$(gcloud compute instances describe slowloris-victim --format=\"get(networkInterfaces[0].accessConfigs[0].natIP)\"):8080"
    fi
    
    echo ""
    echo -e "${GREEN}# Stop attack (preserving container for inspection):${NC}"
    echo "$0 --stop"
    echo ""
}

# Parse command line arguments
ATTACK_TYPE=""
TARGET=""
CONNECTIONS=""
SERVER_TYPE=""
STOP=false
FOLLOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        basic|advanced|cloud)
            ATTACK_TYPE="$1"
            shift
            ;;
        local|gcp)
            TARGET="$1"
            shift
            ;;
        --connections)
            CONNECTIONS="$2"
            shift 2
            ;;
        --server-type)
            SERVER_TYPE="$2"
            if [[ "$SERVER_TYPE" != "old" && "$SERVER_TYPE" != "latest" ]]; then
                log_error "Invalid server type: $SERVER_TYPE. Must be 'old' or 'latest'"
                exit 1
            fi
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
    stop_attacks
    exit 0
fi

# Validate required arguments
if [ -z "$ATTACK_TYPE" ] || [ -z "$TARGET" ]; then
    log_error "Missing required arguments"
    usage
    exit 1
fi

# Set default connections if not specified
if [ -z "$CONNECTIONS" ]; then
    case "$ATTACK_TYPE" in
        basic) CONNECTIONS=$DEFAULT_CONNECTIONS_BASIC ;;
        advanced) CONNECTIONS=$DEFAULT_CONNECTIONS_ADVANCED ;;
        cloud) CONNECTIONS=$DEFAULT_CONNECTIONS_CLOUD ;;
    esac
fi

# Validate Docker is available
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed or not in PATH"
    exit 1
fi

# Get target IP and port
case "$TARGET" in
    local)
        TARGET_IP=$(get_local_target_ip "$SERVER_TYPE")
        ;;
    gcp)
        if ! command -v gcloud &> /dev/null; then
            log_error "gcloud CLI is not installed"
            exit 1
        fi
        TARGET_IP=$(get_gcp_target_ip)
        ;;
esac

TARGET_PORT=$(get_target_port "$TARGET")

# Perform health check
if ! health_check "$TARGET_IP" "$TARGET_PORT"; then
    exit 1
fi

# Clean up old containers
cleanup_old_containers "$ATTACK_TYPE"

# Build attack container
build_attack_container

# Run attack
run_attack "$ATTACK_TYPE" "$TARGET_IP" "$TARGET_PORT" "$CONNECTIONS"

# Show monitoring commands
show_monitoring_commands "$ATTACK_TYPE" "$TARGET"

# Follow logs if requested
if [ "$FOLLOW_LOGS" = true ]; then
    container_name="slowloris-${ATTACK_TYPE}-attack"
    echo ""
    log "Following logs for $container_name (Ctrl+C to exit)..."
    sleep 2
    docker logs -f "$container_name"
else
    log_success "Deployment complete!"
fi