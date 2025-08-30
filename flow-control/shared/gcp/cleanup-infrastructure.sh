#!/bin/bash

# GCP Infrastructure Cleanup
# Destroys the reusable HTTP/2 lab infrastructure

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

INFRASTRUCTURE_NAME="http2-lab-infrastructure"

echo -e "${RED}🗑️  HTTP/2 Lab Infrastructure Cleanup${NC}"
echo -e "${YELLOW}⚠️  This will destroy all lab infrastructure and data${NC}"
echo ""

# Check if infrastructure exists
if ! gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$INFRASTRUCTURE_NAME"; then
    echo -e "${YELLOW}⚠️  No infrastructure found to cleanup${NC}"
    echo "Infrastructure '$INFRASTRUCTURE_NAME' does not exist"
    exit 0
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No GCP project set${NC}"
    exit 1
fi

echo -e "${BLUE}Project: $PROJECT_ID${NC}"
echo -e "${BLUE}Infrastructure: $INFRASTRUCTURE_NAME${NC}"

# Confirm destruction
read -p "Are you sure you want to destroy the infrastructure? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    echo -e "${YELLOW}Cleanup cancelled${NC}"
    exit 0
fi

echo -e "${RED}Destroying infrastructure...${NC}"

# Use terraform to destroy if available
if [ -f "terraform.tfstate" ] && command -v terraform &> /dev/null; then
    echo -e "${GREEN}Using Terraform to destroy infrastructure...${NC}"
    terraform destroy -var="project_id=$PROJECT_ID" -var="infrastructure_name=$INFRASTRUCTURE_NAME" -auto-approve
else
    echo -e "${GREEN}Using gcloud to destroy infrastructure...${NC}"
    
    # Delete instance
    gcloud compute instances delete $INFRASTRUCTURE_NAME --zone=us-central1-a --quiet || true
    
    # Delete firewall rule
    gcloud compute firewall-rules delete "${INFRASTRUCTURE_NAME}-firewall" --quiet || true
fi

# Verify cleanup
echo -e "${GREEN}Verifying cleanup...${NC}"
REMAINING=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(name)")
if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}⚠️  Some resources may still exist:${NC}"
    echo "$REMAINING"
else
    echo -e "${GREEN}✅ All infrastructure cleaned up successfully${NC}"
fi

# Clean up local terraform files
if [ -f "terraform.tfstate" ]; then
    rm -f terraform.tfstate terraform.tfstate.backup terraform.tfvars
    echo -e "${GREEN}✅ Local terraform files cleaned up${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Cleanup complete!${NC}"
echo "You can now run './setup-infrastructure.sh' to create fresh infrastructure"