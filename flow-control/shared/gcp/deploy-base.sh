#!/bin/bash
# Shared GCP Deployment Script for HTTP/2 Labs
# Used by all labs with lab-specific parameters

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Parameters passed from lab-specific deploy.sh
LAB_NAME="$1"
APACHE_VERSION="$2"
ATTACK_SCRIPT="$3"
DEFAULT_CONNECTIONS="$4"

if [ -z "$LAB_NAME" ]; then
    echo -e "${RED}❌ Usage: $0 LAB_NAME APACHE_VERSION ATTACK_SCRIPT DEFAULT_CONNECTIONS${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 $LAB_NAME GCP Deployment${NC}"
echo -e "${BLUE}Target: Apache $APACHE_VERSION on f1-micro (FREE TIER)${NC}"
echo ""

# Check prerequisites
if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ Terraform not found. Please install terraform first.${NC}"
    exit 1
fi

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud not found. Please install Google Cloud CLI first.${NC}"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Not authenticated with gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ No project set. Run: gcloud config set project YOUR_PROJECT_ID${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Using project: $PROJECT_ID${NC}"

# Initialize Terraform (using shared base)
echo -e "${GREEN}Initializing Terraform...${NC}"
terraform init

# Plan deployment
echo -e "${GREEN}Planning deployment...${NC}"
terraform plan \
  -var="project_id=$PROJECT_ID" \
  -var="lab_name=$LAB_NAME" \
  -var="apache_version=$APACHE_VERSION" \
  -var="attack_script=$ATTACK_SCRIPT" \
  -var="default_connections=$DEFAULT_CONNECTIONS"

# Deploy
echo -e "${GREEN}Deploying infrastructure...${NC}"
terraform apply \
  -var="project_id=$PROJECT_ID" \
  -var="lab_name=$LAB_NAME" \
  -var="apache_version=$APACHE_VERSION" \
  -var="attack_script=$ATTACK_SCRIPT" \
  -var="default_connections=$DEFAULT_CONNECTIONS" \
  -auto-approve

# Get outputs
INSTANCE_IP=$(terraform output -raw instance_ip)
echo ""
echo -e "${GREEN}🎉 Infrastructure deployed!${NC}"
echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
echo -e "${BLUE}Victim Server: http://$INSTANCE_IP${NC}"
echo ""

# Wait for instance to be ready
echo -e "${GREEN}Waiting for instance to boot and become accessible...${NC}"
for i in {1..60}; do
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no ubuntu@$INSTANCE_IP "echo 'Instance ready'" >/dev/null 2>&1; then
        break
    fi
    echo -n "."
    sleep 5
done
echo ""

if [ $i -eq 60 ]; then
    echo -e "${RED}❌ Instance failed to become accessible. Check firewall rules and try again.${NC}"
    exit 1
fi

echo -e "${GREEN}Instance is accessible! Waiting for startup script to complete...${NC}"
sleep 60  # Give startup script time to complete

# Automatically copy attack scripts
echo -e "${GREEN}Copying attack scripts to instance...${NC}"
scp -o StrictHostKeyChecking=no ../../shared/scripts/*.py ubuntu@$INSTANCE_IP:/opt/$LAB_NAME/ || {
    echo -e "${RED}❌ Failed to copy scripts. Manual copy required:${NC}"
    echo "scp ../../shared/scripts/*.py ubuntu@$INSTANCE_IP:/opt/$LAB_NAME/"
    exit 1
}

echo -e "${GREEN}✅ Lab deployment complete and ready to use!${NC}"
echo ""
echo -e "${BLUE}🎯 Run Attack:${NC}"
echo "ssh ubuntu@$INSTANCE_IP"
echo "python3 /opt/$LAB_NAME/$ATTACK_SCRIPT localhost --port 80 --connections $DEFAULT_CONNECTIONS --verbose"
echo ""
echo -e "${BLUE}📊 Monitor:${NC}"
echo "ssh ubuntu@$INSTANCE_IP"  
echo "/opt/$LAB_NAME/monitor.sh"
echo ""
echo -e "${RED}⚠️  Instance will auto-shutdown in 2 hours for cost control${NC}"
echo -e "${RED}💰 Cleanup: terraform destroy -var=\"project_id=$PROJECT_ID\" -var=\"lab_name=$LAB_NAME\" -auto-approve${NC}"