#!/bin/bash
# HTTP/2 Flood Lab - Attack-Only Deployment Script
# Launch attacks against running victim servers

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
    echo "HTTP/2 Flood Lab - Attack-Only Deployment"
    echo ""
    echo "Usage: $0 --local|--gcp <part-A|part-B|--stop> [options]"
    echo ""
    echo "Targets:"
    echo "  --local             Attack local victim server"
    echo "  --gcp               Attack GCP victim server from local machine"
    echo ""
    echo "Commands:"
    echo "  part-A              Attack single-worker victim server"
    echo "  part-B              Attack multi-worker victim server"
    echo "  --stop              Stop current attacks"
    echo ""
    echo "Environment Variables:"
    echo "  CONNECTIONS=<num>   Number of TCP connections (default: 4 for part-A, 8 for part-B)"
    echo "  STREAMS=<num>       Streams per connection (default: 256)"
    echo "  ATTACK=<basic|advanced>  Attack type (default: basic)"
    echo ""
    echo "Examples:"
    echo "  $0 --local part-A                    # Attack local part-A server"
    echo "  $0 --gcp part-A                      # Attack GCP part-A server from local"
    echo "  CONNECTIONS=16 $0 --local part-B     # Custom connection count"
    echo "  ATTACK=advanced $0 --gcp part-B      # Advanced attack against GCP"
    echo "  $0 --local --stop                    # Stop local attacks"
    echo ""
    exit 1
}

dc() {
    if command -v docker-compose >/dev/null 2>&1; then
        sudo docker-compose "\$@"
    else
        sudo docker compose "\$@"
    fi
    }


# HTTP/2 server health check function
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
            print_success "HTTP/2 server is healthy and ready for attack"
            return 0
        fi
        
        print_info "Attempt $attempt/$max_attempts - server not ready, retrying in 2 seconds..."
        sleep 2
        ((attempt++))
    done
    
    print_error "HTTP/2 server health check failed!"
    print_error "Make sure the victim server is running:"
    print_error "  Local:  ./deploy-server.sh --local part-A"
    print_error "  GCP:    ./deploy-server.sh --gcp part-A"
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
ATTACK=${ATTACK:-basic}
STREAMS=${STREAMS:-256}

# Set default connections based on part
if [ -z "$CONNECTIONS" ]; then
    if [ "$COMMAND" = "part-A" ]; then
        CONNECTIONS=4
    else
        CONNECTIONS=8
    fi
fi

# Validate target
if [[ "$TARGET" != "--local" && "$TARGET" != "--gcp" ]]; then
    print_error "Invalid target: $TARGET"
    usage
fi

#
# LOCAL ATTACKS (against local server)
#
if [ "$TARGET" = "--local" ]; then
    # Handle --stop command
    if [ "$COMMAND" = "--stop" ]; then
        print_info "Stopping local attacks..."
        cd attacks
        dc -f down 2>/dev/null || true
        cd ..
        print_success "Local attacks stopped successfully!"
        exit 0
    fi
    
    # Validate command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid command: $COMMAND"
        usage
    fi
    
    TARGET_URL="http://host.docker.internal:8080"
    
    # Check if local server is running
    if ! check_http2_server "http://localhost:8080"; then
        exit 1
    fi
    
    print_info "Launching HTTP/2 Flood Attack - $COMMAND (LOCAL → LOCAL)"
    print_info "Target: $TARGET_URL"
    print_info "Attack: $CONNECTIONS TCP connections, $STREAMS streams each"
    
    # Set attack script based on type
    if [ "$ATTACK" = "advanced" ]; then
        export ATTACK_SCRIPT="python cloud_http2_flood.py"
    else
        export ATTACK_SCRIPT="python http2_flood.py"
    fi
    
    print_info "Attack script: $ATTACK_SCRIPT"
    
    # Set environment variables
    export TARGET_URL
    export CONNECTIONS
    export STREAMS
    
    # Stop any existing attacks
    cd attacks
    dc -f down 2>/dev/null || true

    # Launch attack
    print_info "Building and starting attack container..."
    if dc -f up -d --build; then
        print_success "Local attack launched successfully!"
        echo
        echo "=================================================="
        print_info "Attack Monitoring Commands:"
        echo "  docker logs -f http2-attacker"
        echo "  docker stats --no-stream http2-attacker"
        echo "  curl --http2-prior-knowledge -w \"Time: %{time_total}s\n\" http://localhost:8080"
        echo "=================================================="
        echo
        print_info "To stop the attack: bash deploy-attack.sh --local --stop"
        echo
    else
        print_error "Local attack launch failed!"
        exit 1
    fi

