#!/bin/bash
# GCP VM Setup Script for HTTP/2 Flood Lab (Free Tier)

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
VM_NAME="http2-flood-lab"
ZONE="us-central1-a"
MACHINE_TYPE="e2-micro"  # Free tier eligible
IMAGE_FAMILY="ubuntu-2004-lts"
IMAGE_PROJECT="ubuntu-os-cloud"
DISK_SIZE="10GB"

print_info "Creating GCP VM for HTTP/2 Flood Lab (Free Tier)"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed. Please install Google Cloud SDK first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_error "Not authenticated with Google Cloud. Run 'gcloud auth login' first."
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_error "No project set. Run 'gcloud config set project PROJECT_ID' first."
    exit 1
fi

print_info "Using project: $PROJECT_ID"
print_info "Creating VM: $VM_NAME in zone: $ZONE"

# Enable required APIs
print_info "Enabling Compute Engine API..."
gcloud services enable compute.googleapis.com

# Create VM instance
if gcloud compute instances create $VM_NAME \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --image-family=$IMAGE_FAMILY \
    --image-project=$IMAGE_PROJECT \
    --boot-disk-size=$DISK_SIZE \
    --boot-disk-type=pd-standard \
    --tags=http2-lab \
    --metadata-from-file startup-script=./install-deps.sh; then
    
    print_success "VM created successfully!"
    
    # Get external IP
    EXTERNAL_IP=$(gcloud compute instances describe $VM_NAME \
        --zone=$ZONE \
        --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
    
    print_success "VM External IP: $EXTERNAL_IP"
    print_info "VM will automatically install dependencies on first boot."
    print_info "This may take 3-5 minutes. You can monitor with:"
    echo "  gcloud compute ssh $VM_NAME --zone=$ZONE --command='tail -f /var/log/startup.log'"
    
else
    print_error "Failed to create VM!"
    exit 1
fi