#!/bin/bash

# GCP Infrastructure Setup - One-Time Setup for All Labs
# Creates reusable f1-micro instance for all HTTP/2 attack labs

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

LAB_INFRASTRUCTURE_NAME="http2-lab-infrastructure"
PROJECT_ID=""

echo -e "${BLUE}🏗️  HTTP/2 Lab Infrastructure Setup${NC}"
echo -e "${BLUE}Creating reusable GCP environment for all attack labs${NC}"
echo ""

# Check prerequisites
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found${NC}"
    echo "Run in Cloud Shell or install terraform locally"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud not found${NC}"
    echo "Run in Cloud Shell or install Google Cloud CLI locally"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Check if infrastructure already exists
if gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$LAB_INFRASTRUCTURE_NAME"; then
    INSTANCE_IP=$(gcloud compute instances list --filter="name:$LAB_INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
    echo -e "${YELLOW}⚠️  Infrastructure already exists!${NC}"
    echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
    echo -e "${BLUE}SSH access: gcloud compute ssh $LAB_INFRASTRUCTURE_NAME --zone=us-central1-a${NC}"
    echo ""
    echo -e "${GREEN}You can now deploy attacks to this existing infrastructure:${NC}"
    echo "cd zero-window/gcp && ./deploy-attack.sh"
    echo "cd slow-incremental/gcp && ./deploy-attack.sh" 
    echo "cd adaptive-slow/gcp && ./deploy-attack.sh"
    exit 0
fi

# Create infrastructure using terraform
echo -e "${GREEN}Creating GCP infrastructure...${NC}"

# Initialize terraform if not done
if [ ! -d ".terraform" ]; then
    terraform init
fi

# Create terraform variables file
cat > terraform.tfvars << EOF
project_id = "$PROJECT_ID"
infrastructure_name = "$LAB_INFRASTRUCTURE_NAME"
region = "us-central1"
zone = "us-central1-a"
EOF

# Plan and apply
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars -auto-approve

# Get instance IP
INSTANCE_IP=$(terraform output -raw instance_external_ip)

echo ""
echo -e "${GREEN}🎉 Infrastructure setup complete!${NC}"
echo -e "${BLUE}Instance Name: $LAB_INFRASTRUCTURE_NAME${NC}"
echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
echo -e "${BLUE}Region: us-central1 (Free Tier)${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Wait 2-3 minutes for instance startup to complete"
echo "2. Deploy any attack lab:"
echo "   cd zero-window/gcp && ./deploy-attack.sh"
echo "   cd slow-incremental/gcp && ./deploy-attack.sh"
echo "   cd adaptive-slow/gcp && ./deploy-attack.sh"
echo ""
echo -e "${BLUE}🌐 Access Methods:${NC}"
echo "• GCP Console → VM instances → SSH button"
echo "• Command line: gcloud compute ssh $LAB_INFRASTRUCTURE_NAME --zone=us-central1-a"
echo "• Web terminal: http://$INSTANCE_IP:8080 (after attack deployment)"
echo ""
echo -e "${YELLOW}💰 Cost Control:${NC}"
echo "• f1-micro instance (Free Tier eligible)"
echo "• Auto-shutdown after 4 hours"
echo "• Cleanup: ./cleanup-infrastructure.sh"
echo ""
echo -e "${GREEN}✅ Infrastructure ready for all HTTP/2 attack labs!${NC}"