#
# GCP ATTACKS (from local machine to GCP server)
#
elif [ "$TARGET" = "--gcp" ]; then
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Please install Google Cloud SDK."
        exit 1
    fi
    
    # Handle --stop command
    if [ "$COMMAND" = "--stop" ]; then
        print_info "Stopping GCP attacks..."
        cd attacks
        dc -f down 2>/dev/null || true
        cd ..
        print_success "GCP attacks stopped successfully!"
        exit 0
    fi
    
    # Validate command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid command: $COMMAND"
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
    
    # Check VM status
    VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(status)' 2>/dev/null)
    if [ "$VM_STATUS" != "RUNNING" ]; then
        print_warning "VM is not running (status: $VM_STATUS)"
        print_info "Starting VM..."
        gcloud compute instances start $VM_NAME --zone=$ZONE
        print_info "Waiting for VM to be ready..."
        sleep 30
    fi
    
    # Get VM external IP (prioritize gcp.env, fallback to gcloud query)
    if [ -n "$TARGET_IP" ] && [ "$TARGET_IP" != "" ]; then
        EXTERNAL_IP="$TARGET_IP"
        print_info "Using TARGET_IP from gcp.env: $EXTERNAL_IP"
    else
        print_info "TARGET_IP not set in gcp.env, querying VM directly..."
        EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
            --zone=$ZONE \
            --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null)
        
        if [ -z "$EXTERNAL_IP" ]; then
            print_error "Could not get VM external IP. Is the VM running?"
            print_info "Start the VM: gcloud compute instances start $VM_NAME --zone=$ZONE"
            exit 1
        fi
    fi
    
    TARGET_URL="http://$EXTERNAL_IP:8080"
    
    # Check if GCP server is running
    if ! check_http2_server "$TARGET_URL"; then
        print_error "GCP victim server is not running or not accessible!"
        print_info "Deploy the server first: ./deploy-server.sh --gcp $COMMAND"
        exit 1
    fi
    
    print_info "Launching HTTP/2 Flood Attack - $COMMAND (LOCAL → GCP)"
    print_info "Target: $TARGET_URL"
    print_info "Attack: $CONNECTIONS TCP connections, $STREAMS streams each"
    
    # Set attack script based on type  
    if [ "$ATTACK" = "advanced" ]; then
        export ATTACK_SCRIPT="python cloud_http2_flood.py"
    else
        export ATTACK_SCRIPT="python http2_flood.py"
    fi
    
    print_info "Attack script: $ATTACK_SCRIPT"
    
    # Set environment variables
    export TARGET_URL
    export CONNECTIONS
    export STREAMS
    
    # Stop any existing attacks
    cd attacks
    dc -f down 2>/dev/null || true

    # Launch attack
    print_info "Building and starting attack container..."
    if dc -f up -d --build; then
        print_success "GCP attack launched successfully!"
        echo ""
        print_success "Attacking GCP server at: $TARGET_URL"
        echo ""
        echo "=================================================="
        print_info "Attack Monitoring Commands:"
        echo "  docker logs -f http2-attacker"
        echo "  docker stats --no-stream http2-attacker"
        echo "  curl --http2-prior-knowledge -w \"Time: %{time_total}s\n\" $TARGET_URL"
        echo "=================================================="
        echo ""
        print_info "To stop the attack: bash deploy-attack.sh --gcp --stop"
        echo ""
    else
        print_error "GCP attack launch failed!"
        exit 1
    fi

fi