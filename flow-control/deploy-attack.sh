#!/bin/bash

# HTTP/2 Flow Control Lab - Unified Attack Deployment
# Deploys attack scripts with built-in health checking

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load GCP configuration if available, otherwise use defaults
if [ -f "gcp.env" ]; then
    echo -e "${BLUE}[INFO]${NC} Loading GCP configuration from gcp.env"
    source gcp.env
    GCP_TARGET_IP="$TARGET_IP"
    INFRASTRUCTURE_NAME="$GCP_VM_NAME"
    ZONE="$GCP_ZONE"
    PROJECT="$GCP_PROJECT_ID"
else
    echo -e "${YELLOW}[WARNING]${NC} gcp.env not found, using hardcoded defaults"
    echo -e "${BLUE}[INFO]${NC} Run './setup-gcp.sh' to create proper configuration"
    GCP_TARGET_IP=""
    INFRASTRUCTURE_NAME="http2-lab-infrastructure"
    ZONE="us-central1-a"
    PROJECT=""
fi

show_help() {
    cat << EOF
HTTP/2 Flow Control Lab - Attack Deployment

Usage: $0 [attack-type] [target] [OPTIONS]

Arguments:
  attack-type        zero-window, slow-incremental, or adaptive-slow
  target             'local', 'gcp', or IP address (gcp uses gcp.env config)

Options:
  --connections N    Number of connections (default: 512)
  --stop             Stop current attack
  --logs             Show attack progress output
  --help, -h         Show this help

Examples:
  $0 zero-window local --connections 512         # Attack local server
  $0 zero-window gcp --connections 1024         # Attack GCP server (auto-detect IP)
  $0 zero-window 35.123.45.67 --connections 512  # Attack specific IP
  $0 zero-window local --stop                    # Stop attack
  $0 zero-window local --logs                    # Show attack logs

Attack Types:
  zero-window        Basic HTTP/2 flow control attack
  slow-incremental   Sustained resource exhaustion attack
  adaptive-slow      Advanced adaptive attack technique

Targets:
  local              Attack locally deployed server (localhost)
  gcp                Attack GCP server using gcp.env configuration
  IP_ADDRESS         Attack remote server at specific IP
EOF
}

validate_attack_type() {
    local attack_type="$1"
    
    if [ ! -d "attacks/$attack_type" ]; then
        echo -e "${RED}❌ Attack type not found: $attack_type${NC}"
        echo "Available attacks: zero-window, slow-incremental, adaptive-slow"
        exit 1
    fi
    
    # Get attack script name based on attack type
    case $attack_type in
        "zero-window")
            ATTACK_SCRIPT="zero_window_attack.py"
            ;;
        "slow-incremental")
            ATTACK_SCRIPT="slow_inc_window_attack.py"
            ;;
        "adaptive-slow")
            ATTACK_SCRIPT="adv_slow_inc_window_attack.py"
            ;;
        *)
            echo -e "${RED}❌ Unknown attack type: $attack_type${NC}"
            exit 1
            ;;
    esac
    
    if [ ! -f "attacks/$attack_type/$ATTACK_SCRIPT" ]; then
        echo -e "${RED}❌ Attack script not found: attacks/$attack_type/$ATTACK_SCRIPT${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Validated attack type: $attack_type${NC}"
}

health_check() {
    local target="$1"
    local attack_type="$2"
    
    echo -e "${GREEN}🏥 Running HTTP/2 server health check...${NC}"
    
    # Determine target URL
    if [ "$target" = "local" ]; then
        TARGET_URL="http://localhost"
    elif [ "$target" = "gcp" ]; then
        if [ -n "$GCP_TARGET_IP" ] && [ "$GCP_TARGET_IP" != "0.0.0.0" ]; then
            TARGET_URL="http://$GCP_TARGET_IP"
            target="$GCP_TARGET_IP"  # Update target for subsequent use
        else
            echo -e "${RED}❌ GCP target IP not found in gcp.env${NC}"
            echo -e "${YELLOW}Run './setup-gcp.sh' to create infrastructure first${NC}"
            exit 1
        fi
    else
        TARGET_URL="http://$target"
    fi
    
    # Basic connectivity check
    echo -n "• Testing connectivity... "
    if ! curl -s --connect-timeout 10 "$TARGET_URL/" >/dev/null 2>&1; then
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}❌ Server not responding at $TARGET_URL${NC}"
        echo "Make sure server is deployed with: ./deploy-server.sh [local|gcp] $attack_type"
        exit 1
    fi
    echo -e "${GREEN}OK${NC}"
    
    # HTTP/2 protocol check
    echo -n "• Testing HTTP/2 support... "
    if ! curl -I --http2 --connect-timeout 10 "$TARGET_URL/" 2>/dev/null | grep -q "HTTP/2"; then
        echo -e "${RED}FAILED${NC}"
        echo -e "${RED}❌ HTTP/2 not enabled on server${NC}"
        echo "Server may still be starting or HTTP/2 module not loaded"
        exit 1
    fi
    echo -e "${GREEN}OK${NC}"
    
    # Response time check
    echo -n "• Testing response time... "
    RESPONSE_TIME=$(curl -w "%{time_total}" -s -o /dev/null --connect-timeout 10 "$TARGET_URL/" 2>/dev/null || echo "999")
    if [ "${RESPONSE_TIME%.*}" -gt 5 ] 2>/dev/null; then
        echo -e "${YELLOW}SLOW (${RESPONSE_TIME}s)${NC}"
        echo -e "${YELLOW}⚠️  Server responding slowly, attack may be less effective${NC}"
    else
        echo -e "${GREEN}OK (${RESPONSE_TIME}s)${NC}"
    fi
    
    echo -e "${GREEN}✅ Server ready for $attack_type attack!${NC}"
    echo ""
}

