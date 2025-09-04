# HTTP/2 Flood Attack Lab

## 📋 Overview

The HTTP/2 Flood Attack Lab is a comprehensive educational laboratory exercise designed to explore Distributed Denial of Service (DDoS) attacks that exploit HTTP/2 multiplexing capabilities. This lab implements **clean separation** between server deployment and attack deployment, enabling realistic testing scenarios including local-to-cloud attacks.

**Focus**: Understanding HTTP/2 vulnerabilities through practical experimentation.

## 🏗️ Architecture

### Network Architecture

#### Local Setup
```
┌─────────────────┐    ┌─────────────────┐
│ Attack Container│◄──►│Server Container │
│ (http2-flood)   │    │ (HTTP/2 Server) │
└─────────────────┘    └─────────────────┘
     Bridge Network        Port 8080
```

#### Cloud Setup
```
┌─────────────────┐    Internet    ┌─────────────────┐
│ Local Attack    │◄──────────────►│ GCP VM          │
│ Container       │                │ ┌─────────────┐ │
└─────────────────┘                │ │HTTP/2       │ │
                                   │ │Container    │ │
                                   │ └─────────────┘ │
                                   └─────────────────┘
```

### Clean Separation Design
- **`deploy-server.sh`**: Deploy victim servers (local or GCP)
- **`deploy-attack.sh`**: Launch attacks against running servers
- **Independent operation**: Servers run without attacks, attacks target existing servers
- **Real internet simulation**: Attack from local machine → GCP servers

## 🎯 Lab Objectives

### Primary Learning Goals
1. **Attack Vector Understanding** - Comprehend HTTP/2 basic and high level flood attack mechanisms
2. **Performance Measurement** - Quantify attack effectiveness and system degradation  
3. **Cloud vs Local Comparison** - Evaluate performance differences between deployments
4. **Separation of Concerns** - Understand independent server and attack operations

### Lab Parts
- **Part A**: Single-worker HTTP/2 server (development environment)
- **Part B**: Multi-worker HTTP/2 server (production-like environment)

## 🚀 Quick Start

### Step 1: Local Testing
```bash
# Clone repository
git clone https://github.com/OhadLibai/DDoS-SEED-Lab.git
git checkout http2
cd DDoS-SEED-Lab/http2-app-flood

# Deploy local server
./deploy-server.sh --local part-A

# Attack local server (from separate terminal)
./deploy-attack.sh --local part-A
```

### Step 2: GCP Testing (Real Internet)

#### Prerequisites
1. **Create GCP Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Click "Create Project" 
   - Enter project name (e.g., "http2-flood-lab")
   - **Note your PROJECT_ID** (auto-generated, looks like "http2-flood-lab-123456")

2. **No Billing Required**
   - This lab uses GCP Free Tier resources only (f1-micro VM)
   - No credit card or billing setup needed

3. **Install Google Cloud SDK**
   ```bash
   # Download and install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud auth login
   ```

#### Setup GCP Infrastructure (One-Time)
```bash
# Run complete GCP setup (replaces manual VM creation)
./gcp-setup-infrastructure.sh YOUR_PROJECT_ID

# Example:
./gcp-setup-infrastructure.sh http2-flood-lab-123456
```

#### Deploy and Test
```bash
# Deploy server on GCP
./deploy-server.sh --gcp part-A

# Attack GCP server from local machine (real internet!)
./deploy-attack.sh --gcp part-A
```

## 📚 Deployment Reference

### Server Deployment
```bash
./deploy-server.sh --local|--gcp <part-A|part-B|--stop> [options]
```

**Examples:**
```bash
# Local servers
./deploy-server.sh --local part-A           # Single-worker server
./deploy-server.sh --local part-B           # Multi-worker server
./deploy-server.sh --local --stop           # Stop servers

# GCP servers
./deploy-server.sh --gcp part-A             # Single-worker on GCP
./deploy-server.sh --gcp part-B             # Multi-worker on GCP
./deploy-server.sh --gcp --stop             # Stop containers + shutdown VM instance
./deploy-server.sh --gcp --destruct-vm      # REMOVE entire cloud infrastructure
```

### Attack Deployment
```bash
./deploy-attack.sh --local|--gcp <part-A|part-B|--stop> [options]
```

**Examples:**
```bash
# Local attacks (to local servers)
./deploy-attack.sh --local part-A           # Attack local single-worker
./deploy-attack.sh --local --stop           # Stop attacks

# GCP attacks (from local to GCP servers - real internet simulation)
./deploy-attack.sh --gcp part-A             # Attack GCP server from local
./deploy-attack.sh --gcp part-B             # Attack GCP multi-worker
./deploy-attack.sh --gcp --stop             # Stop GCP attacks
```

### Environment Variables
| Variable | Default | Values | Description |
|----------|---------|--------|-------------|
| `SCENARIO` | `default_scenario` | `captcha`, `crypto`, `gaming`, `antibot`, `webservice`, `content_preview` | CPU workload type |
| `WORKLOAD` | `5` | `1-5` | CPU workload intensity |
| `CONNECTIONS` | `4` (part-A), `8` (part-B) | Any number | Attack connections |
| `STREAMS` | `256` | Any number | Streams per connection |
| `ATTACK` | `basic` | `basic`, `advanced` | Attack script type |

