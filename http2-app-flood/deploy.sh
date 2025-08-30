#!/bin/bash
# HTTP/2 Flood Lab - Unified Deployment Script
# Deploy labs locally or on GCP with a single interface

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

# Configuration for GCP
VM_NAME="http2-flood-lab"
ZONE="us-central1-a"

usage() {
    echo "HTTP/2 Flood Lab - Unified Deployment"
    echo ""
    echo "Usage: $0 --local|--gcp <part-A|part-B|--stop> [options]"
    echo ""
    echo "Targets:"
    echo "  --local             Deploy on local Docker"
    echo "  --gcp               Deploy on GCP VM (requires gcp-setup-infrastructure.sh first)"
    echo ""
    echo "Commands:"
    echo "  part-A              Deploy single-worker victim server"
    echo "  part-B              Deploy multi-worker victim server"
    echo "  --stop              Stop current lab containers"
    echo "  --stop --vm         (GCP only) Stop lab containers + shutdown VM"
    echo ""
    echo "Environment Variables:"
    echo "  SCENARIO=<name>     CPU scenario (captcha, crypto, gaming, etc.)"
    echo "  DIFFICULITY=<1-5>    CPU workload difficulty (default: 5)"
    echo "  CONNECTIONS=<num>   Number of attack connections (default: varies by part)"
    echo "  ATTACK=<basic|advanced>  Attack type for part-B (default: basic)"
    echo ""
    echo "Examples:"
    echo "  $0 --local part-A                    # Deploy locally"
    echo "  $0 --gcp part-B                      # Deploy on GCP"
    echo "  SCENARIO=captcha $0 --local part-A   # Local with CAPTCHA scenario"
    echo "  CONNECTIONS=512 $0 --gcp part-B      # GCP with custom connections"
    echo "  $0 --gcp --stop                      # Stop GCP lab"
    echo "  $0 --gcp --stop --vm                 # Stop GCP lab + VM"
    echo ""
    exit 1
}

