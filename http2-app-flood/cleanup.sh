#!/bin/bash
# HTTP/2 Flood Lab - Unified Cleanup Script
# Clean up local Docker containers and/or GCP lab resources

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration for GCP
VM_NAME="http2-flood-lab"
ZONE="us-central1-a"

usage() {
    echo "HTTP/2 Flood Lab - Unified Cleanup"
    echo ""
    echo "Usage: $0 [--local|--gcp|--all] [options]"
    echo ""
    echo "Options:"
    echo "  (no flags)      Clean local Docker containers (default, backward compatible)"
    echo "  --local         Clean local Docker containers explicitly"
    echo "  --gcp           Stop GCP lab containers (keep VM running)"
    echo "  --gcp --vm      Stop GCP lab containers + shutdown VM (save costs)"
    echo "  --all           Clean both local Docker + GCP lab"
    echo ""
    echo "Examples:"
    echo "  $0              # Default: local cleanup only"
    echo "  $0 --local      # Explicit local cleanup"
    echo "  $0 --gcp        # Stop GCP lab, keep VM"
    echo "  $0 --gcp --vm   # Stop GCP lab + VM (cost savings)"
    echo "  $0 --all        # Clean everything"
    echo ""
    exit 1
}

cleanup_local() {
    print_info "Cleaning up local HTTP/2 Flood Lab..."
    
    # Stop and remove containers from both parts
    for part in part-A part-B; do
        if [ -d "$part" ]; then
            print_info "Stopping local $part containers..."
            cd "$part"
            docker-compose down --remove-orphans > /dev/null 2>&1 || true
            cd ..
        fi
    done
    
    # Clean up Docker resources
    print_info "Removing unused Docker resources..."
    docker system prune -f > /dev/null 2>&1 || true
    
    print_success "Local cleanup completed!"
}

cleanup_gcp() {
    local shutdown_vm=$1
    
    # Check if gcloud is available
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI not found. Cannot perform GCP cleanup."
        print_info "Install Google Cloud SDK or use --local for local cleanup only."
        exit 1
    fi
    
    # Check if VM exists
    if ! gcloud compute instances describe $VM_NAME --zone=$ZONE &>/dev/null; then
        print_warning "VM '$VM_NAME' not found. Nothing to clean up in GCP."
        return 0
    fi
    
    VM_STATUS=$(gcloud compute instances describe $VM_NAME --zone=$ZONE --format='get(status)')
    if [ "$VM_STATUS" != "RUNNING" ]; then
        if [ "$shutdown_vm" = true ]; then
            print_info "VM is already stopped."
        else
            print_warning "VM is not running. No containers to stop."
        fi
        return 0
    fi
    
    print_info "Cleaning up GCP HTTP/2 Flood Lab..."
    
    # Stop lab containers
    print_info "Stopping GCP lab containers..."
    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
        cd ~/http2-flood-lab 2>/dev/null || { echo 'No lab deployed'; exit 0; }
        for part in part-A part-B; do
            if [ -d \$part ]; then
                echo \"Stopping \$part containers...\"
                cd \$part
                docker-compose down --remove-orphans || true
                cd ..
            fi
        done
        echo 'GCP lab containers stopped'
    " 2>/dev/null || print_warning "Could not connect to VM or no lab deployed"
    
    # Shutdown VM if requested
    if [ "$shutdown_vm" = true ]; then
        print_info "Shutting down VM to save costs..."
        gcloud compute instances stop $VM_NAME --zone=$ZONE
        print_success "GCP cleanup completed with VM shutdown!"
        print_info "VM stopped. Use 'gcloud compute instances start $VM_NAME --zone=$ZONE' to restart."
    else
        print_success "GCP lab cleanup completed!"
        print_info "VM remains running for quick restart. Use '$0 --gcp --vm' to shutdown VM and save costs."
    fi
}

# Parse arguments
TARGET=""
SHUTDOWN_VM=false

if [ $# -eq 0 ]; then
    # Default behavior: local cleanup (backward compatible)
    TARGET="local"
elif [ "$1" = "--help" ]; then
    usage
elif [ "$1" = "--local" ]; then
    TARGET="local"
elif [ "$1" = "--gcp" ]; then
    TARGET="gcp"
    if [ "$2" = "--vm" ]; then
        SHUTDOWN_VM=true
    fi
elif [ "$1" = "--all" ]; then
    TARGET="all"
    if [ "$2" = "--vm" ]; then
        SHUTDOWN_VM=true
    fi
else
    print_error "Invalid option: $1"
    usage
fi

# Execute cleanup based on target
case $TARGET in
    "local")
        cleanup_local
        ;;
    "gcp")
        cleanup_gcp $SHUTDOWN_VM
        ;;
    "all")
        print_info "Performing complete cleanup (local + GCP)..."
        cleanup_local
        echo ""
        cleanup_gcp $SHUTDOWN_VM
        echo ""
        print_success "Complete cleanup finished!"
        ;;
    *)
        print_error "Unknown target: $TARGET"
        usage
        ;;
esac

print_info "All lab containers have been stopped and removed."