# HTTP/2 Flood Attack Lab

## 📋 Overview

The HTTP/2 Flood Attack Lab is a comprehensive educational laboratory exercise designed to explore Distributed Denial of Service (DDoS) attacks that exploit HTTP/2 multiplexing capabilities. 
**Focus**: Understanding HTTP/2 vulnerabilities through practical experimentation while learning defensive security concepts.

## 🎯 Lab Objectives

### Primary Learning Goals
1. **Attack Vector Understanding** - Comprehend HTTP/2 flood attack mechanisms and characteristics
2. **Performance Measurement** - Learn to quantify attack effectiveness and system degradation  
3. **Cloud vs Local Comparison** - Evaluate performance differences between local and cloud deployments

## 🏗️ Lab Structure

### Part A: Single-Worker HTTP/2 Server Attack
- **Target**: Single-worker HTTP/2 server (development environment)
- **Attack Script**: Basic `http_flood.py` 
- **Expected Behavior**: Significant performance degradation due to single-worker processing limits
- **Learning Focus**: Understanding baseline HTTP/2 server vulnerabilities

### Part B: Multi-Worker HTTP/2 Server Attack
- **Target**: Multi-worker HTTP/2 server (production-like environment)
- **Attack Scripts**: Basic `http_flood.py` + Advanced `cloud_http_flood.py`
- **Expected Behavior**: Better resilience through worker distribution, gradual degradation under sustained load
- **Learning Focus**: Server architecture differences and advanced attack evasion techniques

## ⚡ Quick Start

### 💻 Local Deployment

```bash
# Part A: Attack single-worker server
./deploy.sh --local part-A

# Part B: Attack multi-worker server (basic)
./deploy.sh --local part-B

# Part B: Attack multi-worker server (advanced)
ATTACK=advanced ./deploy.sh --local part-B

# With custom scenarios
SCENARIO=captcha ./deploy.sh --local part-A
SCENARIO=crypto DIFFICULITY=3 ./deploy.sh --local part-B

# Custom connection counts
CONNECTIONS=256 ./deploy.sh --local part-A
```

### ☁️ GCP Cloud Deployment (Decoupled Design)

#### 🏗️ Phase 1: Infrastructure Setup (One-Time Only)
Set up your GCP environment and create the VM infrastructure:

**In Cloud Shell or locally:**
```bash
# Set up your project
gcloud config set project YOUR_PROJECT_ID
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
gcloud services enable compute.googleapis.com

# Clone the lab
git clone <repository-url>
cd DDOS-sandbox-http2-flood

# Create infrastructure (one-time setup)
./gcp-setup-infrastructure.sh
```

#### 🚀 Phase 2: Lab Deployment (Reusable)
Deploy different lab configurations instantly on your existing VM:

```bash
# Deploy different lab parts
./deploy.sh --gcp part-A                    # Single-worker attack
./deploy.sh --gcp part-B                    # Multi-worker attack

# Switch scenarios instantly
SCENARIO=captcha ./deploy.sh --gcp part-A   # CAPTCHA scenario
SCENARIO=crypto DIFFICULITY=3 ./deploy.sh --gcp part-B  # Crypto scenario

# Custom connection counts
CONNECTIONS=512 ./deploy.sh --gcp part-A    # High-intensity attack
CONNECTIONS=128 SCENARIO=gaming ./deploy.sh --gcp part-B  # Gaming scenario with custom connections

# Advanced attacks
ATTACK=advanced ./deploy.sh --gcp part-B    # Advanced evasion techniques
```

#### ⚙️ Phase 3: Lab Control & Operations
Manage your running labs with the unified deployment script:

```bash
# Stop operations
./deploy.sh --gcp --stop       # Stop lab containers (keep VM running)
./deploy.sh --gcp --stop --vm  # Stop containers + shutdown VM (save costs)

# Advanced operations (when needed)
gcloud compute ssh http2-flood-lab --zone=us-central1-a  # SSH into VM
gcloud compute instances start http2-flood-lab --zone=us-central1-a  # Restart stopped VM
```

#### Benefits of Decoupled Design
**Infrastructure Reuse** - One VM serves all lab configurations  
**Instant Switching** - Change between attacks in seconds  
**Cost Efficient** - Single f1-micro instance (free tier eligible)  
**Flexible Testing** - Experiment with different scenarios rapidly  

#### What Happens:
- **Phase 1** creates persistent VM with Docker environment
- **Phase 2** deploys lab configurations without rebuilding infrastructure  
- **Lab runs at**: `http://[VM-EXTERNAL-IP]:8080`
- **Cost Protection**: VM auto-shuts down after 2 hours when idle

### 🧹 Cleanup