check_prerequisites() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found. Please install Python 3 first.${NC}"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}❌ curl not found. Please install curl first.${NC}"
        exit 1
    fi
}

deploy_local_attack() {
    local attack_type="$1"
    local connections="$2"
    
    echo -e "${BLUE}🎯 Deploying Local Attack: $attack_type${NC}"
    echo -e "${BLUE}Target: localhost with $connections connections${NC}"
    echo ""
    
    # Check if attack container exists, create if needed
    if ! docker ps -a --format '{{.Names}}' | grep -q "$attack_type-attacker"; then
        echo -e "${GREEN}Creating attack container...${NC}"
        
        # Clean any old containers
        docker rm -f $attack_type-attacker 2>/dev/null || true
        
        # Build attacker image if it doesn't exist
        if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "http2-attacker:latest"; then
            docker build -t http2-attacker:latest -f shared/docker/Dockerfile.attacker shared/docker/
        fi
        
        # Run attack container
        docker run -d --name $attack_type-attacker \
            --network http2-flow-control-lab \
            -v "$(pwd)/attacks/$attack_type:/workspace/attack" \
            -v "$(pwd)/shared:/workspace/shared" \
            -v "$(pwd)/logs:/tmp/logs" \
            -e PYTHONUNBUFFERED=1 \
            http2-attacker:latest \
            tail -f /dev/null
        
        sleep 3
    fi
    
    # Run the attack
    echo -e "${GREEN}🚀 Launching $attack_type attack...${NC}"
    echo -e "${BLUE}Command: python3 /workspace/attack/${ATTACK_SCRIPT} apache-victim --port 80 --connections $connections --verbose${NC}"
    echo ""
    
    docker exec -d $attack_type-attacker \
        python3 /workspace/attack/${ATTACK_SCRIPT} apache-victim --port 80 --connections $connections --verbose
    
    echo -e "${GREEN}✅ Attack launched in background!${NC}"
    echo ""
    echo -e "${BLUE}📊 Monitor with:${NC}"
    echo "• Attack logs: $0 $attack_type local --logs"
    echo "• Server status: ./deploy-server.sh local $attack_type --status"
    echo "• Stop attack: $0 $attack_type local --stop"
}

deploy_remote_attack() {
    local attack_type="$1"
    local target="$2"
    local connections="$3"
    
    echo -e "${BLUE}🎯 Deploying Remote Attack: $attack_type${NC}"
    echo -e "${BLUE}Target: $target with $connections connections${NC}"
    echo -e "${BLUE}Network: Real internet simulation${NC}"
    echo ""
    
    # Create logs directory
    mkdir -p logs
    
    # Kill any existing attack processes
    pkill -f "${ATTACK_SCRIPT}" 2>/dev/null || true
    
    # Determine port based on target
    if [ "$target" = "localhost" ] || [ "$target" = "127.0.0.1" ]; then
        TARGET_PORT="80"
    else
        TARGET_PORT="80"
    fi
    
    # Run the attack in background
    echo -e "${GREEN}🚀 Launching $attack_type attack over internet...${NC}"
    echo -e "${BLUE}Command: python3 attacks/$attack_type/${ATTACK_SCRIPT} $target --port $TARGET_PORT --connections $connections --verbose${NC}"
    echo ""
    
    nohup python3 attacks/$attack_type/${ATTACK_SCRIPT} $target --port $TARGET_PORT --connections $connections --verbose \
        > logs/${attack_type}-attack.log 2>&1 &
    
    ATTACK_PID=$!
    echo "$ATTACK_PID" > logs/${attack_type}-attack.pid
    
    echo -e "${GREEN}✅ Attack launched (PID: $ATTACK_PID)!${NC}"
    echo ""
    echo -e "${BLUE}📊 Monitor with:${NC}"
    echo "• Attack logs: $0 $attack_type $target --logs"
    echo "• Live logs: tail -f logs/${attack_type}-attack.log"
    echo "• Stop attack: $0 $attack_type $target --stop"
}

