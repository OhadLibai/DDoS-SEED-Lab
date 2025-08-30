#!/bin/bash

# slow-incremental Attack Deployment
# Deploys Slow Incremental attack to existing GCP infrastructure

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

LAB_NAME="slow-incremental"
APACHE_VERSION="2.4.62"
ATTACK_SCRIPT="slow_inc_window_attack.py"
DEFAULT_CONNECTIONS="512"
INFRASTRUCTURE_NAME="http2-lab-infrastructure"

echo -e "${BLUE}🎯 Deploying slow-incremental Attack${NC}"
echo -e "${BLUE}Target: Apache $APACHE_VERSION with $DEFAULT_CONNECTIONS connections${NC}"
echo ""

# Check if infrastructure exists
if ! gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(name)" | grep -q "$INFRASTRUCTURE_NAME"; then
    echo -e "${RED}❌ Infrastructure not found!${NC}"
    echo "First run: cd ../../shared/gcp && ./setup-infrastructure.sh"
    exit 1
fi

# Get instance info
INSTANCE_IP=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(EXTERNAL_IP)")
INSTANCE_ZONE=$(gcloud compute instances list --filter="name:$INFRASTRUCTURE_NAME" --format="value(ZONE)" | cut -d'/' -f4)

echo -e "${GREEN}✅ Found infrastructure: $INFRASTRUCTURE_NAME${NC}"
echo -e "${BLUE}Instance IP: $INSTANCE_IP${NC}"
echo -e "${BLUE}Zone: $INSTANCE_ZONE${NC}"
echo ""

# Copy attack script to instance
echo -e "${GREEN}Copying attack script to instance...${NC}"
gcloud compute scp ../../shared/scripts/$ATTACK_SCRIPT ubuntu@$INFRASTRUCTURE_NAME:/opt/http2-labs/shared/scripts/ --zone=$INSTANCE_ZONE --quiet

# Deploy the lab on the instance
echo -e "${GREEN}Deploying Slow Incremental attack lab...${NC}"
gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE --quiet --command="
    /opt/http2-labs/shared/deploy-lab.sh '$LAB_NAME' '$APACHE_VERSION' '$ATTACK_SCRIPT' '$DEFAULT_CONNECTIONS'
"

echo ""
echo -e "${GREEN}🎉 slow-incremental deployed successfully!${NC}"
echo ""
echo -e "${BLUE}🌐 Access Options:${NC}"
echo "• Web Terminal: http://$INSTANCE_IP:8080"
echo "• Apache Target: http://$INSTANCE_IP"
echo "• SSH: gcloud compute ssh ubuntu@$INFRASTRUCTURE_NAME --zone=$INSTANCE_ZONE"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "• Live monitor: ssh to instance → /opt/http2-labs/shared/monitor.sh"
echo "• Attack logs: ssh to instance → tail -f /opt/http2-labs/shared/logs/$LAB_NAME-attack.log"
echo ""
echo -e "${BLUE}🔄 Switch Labs:${NC}"
echo "• cd ../../zero-window/gcp && ./deploy-attack.sh"
echo "• cd ../../adaptive-slow/gcp && ./deploy-attack.sh"
echo ""
echo -e "${GREEN}⚡ Attack should be running automatically!${NC}"
echo "Check web terminal or SSH to see live results"