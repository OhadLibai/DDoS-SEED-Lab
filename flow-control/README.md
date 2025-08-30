# HTTP/2 Flow Control Attack Lab

## Overview

This lab explores HTTP/2 flow control vulnerabilities through three distinct attack types. Each attack demonstrates different exploitation techniques.

**Focus**: Compare attack effectiveness between local Docker environments and GCP free-tier cloud deployment to understand network conditions' impact on attack success.

## 🚀 Quick Start

### Prerequisites
- **Local**: Docker, Docker Compose
- **GCP**: Google Cloud CLI, Terraform, GCP project (free tier)

### Choose Your Attack Lab

| Lab | Target | Learning Focus | Start Command |
|-----|--------|----------------|---------------|
| **Zero-Window** | Apache 2.4.55 | Basic HTTP/2 flow control | `cd zero-window/local && ./run.sh` |
| **Slow-Incremental** | Apache 2.4.62 | Sustained resource exhaustion | `cd slow-incremental/local && ./run.sh` |
| **Adaptive-Slow** | Apache 2.4.62 | Advanced attack intelligence | `cd adaptive-slow/local && ./run.sh` |

### Local Docker Deployment

**Run attacks locally with Docker:**

```bash
# Choose your attack lab:
cd zero-window/local && ./run.sh           # Basic HTTP/2 flow control
cd slow-incremental/local && ./run.sh      # Sustained resource exhaustion  
cd adaptive-slow/local && ./run.sh         # Advanced attack intelligence
```

**What happens:**
1. ✅ Starts Apache server (version-specific per lab)
2. ✅ Builds attacker container with Python tools
3. ✅ Shows ready-to-run attack commands
4. ✅ Monitor with `docker stats`, `curl`, etc.

**Example workflow:**
```bash
cd zero-window/local/
./run.sh                                       # Start environment

# In new terminal - run attack:
docker exec zero-window-attacker python3 /workspace/shared/scripts/zero_window_attack.py apache-victim --port 80 --connections 512 --verbose

# In another terminal - monitor:
docker stats --no-stream
curl -w "Time: %{time_total}s\n" http://localhost/
```

**Cleanup:**
```bash
docker-compose down
```

## 🌐 GCP Free Tier Deployment

### Phase 1: One-Time Infrastructure Setup

1. **Create GCP Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Sign in with Google account (create one if needed)  
   - Click "Create Project" → Enter name like "HTTP2-Lab" → Note the **Project ID**

2. **Open Cloud Shell**:
   - Click the **Cloud Shell icon** `>_` in top toolbar
   - A terminal opens in your browser (all tools pre-installed!)

3. **Setup Infrastructure** (one-time):
   ```bash
   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   
   # Clone the lab repository
   git clone https://github.com/your-username/DDOS-Sandbox.git
   cd DDOS-Sandbox
   
   # Enable required APIs
   gcloud services enable compute.googleapis.com
   
   # Create reusable infrastructure
   cd shared/gcp
   ./setup-infrastructure.sh
   ```

### Phase 2: Deploy Any Attack (Instant)

**After infrastructure exists, deploy any attack instantly:**

```bash
# Choose your attack lab:
cd zero-window/gcp && ./deploy-attack.sh           # Basic attack
cd slow-incremental/gcp && ./deploy-attack.sh      # Sustained attack  
cd adaptive-slow/gcp && ./deploy-attack.sh         # Advanced attack
```

**Each deployment automatically:**
- ✅ Switches Apache version for the attack
- ✅ Copies attack script to instance
- ✅ Starts attack automatically
- ✅ Provides web terminal access

### Access Your Running Lab

**🌐 Web Terminal**: `http://INSTANCE_IP:8080` - Full terminal in browser
**🎯 Apache Target**: `http://INSTANCE_IP` - See attack impact
**📊 Live Monitoring**: Use commands from "Live Monitoring Commands" section below

### Switch Between Labs

**No rebuild needed! Switch instantly:**
```bash
cd zero-window/gcp && ./deploy-attack.sh        # Switch to Zero Window
cd slow-incremental/gcp && ./deploy-attack.sh   # Switch to Slow Incremental  
cd adaptive-slow/gcp && ./deploy-attack.sh      # Switch to Adaptive Slow
```

