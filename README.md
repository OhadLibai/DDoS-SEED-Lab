# DDoS SEED Lab - HTTP/2 Protocol Vulnerability Studies
*Libai Ohad*  
*Ben Zion Roei*

---
A comprehensive educational laboratory suite for exploring Distributed Denial of Service (DDoS) attacks targeting HTTP/2 protocol vulnerabilities. This lab collection provides hands-on experience with modern web protocol exploitation techniques through controlled local environments and real-world cloud deployments.

## 🎯 Learning Objectives

- **Protocol Vulnerability Analysis**: Understand HTTP/2 and HTTP/1.1 attack mechanisms
- **Performance Impact Assessment**: Quantify attack effectiveness and system degradation
- **Cloud vs Local Comparison**: Evaluate attack performance across different deployment scenarios
- **Real-world Attack Simulation**: Experience internet-scale attacks using cloud infrastructure

## 🏗️ Lab Architecture

### Clean Separation Design
All labs implement **clean separation** between server deployment and attack deployment:
- **Deploy servers independently** (local or cloud)
- **Launch attacks against running servers** 
- **Real internet simulation**: Attack from local machine → cloud servers
- **Independent operation**: Servers run without attacks, attacks target existing servers

### Network Topologies

#### Local Testing Environment
```
┌─────────────────┐    ┌─────────────────┐
│ Attack Container│◄──►│Server Container │
│                 │    │                 │
└─────────────────┘    └─────────────────┘
     Bridge Network        HTTP/2 Server
```

#### Cloud Testing Environment
```
┌─────────────────┐    Internet    ┌─────────────────┐
│ Local Attack    │◄──────────────►│ GCP VM          │
│ Container       │                │ ┌─────────────┐ │
└─────────────────┘                │ │HTTP/2       │ │
                                   │ │Container    │ │
                                   │ └─────────────┘ │
                                   └─────────────────┘
```

## 📚 Lab Components

### 1. HTTP/2 Application Flood Attack Lab (`http2-app-flood/`)
**Focus**: HTTP/2 multiplexing exploitation and application-layer flooding

- **Part A**: Single-worker development environment testing  
- **Part B**: Multi-worker production-like environment testing
- **Attack Types**: Basic flood, advanced evasion techniques
- **Scenarios**: 6 CPU-intensive workload types (CAPTCHA, crypto, gaming, etc.)
- **Key Learning**: HTTP/2 stream multiplexing vulnerabilities, server resource exhaustion

### 2. HTTP/2 Flow Control Attack Lab (`flow-control/`)
**Focus**: HTTP/2 flow control mechanism exploitation

- **Zero-Window Attack**: Forces indefinite worker thread blocking
- **Slow-Incremental Attack**: Sustained resource exhaustion via minimal window updates
- **Adaptive-Slow Attack**: Intelligent attack adaptation with evasion techniques  
- **Key Learning**: Protocol-level flow control abuse, connection state manipulation

### 3. Slowloris Attack Lab (`bonus-slowloris/`)
**Focus**: HTTP/1.1 legacy protocol vulnerabilities in HTTP/2 environments

- **Basic Slowloris**: Traditional incomplete header attacks
- **Advanced Slowloris**: Modern server evasion with multi-threading
- **Cloud Slowloris**: Steganographic headers with intelligent adaptation
- **Key Learning**: Backward compatibility attack vectors, protocol fallback exploitation

## 🚀 Quick Start

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Google Cloud Platform** account (free tier, no billing required)
- **gcloud CLI** installed for cloud deployments
- 4GB+ RAM recommended for local testing

### Choose Your Lab Path

#### Option 1: Start with HTTP/2 Application Floods
```bash
cd http2-app-flood
./deploy-server.sh --local part-A
./deploy-attack.sh --local part-A
```

#### Option 2: Explore Flow Control Attacks
```bash
cd flow-control
./deploy-server.sh local zero-window
./deploy-attack.sh zero-window local --connections 512
```

#### Option 3: Study Legacy Protocol Vulnerabilities
```bash
cd bonus-slowloris
./deploy-server.sh latest local
./deploy-attack.sh advanced local --logs
```

### Real Internet Testing (GCP Free Tier)

Each lab supports cloud deployment for realistic internet-scale testing:

```bash
# One-time GCP setup (run from any lab directory)
./setup-gcp-infrastructure.sh YOUR_PROJECT_ID

# Deploy server to cloud
./deploy-server.sh --gcp <lab-specific-options>

# Attack cloud server from local machine
./deploy-attack.sh --gcp <lab-specific-options>
```

## 🔧 Common Deployment Patterns

### Server Deployment
```bash
# Local development
./deploy-server.sh --local <options>

# Cloud production testing  
./deploy-server.sh --gcp <options>

# Stop servers
./deploy-server.sh --stop

# Destroy cloud infrastructure
./deploy-server.sh --destruct-vm
```

### Attack Deployment
```bash
# Local attacks (to local servers)
./deploy-attack.sh --local <attack-type> <options>

# Cloud attacks (from local to cloud servers)
./deploy-attack.sh --gcp <attack-type> <options>

# Stop all attacks
./deploy-attack.sh --stop
```

## 📊 Monitoring and Analysis

### Essential Monitoring Commands

**Response Time Testing**:
```bash
# Local server
watch -n 1 'curl -w "Response: %{time_total}s\n" -o /dev/null -s http://localhost:8080'

# Cloud server  
curl -w "Response: %{time_total}s\n" -o /dev/null -s http://EXTERNAL_IP:8080
```

**Resource Usage**:
```bash
# Local containers
docker stats --no-stream

# Cloud resources
gcloud compute ssh <instance-name> --command="docker stats --no-stream"
```

**Connection Analysis**:
```bash
# Active connections
ss -tan | grep :8080 | wc -l

# Container-level connections
docker exec <container> sh -c "awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp"
```

## 🧹 Cleanup and Cost Management

### Complete Lab Cleanup
```bash
# Stop all local resources
docker stop $(docker ps -q)
docker system prune -f

# Destroy all GCP resources
./deploy-server.sh --gcp --destruct-vm  # Run from any lab directory
```

### Cost Management
- GCP VMs auto-shutdown after 2 hours to prevent unexpected charges
- Use `--destruct-vm` flag to completely remove cloud infrastructure
- Monitor GCP billing dashboard for usage

## 📋 Lab Directory Structure

```
DDoS-SEED-Lab/
├── README.md                    # This overview document
├── http2-app-flood/            # HTTP/2 application flood attacks
│   ├── README.md               
│   ├── part-A/                 # Single-worker environment
│   ├── part-B/                 # Multi-worker environment
│   ├── deploy-server.sh
│   └── deploy-attack.sh
├── flow-control/               # HTTP/2 flow control attacks  
│   ├── README.md
│   ├── attacks/                # Attack implementations
│   ├── deploy-server.sh
│   └── deploy-attack.sh
└── bonus-slowloris/           # HTTP/1.1 slowloris attacks
    ├── README.md
    ├── attacks/               # Slowloris variants
    ├── deploy-server.sh
    └── deploy-attack.sh
```

## 📚 Further Reading

- [RFC 7540: HTTP/2 Specification](https://tools.ietf.org/html/rfc7540)
- [HTTP/2 Flow Control Mechanisms](https://tools.ietf.org/html/rfc7540#section-6.9)
- [Apache HTTP/2 Module Documentation](https://httpd.apache.org/docs/2.4/mod/mod_http2.html)
- [GCP Free Tier Documentation](https://cloud.google.com/free/docs/gcp-free-tier)