# Check arguments
if [ $# -lt 2 ]; then
    usage
fi

TARGET=$1
COMMAND=$2
SCENARIO=${SCENARIO:-proof_of_work}
DIFFICULITY=${DIFFICULITY:-5}
CONNECTIONS=${CONNECTIONS:-}
ATTACK=${ATTACK:-basic}

# Validate target
if [[ "$TARGET" != "--local" && "$TARGET" != "--gcp" ]]; then
    print_error "Invalid target: $TARGET"
    usage
fi

#
# LOCAL DEPLOYMENT
#
if [ "$TARGET" = "--local" ]; then
    # Validate local command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid local command: $COMMAND"
        print_error "Local deployment only supports part-A and part-B"
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
        ./cleanup.sh > /dev/null 2>&1 || true
    fi
    
    print_info "Deploying HTTP/2 Flood Lab - $COMMAND (LOCAL)"
    print_info "Configuration: Scenario=$SCENARIO, Difficulty=$DIFFICULITY"
    if [ -n "$CONNECTIONS" ]; then
        print_info "Attack Connections: $CONNECTIONS"
    fi
    
    if [ "$COMMAND" = "part-B" ]; then
        if [ "$ATTACK" = "advanced" ]; then
            print_info "Using advanced cloud attack script"
            export ATTACK_SCRIPT="python cloud_http_flood.py"
        else
            print_info "Using basic attack script"
            export ATTACK_SCRIPT="python http_flood.py"
        fi
        print_info "Attack type: $ATTACK"
    fi
    
    # Set environment variables for docker-compose
    export SCENARIO
    export DIFFICULITY
    if [ -n "$CONNECTIONS" ]; then
        export CONNECTIONS
    fi
    
    # Deploy the specified part
    print_info "Building and starting containers..."
    cd "$COMMAND"
    
    if docker-compose up -d --build; then
        print_success "Local deployment completed successfully!"
        echo ""
        print_success "Lab is running at: http://localhost:8080"
        print_info "Health check: curl --http2-prior-knowledge http://localhost:8080/health"
        echo ""
        print_info "Monitoring Commands:"
        echo "  watch -n 1 'curl -w \"Response: %{time_total}s\\n\" http://localhost:8080'"
        echo "  docker stats --no-stream"
        echo "  curl -w \"Time:%{time_total}s Code:%{http_code}\\n\" http://localhost:8080"
        echo ""
        print_info "To stop the lab: ./cleanup.sh"
    else
        print_error "Local deployment failed!"
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
    
    # Handle --stop command
    if [ "$COMMAND" = "--stop" ]; then
        STOP_VM=false
        if [ "$3" = "--vm" ]; then
            STOP_VM=true
        fi
        
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
        
        print_info "Stopping GCP lab containers..."
        gcloud compute ssh $VM_NAME --zone=$ZONE --command="
            cd ~/http2-flood-lab 2>/dev/null || { echo 'No lab deployed'; exit 0; }
            for part in part-A part-B; do
                if [ -d \$part ]; then
                    echo \"Stopping \$part containers...\"
                    cd \$part
                    docker-compose stop || true
                    cd ..
                fi
            done
            echo 'Lab containers stopped'
        " 2>/dev/null || print_warning "Could not connect to VM"
        
        if [ "$STOP_VM" = true ]; then
            print_info "Shutting down VM to save costs..."
            gcloud compute instances stop $VM_NAME --zone=$ZONE
            print_success "VM shutdown complete. Use 'gcloud compute instances start $VM_NAME --zone=$ZONE' to restart."
        else
            print_success "GCP lab stopped. VM remains running for quick restart."
        fi
        exit 0
    fi
    
    # Validate GCP deployment command
    if [[ "$COMMAND" != "part-A" && "$COMMAND" != "part-B" ]]; then
        print_error "Invalid GCP command: $COMMAND"
        usage
    fi
    
    # Check if VM exists
    if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
        print_error "VM '$VM_NAME' not found!"
        print_info "Run './gcp-setup-infrastructure.sh' first to create the infrastructure."
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
    
    print_info "Deploying HTTP/2 Flood Lab - $COMMAND (GCP)"
    print_info "Configuration: Scenario=$SCENARIO, Difficulty=$DIFFICULITY"
    if [ -n "$CONNECTIONS" ]; then
        print_info "Attack Connections: $CONNECTIONS"
    fi
    
    if [ "$COMMAND" = "part-B" ]; then
        if [ "$ATTACK" = "advanced" ]; then
            print_info "Using advanced cloud attack script"
            ATTACK_SCRIPT="python cloud_http_flood.py"
        else
            print_info "Using basic attack script"
            ATTACK_SCRIPT="python http_flood.py"
        fi
        print_info "Attack type: $ATTACK"
    fi
    
    # Get VM external IP for output
    EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
        --zone=$ZONE \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    
    # Create deployment archive
    print_info "Preparing lab files for upload..."
    TAR_FILE="/tmp/http2-flood-lab-$(date +%s).tar.gz"
    tar -czf $TAR_FILE \
        --exclude='.git' \
        --exclude='*.log' \
        --exclude='__pycache__' \
        --exclude='gcp-*.sh' \
        --exclude='deploy.sh' \
        shared/ $COMMAND/ Dockerfile.attacker cleanup.sh
    
    # Upload lab files to VM
    print_info "Uploading lab files to VM..."
    gcloud compute scp $TAR_FILE $VM_NAME:~/http2-flood-lab-update.tar.gz --zone=$ZONE
    
    # Deploy on VM
    print_info "Deploying lab on VM..."
    DEPLOY_SCRIPT="
        set -e
        cd ~/
        
        # Kill ALL existing lab containers (ensures clean state)
        if [ -d http2-flood-lab ]; then
            cd http2-flood-lab
            for part in part-A part-B; do
                if [ -d \$part ]; then
                    echo \"Stopping \$part containers...\"
                    cd \$part
                    docker-compose down --remove-orphans || true
                    cd ..
                fi
            done
            cd ~/
        fi
        
        # Extract new lab files
        tar -xzf http2-flood-lab-update.tar.gz
        cd http2-flood-lab
        
        # Set environment variables
        export SCENARIO='$SCENARIO'
        export DIFFICULITY='$DIFFICULITY'"
    
    # Add CONNECTIONS if specified
    if [ -n "$CONNECTIONS" ]; then
        DEPLOY_SCRIPT="$DEPLOY_SCRIPT
        export CONNECTIONS='$CONNECTIONS'"
    fi
    
    if [ "$COMMAND" = "part-B" ]; then
        DEPLOY_SCRIPT="$DEPLOY_SCRIPT
        export ATTACK_SCRIPT='$ATTACK_SCRIPT'"
    fi
    
    DEPLOY_SCRIPT="$DEPLOY_SCRIPT
        # Deploy the lab
        cd $COMMAND
        docker-compose up -d --build
        
        echo 'Lab deployment completed!'
        echo 'Checking container status...'
        sleep 5
        docker-compose ps
    "
    
    # Execute deployment on VM
    if gcloud compute ssh $VM_NAME --zone=$ZONE --command="$DEPLOY_SCRIPT"; then
        print_success "GCP deployment completed successfully!"
        echo ""
        print_success "Lab is running at: http://$EXTERNAL_IP:8080"
        print_info "Health check: curl --http2-prior-knowledge http://$EXTERNAL_IP:8080/health"
        echo ""
        print_info "Control Commands:"
        echo "  ./deploy.sh --gcp --stop       # Stop lab containers"
        echo "  ./deploy.sh --gcp --stop --vm  # Stop lab + shutdown VM"
        echo ""
        print_info "Switch to different lab:"
        echo "  ./deploy.sh --gcp part-B       # Switch to Part B"
        echo "  SCENARIO=captcha ./deploy.sh --gcp part-A  # Switch scenario"
        echo "  CONNECTIONS=256 ./deploy.sh --gcp part-A   # Custom connections"
    else
        print_error "GCP deployment failed!"
        print_info "Check VM logs: gcloud compute ssh $VM_NAME --zone=$ZONE"
        exit 1
    fi
    
    # Clean up local temp file
    rm -f $TAR_FILE
    
    print_info "Deployment complete. VM will auto-shutdown in 2 hours if idle."

fi