**Free Tier Specifications**:
- **Instance**: f1-micro (always free eligible)
- **One VM**: Runs all attack types
- **Storage**: 20GB (of 30GB total allowance)  
- **Auto-shutdown**: 4 hours (cost control)
- **Region**: us-central1 (free tier compatible)
- **No billing account required**

### Cleanup
```bash
cd shared/gcp && ./cleanup-infrastructure.sh
```

## 📊 SEED Lab Methodology

### Lab Objectives
1. **Understand** HTTP/2 flow control protocol weaknesses
2. **Implement** three different attack vectors with varying characteristics
3. **Compare** local vs cloud attack effectiveness and network impact
4. **Analyze** server resource exhaustion patterns under different conditions

### Performance Comparison Framework
Each lab includes comprehensive monitoring to compare:
- **Connection establishment rates** (local network vs internet)
- **Server response degradation** patterns
- **Resource utilization** efficiency differences
- **Attack sustainability** across environments
- **Network latency impact** on attack success

## 📝 Live Monitoring Commands

### Basic Monitoring (All Labs)
```bash
# Container resource usage
docker stats --no-stream

# Response time test  
curl -w "Time: %{time_total}s\n" -s -o /dev/null http://localhost/

# Active connections
ss -tuln | grep :80 | wc -l
```

### Intermediate Monitoring
```bash
# Continuous response monitoring
while true; do 
  curl -w "$(date +%H:%M:%S) - Response: %{time_total}s\n" -s -o /dev/null http://localhost/
  sleep 5
done

# Resource tracking
watch -n 10 "echo 'Connections:'; ss -tuln | grep :80 | wc -l; echo 'Memory:'; free -m | grep Mem"

# Attack effectiveness
docker logs [container-name] | tail -20
```

### Advanced Monitoring
```bash
# Connection state analysis
ss -tuln | grep :80 | awk '{print $1}' | sort | uniq -c

# Network packet inspection
tcpdump -i any -n port 80 -c 50

# Apache process monitoring (inside container)
docker exec [container-name] ps aux | grep httpd

# Detailed connection metrics
ss -i | grep :80 | head -10

# System load analysis
uptime && iostat -x 1 3
```

### GCP Cloud Monitoring
```bash
# SSH to GCP instance
ssh ubuntu@INSTANCE_IP

# Use monitoring commands from the guide below
# See "📝 Live Monitoring Commands" section

# System resource monitoring
htop

# Network analysis with cloud latency
ping -c 10 8.8.8.8
traceroute google.com
```

## 🧹 Cleanup & Safety

### Local Environment
```bash
# In any lab directory
cd local/
docker-compose down
docker system prune -f  # Optional: clean unused containers
```

### GCP Environment  
```bash
# In lab's gcp directory - ALWAYS RUN THIS
terraform destroy -var="project_id=YOUR_PROJECT_ID" -auto-approve

# Verify no running instances
gcloud compute instances list
```

### Emergency GCP Cleanup
```bash
# If terraform destroy fails, nuclear option:
gcloud compute instances delete --zone=us-central1-a $(gcloud compute instances list --format="value(name)") --quiet
```

## ⚠️ Important Notes

### GCP Free Tier Limits
- **744 hours/month** f1-micro usage (one instance can run continuously)
- **30GB** persistent disk storage total
- **1GB** network egress to most regions per month
- **Auto-shutdown after 2 hours** prevents accidental charges

### Troubleshooting
- **Docker issues**: Ensure Docker daemon is running
- **GCP authentication**: Run `gcloud auth login` and set project
- **Terraform errors**: Check GCP APIs are enabled
- **Attack not working**: Verify Apache HTTP/2 is enabled with `curl -I --http2`

## 📚 References & Further Reading

- [RFC 7540: HTTP/2 Specification](https://tools.ietf.org/html/rfc7540)
- [HTTP/2 Flow Control Mechanisms](https://tools.ietf.org/html/rfc7540#section-6.9)
- [Apache HTTP/2 Module Documentation](https://httpd.apache.org/docs/2.4/mod/mod_http2.html)
- [GCP Free Tier Documentation](https://cloud.google.com/free/docs/gcp-free-tier)