**Examples:**
```bash
# Custom scenarios and workloads
SCENARIO=captcha WORKLOAD=3 ./deploy-server.sh --local part-A
CONNECTIONS=16 STREAMS=512 ./deploy-attack.sh --gcp part-B
ATTACK=advanced ./deploy-attack.sh --local part-B
```

## 🔧 CPU Workload Scenarios

The lab supports multiple CPU-intensive scenarios that simulate real-world server operations:

| Scenario | Description | Use Case |
|----------|-------------|----------|
| `default_scenario` | Simple CPU calculations | Baseline CPU workload |
| `captcha` | Visual/audio CAPTCHA generation | Bot protection systems |
| `crypto` | Cryptographic operations | SSL/TLS handshakes |
| `gaming` | Sudoku/maze generation | Game server content |
| `antibot` | Anti-automation challenges | Rate limiting systems |
| `webservice` | Map tiles/routing | Real-world web services |
| `content_preview` | Search/preview generation | Content management |

**For detailed scenario documentation, see [victims/scenarios/README_scenarios.md](victims/scenarios/README_scenarios.md)**

## 📊 Live Monitoring and Testing

### Essential Monitoring Commands

#### Response Time Monitoring
```bash
# Local deployment
watch -n 1 'curl -w "Response: %{time_total}s\n" -o /dev/null -s http://localhost:8080'

# GCP deployment (replace EXTERNAL_IP)
watch -n 1 'curl -w "Response: %{time_total}s\n" -o /dev/null -s http://EXTERNAL_IP:8080'
```

#### Resource Usage Monitoring
```bash
# Local
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# GCP
gcloud compute ssh http2-flood-lab --zone=us-central1-a --command="docker stats --no-stream"
```

#### Bandwidth Consumption
```bash
# Monitor network I/O (bytes per second)
docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"

# Track bandwidth usage over time
watch -n 5 'docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"'

# GCP bandwidth monitoring
gcloud compute ssh http2-flood-lab --zone=us-central1-a --command="docker stats --no-stream --format 'table {{.Name}}\t{{.NetIO}}'"
```

#### Request Rate
```bash
# Monitor HTTP/2 requests per second
docker logs -f http2-flood-*-attack | grep -c "request" &
sleep 10; kill $!

# Count active HTTP/2 streams
docker exec dev-victim-server sh -c "netstat -an | grep :8080 | grep ESTABLISHED | wc -l"

# Monitor request patterns
docker logs http2-flood-*-attack | grep -E "(stream|request)" | tail -20
```

#### Error Rates
```bash
# Monitor HTTP error responses
docker logs dev-victim-server | grep -E "(40[0-9]|50[0-9])" | tail -20
docker logs prod-victim-server | grep -E "(40[0-9]|50[0-9])" | tail -20

# Real-time error monitoring
docker logs -f dev-victim-server | grep --line-buffered -E "(ERROR|WARN)"

# HTTP/2 specific errors
docker logs -f dev-victim-server | grep --line-buffered -i "http2"
```

#### Thread Pool Depletion
```bash
# Check server thread status
docker exec dev-victim-server sh -c "ps aux | grep python | wc -l"
docker exec prod-victim-server sh -c "ps aux | grep python | wc -l"

# Monitor worker processes
docker exec dev-victim-server sh -c "pgrep -f 'python.*server' | wc -l"

# Check uvicorn workers (for production)
docker exec prod-victim-server sh -c "ps aux | grep uvicorn"
```

#### Latency Spikes
```bash
# Monitor latency distribution
for i in {1..10}; do curl -w "%{time_total}s\n" -o /dev/null -s http://localhost:8080; done

# Detect latency anomalies
bash -c 'baseline=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080 2>/dev/null); echo "Baseline: ${baseline}s"; while true; do current=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080 2>/dev/null); if (( $(echo "$current > $baseline * 3" | bc -l) )); then echo "SPIKE: ${current}s ($(date))"; fi; sleep 1; done'

# HTTP/2 specific latency monitoring
curl --http2-prior-knowledge -w "H2-Time:%{time_total}s\n" -o /dev/null -s http://localhost:8080
```

#### Stream Status
```bash
# Monitor HTTP/2 stream multiplexing
docker logs dev-victim-server | grep -E "(stream|multiplex)" | tail -10

# Track concurrent streams
docker exec dev-victim-server sh -c "netstat -an | grep ':8080.*ESTABLISHED' | wc -l"

# Monitor HTTP/2 connection reuse
docker logs -f dev-victim-server | grep --line-buffered -E "(connection.*reuse|stream.*[0-9]+)"
```

