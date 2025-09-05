# HTTP/2 Flow Control Attack Lab

## Overview

This lab explores HTTP/2 flow control vulnerabilities through three distinct attack types. Each attack demonstrates different exploitation techniques using a unified deployment architecture.

**Focus**: Learn HTTP/2 protocol vulnerabilities through hands-on attack experimentation comparing local controlled environments vs. real internet conditions.

## Network Architecture

### Local Setup
```
┌─────────────────┐    ┌─────────────────┐
│ Attack Container│◄──►│Server Container │
│ (http2-attacker)│    │ (Apache)        │
└─────────────────┘    └─────────────────┘
     Bridge Network        Port 80
```

### GCP Setup
```
┌─────────────────┐    Internet    ┌─────────────────┐
│ Local Attack    │◄──────────────►│ GCP VM          │
│ Container       │                │ ┌─────────────┐ │
└─────────────────┘                │ │Apache       │ │
                                   │ │Container    │ │
                                   │ └─────────────┘ │
                                   └─────────────────┘
```


## 🚀 Quick Start

### Prerequisites
- **Local**: Docker, Docker Compose, Python 3, curl
- **GCP**: Google Cloud CLI, GCP project (free tier)

### Attack Types

| Attack | Apache Version | Learning Focus |
|--------|---------------|----------------|
| **Zero-Window** | 2.4.55 | Basic HTTP/2 flow control exploitation |
| **Slow-Incremental** | 2.4.62 | Sustained resource exhaustion patterns |
| **Adaptive-Slow** | 2.4.62 | Advanced intelligent attack adaptation |

### Attack Techniques Explained

**Zero-Window Attack:**
- **Mechanism**: Sets INITIAL_WINDOW_SIZE=0 in HTTP/2 SETTINGS frame
- **Impact**: Forces server to hold worker threads indefinitely
- **Learning**: Basic HTTP/2 flow control exploitation

**Slow-Incremental Attack:**  
- **Mechanism**: Sends minimal WINDOW_UPDATE increments
- **Impact**: Artificially limits server transmission speed
- **Learning**: Resource exhaustion through protocol abuse

**Adaptive-Slow Attack:**
- **Mechanism**: Dynamically adjusts timing based on server responses
- **Impact**: Optimized resource exhaustion with evasion
- **Learning**: Advanced attack intelligence and adaptation to overcome cloud infrastructure
  
## 🖥️ Local Lab Testing

**Deploy and attack servers locally:**

```bash
#SSH to the created VM and clone the repo.


# Deploy Apache server
./deploy-server.sh local zero-window

# Launch attack (new terminal)
./deploy-attack.sh zero-window local --connections 512

# Monitor attack progress
./deploy-attack.sh zero-window local --logs

# Stop attack
./deploy-attack.sh zero-window local --stop
```

**Example Complete Workflow:**
Set the project to gcloud.

```bash
# Deploy zero-window server locally
./deploy-server.sh local zero-window

# Launch attack with 1024 connections  
./deploy-attack.sh zero-window local --connections 1024

# Monitor in real-time
./deploy-attack.sh zero-window local --logs

# Check server status
./deploy-server.sh local zero-window --status

# Stop everything
./deploy-attack.sh zero-window local --stop
./deploy-server.sh local zero-window --stop
```

## 🌐 GCP Free Tier Lab (Real Internet Testing)

### One-Time Setup

**1. Create GCP Project:**
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Sign in with Google account → Click "Create Project"
- Enter name like "HTTP2-Lab" → Note the **Project ID**

**2. Setup Infrastructure:**
```bash
# In Cloud Shell or local with gcloud CLI:
gcloud config set project YOUR_PROJECT_ID

# Clone lab (if needed)
git clone https://github.com/your-repo/DDoS-SEED-Lab.git
cd DDoS-SEED-Lab/flow-control

# Create GCP infrastructure (one-time setup)
./setup-gcp.sh
```

### Real Internet Attack Testing

**Deploy server on GCP, attack from local machine:**

```bash
# Deploy Apache server to GCP
./deploy-server.sh gcp zero-window

# You will revieve the IP of the server to attack along with a command to run

# Attack from local machine over internet
./deploy-attack.sh zero-window 35.123.45.67 --connections 512

# Monitor attack progress
./deploy-attack.sh zero-window 35.123.45.67 --logs

# NOTE: if h2 causes import issues use sudo apt install python3-h2

# Stop attack
./deploy-attack.sh zero-window 35.123.45.67 --stop
```

**Complete Real Internet Workflow:**
```bash
# Setup (one-time)
./setup-gcp.sh

# Deploy server on GCP
./deploy-server.sh gcp slow-incremental

# Attack from local over real internet
./deploy-attack.sh slow-incremental 35.123.45.67 --connections 256

# Compare with local testing
./deploy-server.sh local slow-incremental  
./deploy-attack.sh slow-incremental local --connections 256
```

### Infrastructure Management

```bash
# Stop GCP server (restartable)
./deploy-server.sh gcp zero-window --stop

# Completely destroy infrastructure
./deploy-server.sh gcp zero-window --destruct-vm

# Check server status/logs
./deploy-server.sh gcp zero-window --status
./deploy-server.sh gcp zero-window --logs
```

## 📝 Monitoring & Analysis

### Built-in Monitoring Commands

**Server Status:**
```bash
# Check server health and resource usage
./deploy-server.sh local zero-window --status
./deploy-server.sh gcp zero-window --status

# View server logs
./deploy-server.sh local zero-window --logs
./deploy-server.sh gcp zero-window --logs
```