```bash
# Unified cleanup options
./cleanup.sh              # Local Docker cleanup (default)
./cleanup.sh --local      # Explicit local cleanup
./cleanup.sh --gcp        # Stop GCP lab (keep VM running)
./cleanup.sh --gcp --vm   # Stop GCP lab + VM (save costs)
./cleanup.sh --all        # Clean both local + GCP

# Alternative: Using deploy script
./deploy.sh --gcp --stop     # Stop GCP lab containers
./deploy.sh --gcp --stop --vm # Stop GCP lab + VM
```

## 🔧 CPU Workload Scenarios

The lab supports multiple CPU-intensive scenarios (located in `shared/scenarios/`) that replace the default proof-of-work computation:

**📖 For detailed scenario documentation, see [shared/scenarios/README_scenarios.md](shared/scenarios/README_scenarios.md)**

| Scenario | Description | Use Case |
|----------|-------------|----------|
| `proof_of_work` | Default cryptocurrency-style mining | Baseline CPU workload |
| `captcha` | Visual/audio CAPTCHA generation | Bot protection systems |
| `crypto` | Cryptographic operations | SSL/TLS handshakes |
| `gaming` | Sudoku/maze generation | Game server content |
| `antibot` | Anti-automation challenges | Rate limiting systems |
| `webservice` | Map tiles/routing | Real-world web services |
| `content` | Search/preview generation | Content management |

### Scenario Usage
```bash
# Deploy with specific scenarios
SCENARIO=captcha ./deploy.sh --local part-A        # Local deployment
SCENARIO=crypto DIFFICULITY=4 ./deploy.sh --gcp part-B    # GCP deployment
```

## 📊 Live Monitoring and Testing

### Essential Monitoring Commands

Run these commands during attacks to observe the impact in real-time:

#### Response Time Monitoring
```bash
# Watch server response times degrade
watch -n 1 'curl -w "Response: %{time_total}s\n" -o /dev/null -s http://localhost:8080'
```

#### Resource Usage Monitoring
```bash
# Monitor CPU and memory usage
watch -n 2 'docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"'
```

#### Service Availability Testing
```bash
# Experience the denial of service effect
curl -w "Time:%{time_total}s Code:%{http_code}\n" http://localhost:8080

# Health check endpoint
curl --http2-prior-knowledge http://localhost:8080/health
```

#### Connection Count Monitoring
```bash
# Monitor active connections
watch -n 1 'ss -tan | grep :8080 | wc -l'
```

#### Advanced Monitoring
```bash
# Monitor HTTP/2 streams and multiplexing
watch -n 1 'netstat -an | grep 8080'

# Monitor Docker container resource limits
docker exec http2-victim-single cat /sys/fs/cgroup/memory/memory.usage_in_bytes
```

## ⚙️ Prerequisites

### System Requirements
- **Docker** and **Docker Compose** installed
- Available port 8080 on your system
- **Google Cloud Platform** account (for cloud deployment)
- 4GB+ RAM recommended for local testing

### Knowledge Prerequisites
- Basic understanding of HTTP/1.1 and HTTP/2 protocols
- Familiarity with client-server architecture and async processing
- Elementary networking concepts (TCP connections, multiplexing)
- Basic command-line proficiency

### GCP Requirements
- Google Cloud SDK (`gcloud`) installed and configured
- Active GCP project with Compute Engine API enabled
- SSH client for remote access

## 🚀 Advanced Usage

### Custom Attack Parameters
```bash
# Adjust attack intensity
CONNECTIONS=256 ./local-deploy.sh part-B

# Custom DIFFICULITY levels
DIFFICULITY=1 ./local-deploy.sh part-A   # Light CPU load
DIFFICULITY=5 ./local-deploy.sh part-A   # Heavy CPU load
```

### Multi-Vector Attacks
```bash
# Advanced attack with header diversification and evasion
ATTACK=advanced ./gcp-deploy.sh part-B
```

## 🔧 Troubleshooting

### Common Issues

**Port 8080 in use**:
```bash
# Check what's using the port
ss -tuln | grep :8080
./cleanup.sh  # Stop all lab containers
```

**Docker permission errors**:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**GCP authentication issues**:
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

**GCP auto-shutdown extension**:
```bash
# Cancel scheduled shutdown
sudo atrm $(atq | awk '{print $1}')
# Extend by 2 more hours  
echo "sudo shutdown -h now" | at now + 2 hours
```

**Attack not effective**:
- Increase DIFFICULITY level. The higher the difficulity- the busiest the server is.
- Check container resource limits

## 🎓 Learning Deliverables
This lab follows the SEED (SEcurity EDucation) project methodology, emphasizing:
- Performance comparison reports
- Attack effectiveness analysis
- Infrastructure resilience assessment
- Defensive strategy recommendations
  
- Hands-on experiential learning
- Controlled laboratory environments  
- Comparative analysis approaches
- Defensive security perspectives