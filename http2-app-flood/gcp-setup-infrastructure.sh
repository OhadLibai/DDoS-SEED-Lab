#!/bin/bash
# HTTP/2 Flood Lab - GCP Infrastructure Setup (One-Time)
# Creates VM and prepares environment for multiple lab deployments

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

# Configuration
VM_NAME="http2-flood-lab"
ZONE="us-central1-a"
MACHINE_TYPE="f1-micro"  # Free tier eligible

usage() {
    echo "HTTP/2 Flood Lab - Infrastructure Setup"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "This script creates the GCP infrastructure once."
    echo "After setup, use lab-deploy.sh to deploy different lab configurations."
    echo ""
    echo "Options:"
    echo "  --force     Delete existing VM and create new one"
    echo "  --help      Show this help message"
    echo ""
    exit 1
}

# Parse arguments
FORCE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --help)
            usage
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Check if gcloud is available
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI not found. Please install Google Cloud SDK."
    exit 1
fi

print_info "Setting up HTTP/2 Flood Lab Infrastructure on GCP"

# Check if VM already exists
if gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
    if [ "$FORCE" = true ]; then
        print_warning "Deleting existing VM..."
        gcloud compute instances delete $VM_NAME --zone=$ZONE --quiet
    else
        print_error "VM '$VM_NAME' already exists!"
        print_info "Use --force to recreate, or use lab-deploy.sh to deploy labs on existing VM."
        exit 1
    fi
fi

print_info "Creating VM instance..."
# Create VM with startup script
gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --metadata-from-file startup-script=gcp/install-deps.sh \
    --tags=http-server,https-server

# Wait for VM to be ready
print_info "Waiting for VM to be ready (this may take 2-3 minutes)..."
sleep 30

# Wait for startup script to complete
print_info "Waiting for dependency installation to complete..."
for i in {1..20}; do
    if gcloud compute ssh $VM_NAME --zone=$ZONE --command="docker --version" &>/dev/null; then
        break
    fi
    print_info "Still setting up dependencies... ($i/20)"
    sleep 15
done

# Verify Docker is working
if ! gcloud compute ssh $VM_NAME --zone=$ZONE --command="docker --version" &>/dev/null; then
    print_error "Docker installation failed. Check VM logs."
    exit 1
fi

# Create firewall rule if it doesn't exist
if ! gcloud compute firewall-rules describe allow-lab-traffic &>/dev/null; then
    print_info "Creating firewall rule..."
    gcloud compute firewall-rules create allow-lab-traffic \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow HTTP/2 Flood Lab traffic"
fi

# Get VM external IP
EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

print_success "Infrastructure setup completed!"
echo ""
print_info "VM Details:"
echo "  Name: $VM_NAME"
echo "  Zone: $ZONE"
echo "  External IP: $EXTERNAL_IP"
echo "  Machine Type: $MACHINE_TYPE (Free tier eligible)"
echo ""
print_info "Next Steps:"
echo "  1. Deploy labs: ./lab-deploy.sh part-A"
echo "  2. Control labs: ./lab-control.sh status"
echo "  3. Access lab: http://$EXTERNAL_IP:8080"
echo ""
print_warning "VM will auto-shutdown after 2 hours to prevent unexpected charges."
print_info "Use 'gcloud compute instances start $VM_NAME --zone=$ZONE' to restart if needed."