**Attack Progress:**
```bash
# Monitor attack in real-time
./deploy-attack.sh zero-window local --logs
./deploy-attack.sh zero-window 35.123.45.67 --logs
```

### Manual Monitoring 

**Response Time Testing:**
```bash
# Local server response time
curl -w "Response: %{time_total}s\n" -s -o /dev/null http://localhost/

# GCP server response time (with internet latency)
curl -w "Response: %{time_total}s\n" -s -o /dev/null http://35.123.45.67/
```

**Connection Analysis:**
```bash
# Active HTTP connections (port 80)
ss -tuln | grep ':80' | wc -l

# Connection state breakdown
ss -tuln | grep ':80' | awk '{print $1}' | sort | uniq -c

# Continuous monitoring
watch -n 5 "ss -tuln | grep ':80' | wc -l"
```

**Resource Usage:**
```bash
# Docker container resources (local)
docker stats --no-stream

# System resources (GCP)
# SSH to instance: gcloud compute ssh http2-lab-infrastructure --zone=us-central1-a
htop
```

**Bandwidth Consumption:**
```bash
# Monitor network I/O (bytes per second)
docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"

# Track bandwidth usage over time
watch -n 5 'docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"'
```

**Request Rate:**
```bash
# Monitor HTTP/2 flow control requests per second
docker logs http2-attacker-* | grep -E "(request|window)" | wc -l

# Count active HTTP/2 connections
docker exec http2-attacker-* sh -c "netstat -an | grep ESTABLISHED | wc -l" 2>/dev/null || echo "0"
```

**Error Rates:**
```bash
# Monitor HTTP/2 protocol errors
docker logs apache-server | grep -E "(40[0-9]|50[0-9]|HTTP2|ERROR)" | tail -10

# Real-time error monitoring
docker logs -f apache-server | grep --line-buffered -E "(ERROR|WARN)"
```

**Thread Pool Depletion:**
```bash
# Check Apache worker threads
docker exec apache-server sh -c "ps aux | grep apache2 | wc -l" 2>/dev/null || echo "0"

# Monitor Apache worker status
docker exec apache-server sh -c "apache2ctl status" 2>/dev/null || echo "Status module not available"
```

**Latency Spikes:**
```bash
# Monitor latency distribution
for i in {1..5}; do curl -w "%{time_total}s\n" -o /dev/null -s http://localhost/; done

# Detect latency anomalies during attacks
bash -c 'baseline=$(curl -w "%{time_total}" -o /dev/null -s http://localhost/ 2>/dev/null); echo "Baseline: ${baseline}s"; for i in {1..10}; do current=$(curl -w "%{time_total}" -o /dev/null -s http://localhost/ 2>/dev/null); echo "Current: ${current}s"; done'
```

**Stream Status:**
```bash
# Monitor HTTP/2 stream flow control
docker logs apache-server | grep -E "(stream|flow.*control)" | tail -10

# Track window updates
docker logs apache-server | grep -i "window" | tail -5
```

**Average Connection Duration:**
```bash
# Monitor connection lifetimes
docker exec apache-server sh -c "ss -o | grep :80 | head -5" 2>/dev/null || echo "No connections found"

# Track persistent connections
docker logs apache-server | grep -E "(connection|establish|close)" | tail -5
```

## 🧹 Stop & Cleanup

### Stop Everything
```bash
# Stop local attacks and servers
./deploy-attack.sh zero-window local --stop
./deploy-server.sh local zero-window --stop

# Stop GCP attacks and pause server
./deploy-attack.sh zero-window 35.123.45.67 --stop  
./deploy-server.sh gcp zero-window --stop
```

### Complete Infrastructure Removal
```bash
# Destroy GCP infrastructure completely
./deploy-server.sh gcp zero-window --destruct-vm

# Clean local Docker resources
docker system prune -f
```

## Troubleshooting

### Common Issues

**Attack Won't Start:**
```bash
# Check server health first
curl -I --http2 http://localhost/  # or your GCP IP
./deploy-server.sh local zero-window --status
```

**GCP Authentication:**
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**Docker Issues:**
```bash
# Restart Docker daemon
sudo systemctl restart docker

# Clean Docker resources
docker system prune -f
```

**Health Check Failures:**
- Ensure server is fully started (wait 30 seconds after deployment)
- Check HTTP/2 is enabled: `curl -I --http2 http://target/`
- Verify firewall allows HTTP traffic (GCP automatically configured)

## 🚀 Quick Command Reference

```bash
# Help
./deploy-server.sh --help
./deploy-attack.sh --help

# Local Lab
./deploy-server.sh local zero-window
./deploy-attack.sh zero-window local --connections 512

# GCP Lab  
./setup-gcp.sh
./deploy-server.sh gcp zero-window
./deploy-attack.sh zero-window 35.123.45.67 --connections 512

# Monitor & Stop
./deploy-attack.sh zero-window local --logs
./deploy-attack.sh zero-window local --stop
./deploy-server.sh gcp zero-window --destruct-vm
```

## 📚 References & Further Reading

### Protocol Documentation
- [RFC 7540: HTTP/2 Specification](https://tools.ietf.org/html/rfc7540)
- [HTTP/2 Flow Control Mechanisms](https://tools.ietf.org/html/rfc7540#section-6.9) 
- [Apache HTTP/2 Module Documentation](https://httpd.apache.org/docs/2.4/mod/mod_http2.html)

### Cloud & Infrastructure
- [GCP Free Tier Documentation](https://cloud.google.com/free/docs/gcp-free-tier)
- [Google Cloud CLI Reference](https://cloud.google.com/sdk/gcloud/reference)


