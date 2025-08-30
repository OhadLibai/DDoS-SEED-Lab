#!/bin/bash
# GCP Firewall Configuration for HTTP/2 Flood Lab

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }

FIREWALL_RULE="allow-http2-flood-lab"
VM_NAME="http2-flood-lab"
ZONE="us-central1-a"

print_info "Configuring firewall for HTTP/2 Flood Lab..."

# Create firewall rule
if gcloud compute firewall-rules describe $FIREWALL_RULE &>/dev/null; then
    print_info "Firewall rule already exists."
else
    print_info "Creating firewall rule..."
    gcloud compute firewall-rules create $FIREWALL_RULE \
        --allow tcp:8080 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow HTTP/2 Flood Lab traffic on port 8080" \
        --target-tags http2-lab
    
    print_success "Firewall rule created!"
fi

# Apply firewall tag to VM
print_info "Applying firewall tag to VM..."
gcloud compute instances add-tags $VM_NAME \
    --tags http2-lab \
    --zone=$ZONE

print_success "Firewall configuration completed!"
print_info "Port 8080 is now accessible from the internet."