#### Average Connection Duration
```bash
# Monitor connection lifetimes
docker exec dev-victim-server sh -c "ss -o | grep :8080 | awk '{print \$6}' | grep -o 'timer:[^,]*'"
docker exec prod-victim-server sh -c "ss -o | grep :8080 | awk '{print \$6}' | grep -o 'timer:[^,]*'"

# Track HTTP/2 persistent connections
docker logs dev-victim-server | grep -E "(connection.*establish|connection.*close)" | tail -10

# Monitor connection pool statistics
docker logs -f dev-victim-server | grep --line-buffered -E "(pool|connection.*duration)"
```

#### Service Availability Testing
```bash
# Health check
curl --http2-prior-knowledge http://localhost:8080/health        # Local
curl --http2-prior-knowledge http://EXTERNAL_IP:8080/health      # GCP

# Performance test
curl -w "Time:%{time_total}s Code:%{http_code}\n" http://localhost:8080
```

#### Connection Monitoring
```bash
# Active connections (host level)
watch -n 1 'ss -tan | grep :8080 | wc -l'

# Container-level connections
# Local part-A:
docker exec dev-victim-server sh -c "awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp"

# Local part-B:
docker exec prod-victim-server sh -c "awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp"

# GCP monitoring (check which container is running first with 'docker ps'):
gcloud compute ssh http2-flood-lab --zone=us-central1-a --command="docker exec \$(docker ps --format '{{.Names}}' | grep victim) sh -c \"awk 'NR>1 && \\\$4==\\\"01\\\" {count++} END {print count+0}' /proc/net/tcp\""
```

## 🧪 Testing Scenarios

### Scenario 1: Local Development Testing
```bash
# 1. Deploy local single-worker server
./deploy-server.sh --local part-A

# 2. Basic attack
./deploy-attack.sh --local part-A

# 3. Monitor response degradation
curl -w "Time:%{time_total}s\n" http://localhost:8080

# 4. Stop and switch to multi-worker
./deploy-server.sh --local --stop
./deploy-server.sh --local part-B
./deploy-attack.sh --local part-B
```

### Scenario 2: Real Internet Attack Simulation
```bash
# 1. Setup GCP infrastructure (one-time)
./gcp-setup-infrastructure.sh your-project-id

# 2. Deploy server on GCP
./deploy-server.sh --gcp part-A

# 3. Attack from local machine over real internet
./deploy-attack.sh --gcp part-A

# 4. Compare response times
curl -w "Time:%{time_total}s\n" http://EXTERNAL_IP:8080
```

### Scenario 3: Advanced Attack Testing
```bash
# 1. Deploy production-like server
./deploy-server.sh --gcp part-B

# 2. Advanced evasion attack
ATTACK=advanced CONNECTIONS=16 ./deploy-attack.sh --gcp part-B

# 3. Monitor server resilience
gcloud compute ssh http2-flood-lab --zone=us-central1-a --command="docker stats"
```

## 🔧 Troubleshooting

### Common Issues

**"Server health check failed"**:
```bash
# Check if server is running
docker ps
# or for GCP:
gcloud compute ssh http2-flood-lab --zone=us-central1-a --command="docker ps"

# Check server logs (use actual container name from 'docker ps')
docker logs dev-victim-server    # for part-A
docker logs prod-victim-server   # for part-B
```

**"Port 8080 in use"**:
```bash
# Stop existing servers
./deploy-server.sh --local --stop

# Check what's using the port
ss -tuln | grep :8080
```

**"Docker permission errors"**:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**"GCP VM not accessible"**:
```bash
# Check VM status
gcloud compute instances describe http2-flood-lab --zone=us-central1-a --format='get(status)'

# Start VM if stopped
gcloud compute instances start http2-flood-lab --zone=us-central1-a
```

**"Attack not effective"**:
- Increase WORKLOAD level: `WORKLOAD=5`
- Increase connections: `CONNECTIONS=32`
- Use advanced attack: `ATTACK=advanced`
- Check container resource limits

### GCP Cost Management

**VM Auto-Shutdown**: VMs automatically shutdown after 2 hours to prevent unexpected charges.

**Manual Control**:
```bash
# Stop everything and shutdown VM
./deploy-server.sh --gcp --destruct-vm

# Restart when needed
gcloud compute instances start http2-flood-lab --zone=us-central1-a
```

## 🧹 Cleanup

### GCP Cleanup
```bash
# Stop everything but keep VM
./deploy-server.sh --gcp --stop
./deploy-attack.sh --gcp --stop

# REMOVE entire cloud infrastructure (requires re-running gcp-setup-infrastructure.sh)
./deploy-server.sh --gcp --destruct-vm

# Manual infrastructure deletion (same as --destruct-vm)
gcloud compute instances delete http2-flood-lab --zone=us-central1-a
gcloud compute firewall-rules delete allow-http2-lab
```

## ⚙️ Prerequisites

### System Requirements
- **Docker** and **Docker Compose** installed
- Available port 8080 on your system
- **Google Cloud Platform** account (free tier, no billing required)
- 4GB+ RAM recommended for local testing

### Knowledge Prerequisites
- Basic understanding of HTTP/1.1 and HTTP/2 protocols
- Familiarity with client-server architecture and async processing
- Elementary networking concepts (TCP connections, multiplexing)