stop_attack() {
    local attack_type="$1"
    local target="$2"
    
    if [ "$target" = "local" ]; then
        echo -e "${YELLOW}Stopping local attack...${NC}"
        docker exec $attack_type-attacker pkill -f "${ATTACK_SCRIPT}" 2>/dev/null || true
        docker stop $attack_type-attacker 2>/dev/null || true
        docker rm $attack_type-attacker 2>/dev/null || true
        echo -e "${GREEN}✅ Local attack stopped${NC}"
    else
        echo -e "${YELLOW}Stopping remote attack...${NC}"
        if [ -f "logs/${attack_type}-attack.pid" ]; then
            ATTACK_PID=$(cat logs/${attack_type}-attack.pid)
            kill $ATTACK_PID 2>/dev/null || true
            rm -f logs/${attack_type}-attack.pid
            echo -e "${GREEN}✅ Remote attack stopped (PID: $ATTACK_PID)${NC}"
        else
            pkill -f "${ATTACK_SCRIPT}" 2>/dev/null || true
            echo -e "${GREEN}✅ Attack processes stopped${NC}"
        fi
    fi
}

show_logs() {
    local attack_type="$1"
    local target="$2"
    
    if [ "$target" = "local" ]; then
        if docker ps --format '{{.Names}}' | grep -q "$attack_type-attacker"; then
            echo -e "${BLUE}Local Attack Logs (last 50 lines):${NC}"
            docker logs --tail=50 -f $attack_type-attacker
        else
            echo -e "${YELLOW}⚠️  No local attack container running${NC}"
        fi
    else
        if [ -f "logs/${attack_type}-attack.log" ]; then
            echo -e "${BLUE}Remote Attack Logs (last 50 lines):${NC}"
            tail -f -n 50 logs/${attack_type}-attack.log
        else
            echo -e "${YELLOW}⚠️  No attack log file found${NC}"
            echo "Attack may not be running or haven't started yet"
        fi
    fi
}

# Main execution
if [ $# -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    show_help
    exit 0
fi

ATTACK_TYPE="$1"
TARGET="$2"
shift 2

# Validate attack type
if [ "$ATTACK_TYPE" != "zero-window" ] && [ "$ATTACK_TYPE" != "slow-incremental" ] && [ "$ATTACK_TYPE" != "adaptive-slow" ]; then
    echo -e "${RED}❌ Invalid attack type: $ATTACK_TYPE${NC}"
    echo "Must be: zero-window, slow-incremental, or adaptive-slow"
    show_help
    exit 1
fi

# Parse options
CONNECTIONS="512"  # default
STOP=false
SHOW_LOGS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --connections)
            CONNECTIONS="$2"
            shift 2
            ;;
        --stop)
            STOP=true
            shift
            ;;
        --logs)
            SHOW_LOGS=true
            shift
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate target
if [ -z "$TARGET" ]; then
    echo -e "${RED}❌ Target required${NC}"
    show_help
    exit 1
fi

if [ "$TARGET" != "local" ] && [ "$TARGET" != "gcp" ] && ! echo "$TARGET" | grep -E '^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$' >/dev/null; then
    echo -e "${RED}❌ Invalid target: $TARGET${NC}"
    echo "Must be 'local', 'gcp', or an IP address (e.g., 35.123.45.67)"
    exit 1
fi

# Handle stop action
if [ "$STOP" = true ]; then
    stop_attack "$ATTACK_TYPE" "$TARGET"
    exit 0
fi

# Handle logs action
if [ "$SHOW_LOGS" = true ]; then
    show_logs "$ATTACK_TYPE" "$TARGET"
    exit 0
fi

# Check prerequisites
check_prerequisites

# Validate attack type and get script name
validate_attack_type "$ATTACK_TYPE"

# Validate connections parameter
if ! [[ "$CONNECTIONS" =~ ^[0-9]+$ ]] || [ "$CONNECTIONS" -lt 1 ] || [ "$CONNECTIONS" -gt 10000 ]; then
    echo -e "${RED}❌ Invalid connections count: $CONNECTIONS${NC}"
    echo "Must be a number between 1 and 10000"
    exit 1
fi

# Run health check before attack
health_check "$TARGET" "$ATTACK_TYPE"

# Deploy attack
if [ "$TARGET" = "local" ]; then
    deploy_local_attack "$ATTACK_TYPE" "$CONNECTIONS"
else
    deploy_remote_attack "$ATTACK_TYPE" "$TARGET" "$CONNECTIONS"
fi