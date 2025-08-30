#!/bin/bash

# zero-window Local Setup
# Simple script to run HTTP/2 Zero Window Attack locally

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎯 zero-window: HTTP/2 Zero Window Attack (Local)${NC}"
echo -e "${BLUE}Target: Apache 2.4.55${NC}"
echo ""

# Clean start
echo -e "${GREEN}Starting lab environment...${NC}"
docker-compose down 2>/dev/null || true
mkdir -p logs

# Start environment
docker-compose up -d --build

# Wait for Apache to be ready
echo -e "${GREEN}Waiting for Apache to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost/ >/dev/null 2>&1; then
        break
    fi
    sleep 2
done

echo -e "${GREEN}✅ Lab environment ready!${NC}"
echo ""
echo -e "${BLUE}Apache victim server: http://localhost${NC}"
echo -e "${BLUE}Attack script: ../../zero_window_attack.py${NC}"
echo ""
echo -e "${GREEN}Quick start commands:${NC}"
echo "# Run attack (in new terminal):"
echo "docker exec zero-window-attacker python3 /workspace/shared/scripts/zero_window_attack.py apache-victim --port 80 --connections 512 --verbose"
echo ""
echo "# Monitor (in another terminal):"
echo "docker stats --no-stream"
echo ""
echo -e "${GREEN}📖 See README.md for complete monitoring commands${NC}"