# Slowloris Attack Lab

This lab demonstrates **HTTP/1.1 slowloris attacks** as part of a larger HTTP/2 protocol vulnerability study. While the main lab focuses on HTTP/2 exploits, this bonus section shows how legacy protocol attacks remain effective due to backward compatibility requirements.

### HTTP/2 Context

This lab demonstrates HTTP/1.1 attacks within an HTTP/2 learning environment because:
- **Compatibility**: HTTP/2 servers almost certainly support HTTP/1.1 fallback
- **Real-world**: Many connections still use HTTP/1.1
- **Attack Surface**: Legacy protocol support creates vulnerabilities
- **Educational Value**: Understanding both old and new attack vectors


## Lab Objectives

- **Compatibility Issues**: Understand how backward compatibility demands create attack vectors
- **Performance Comparison**: Evaluate cloud vs. local environment performance and scalability  
- **Attack Implementation**: Master slowloris techniques across different deployment scenarios
- **Real-world Simulation**: Experience internet-scale attacks using cloud infrastructure

## Attack Types

### Basic Slowloris (`basic`)
- **Target**: Old Apache servers (2.2.14 and earlier, 2009's and before)
- **Mechanism**: Incomplete HTTP headers sent slowly
- **Connections**: 256 (default)
- **Script**: `attacks/slowloris.py`

### Advanced Slowloris (`advanced`)
- **Target**: Modern Apache with hardening (latest image!)
- **Mechanism**: Multi-threaded with adaptive pacing
- **Connections**: 512 (default)
- **Features**: Dynamic sleep adjustment, larger headers
- **Script**: `attacks/advanced_slowloris.py`

### Cloud Slowloris (`cloud`)
- **Target**: Internet-facing servers (local or cloud)
- **Mechanism**: Steganographic headers, evasion techniques
- **Connections**: 512 (default)
- **Features**: Realistic user agents, intelligent adaptation, connection rotation
- **Script**: `attacks/cloud_advanced_slowloris.py`

## Quick Start

### Prerequisites
- Docker installed and running
- For cloud deployment: gcloud CLI installed and configured

## GCP Setup (One-Time Only)

**Important**: Run `./setup-gcp-infrastructure.sh` only once per GCP project. It creates permanent infrastructure.

1. **Create GCP Account**: Visit [Google Cloud Console](https://console.cloud.google.com)
2. **Enable Billing**: Required for Compute Engine (free tier available)
3. **Install gcloud CLI**:
   ```bash
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   gcloud init  # Authenticate and select project
   ```

4. **Get the lab files**:
   ```bash
   git clone <repository-url>
   cd DDoS-SEED-Lab/bonus-slowloris
   ```

5. **Run setup script**:
   ```bash
   ./setup-gcp-infrastructure.sh  # Creates e2-micro VM (free tier)
   ```

### Cost Management
```bash
./deploy-server.sh --stop         # Stop VM (keeps disk)
./deploy-server.sh --destruct-vm   # Destroy everything (saves costs)
```

## Deployment Scripts

### deploy-server.sh 
[old|latest] [local|gcp] [--logs] [--stop] [--destruct-vm]
```bash
./deploy-server.sh old local --logs        # Apache 2.2.14, follow logs
./deploy-server.sh latest gcp             # Modern Apache on cloud
./deploy-server.sh --stop                 # Stop all servers
./deploy-server.sh --destruct-vm           # Destroy GCP resources
```

### deploy-attack.sh
[basic|advanced|cloud] [local|gcp] [--connections NUM] [--logs] [--stop]
```bash
./deploy-attack.sh basic local --logs         # Basic attack (local or GCP)
./deploy-attack.sh advanced gcp --connections 300  # Advanced attack (local or GCP)
./deploy-attack.sh cloud local --logs         # Cloud attack (local or GCP)
./deploy-attack.sh cloud gcp                  # All attacks work on both targets
./deploy-attack.sh --stop                     # Stop all attacks
```

## Workflows

### Local Testing Workflow
```bash
# 1. Deploy server (with logs)
./deploy-server.sh latest local --logs

# 2. In another terminal, launch attack
./deploy-attack.sh advanced local --logs

# 3. Monitor server response time in third terminal
curl --no-progress-meter -o /dev/null -w "Time: %{time_total}s\n" http://localhost:8080

# 4. Stop everything when done
./deploy-attack.sh --stop
./deploy-server.sh --stop
```

### Cloud Testing Workflow
```bash
# 1. Deploy server to cloud (setup-gcp-infrastructure.sh must be run first)
./deploy-server.sh latest gcp

# 2. Attack from local machine to cloud
./deploy-attack.sh cloud gcp --logs

# 3. Clean up when completely done
./deploy-server.sh --destruct-vm
```






## Port Configuration

**Local Deployment:**
- **Host Access:** `http://localhost:8080` 
- **Container Port:** `80` (Apache default)
- **Port Mapping:** Host port `8080` → Container port `80`

**GCP Deployment:**
- **External Access:** `http://VM_IP:80`
- **VM Port:** `80` (direct Apache access)
- **Firewall:** Allows TCP traffic on ports 80 and 8080

## Network Architecture

### Local Setup
```
┌─────────────────┐    ┌─────────────────┐
│ Attack Container│◄──►│Server Container │
│ (slowloris-*)   │    │ (Apache)        │
└─────────────────┘    └─────────────────┘
   Bridge Network    Host Port 8080→Container Port 80
```

### Cloud Setup  
```
┌─────────────────┐    Internet    ┌─────────────────┐
│ Local Attack    │◄──────────────►│ GCP VM          │
│ Container       │                │ ┌─────────────┐ │
└─────────────────┘                │ │Apache       │ │
                                   │ │Container    │ │
                                   │ └─────────────┘ │
                                   └─────────────────┘
```


## Monitoring

### Follow Live Logs

**Follow attack progress:**
```bash
./deploy-attack.sh advanced local --logs    # Auto-follow logs
docker logs -f slowloris-advanced-attack    # Manual log following
```

**Follow server logs:**
```bash
./deploy-server.sh latest local --logs      # Auto-follow logs  
docker logs -f slowloris-latest-server      # Manual log following
```

### Monitor Attack Impact

**Check active connections:**
```bash
# Local server connections
docker exec slowloris-*-server sh -c "awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp"
```

**Test response times:**
```bash
# Local server (mapped to host port 8080)
curl --no-progress-meter -o /dev/null -w "Time: %{time_total}s\n" http://localhost:8080

# GCP server (direct access on port 80)  
curl --no-progress-meter -o /dev/null -w "Time: %{time_total}s\n" http://$(gcloud compute instances describe slowloris-victim --format="get(networkInterfaces[0].accessConfigs[0].natIP)"):80
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
# Monitor HTTP requests per second
docker logs -f slowloris-*-attack | grep -c "request" &
sleep 10; kill $!

# Count active attack connections
docker exec slowloris-*-attack sh -c "netstat -an | grep ESTABLISHED | wc -l"
```

**Error Rates:**
```bash
# Monitor HTTP error responses (already exists above, enhanced here)
docker logs slowloris-*-server | grep -E "(40[0-9]|50[0-9])" | tail -20

# Real-time error monitoring
docker logs -f slowloris-*-server | grep --line-buffered -E "(ERROR|WARN)"
```

**CPU and Memory Usage:**
```bash
# Real-time resource monitoring
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Continuous monitoring
watch -n 3 'docker stats --no-stream'
```

**Thread Pool Depletion:**
```bash
# Check server thread status
docker exec slowloris-*-server sh -c "ps aux | grep apache | wc -l"

# Monitor worker processes
docker exec slowloris-*-server sh -c "apache2ctl status" 2>/dev/null || echo "Status module not available"
```

**Latency Spikes:**
```bash
# Monitor latency distribution
for i in {1..10}; do curl -w "%{time_total}s\n" -o /dev/null -s http://localhost:8080; done

# Detect latency anomalies
bash -c 'baseline=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080 2>/dev/null); echo "Baseline: ${baseline}s"; while true; do current=$(curl -w "%{time_total}" -o /dev/null -s http://localhost:8080 2>/dev/null); if (( $(echo "$current > $baseline * 2" | bc -l) )); then echo "SPIKE: ${current}s ($(date))"; fi; sleep 1; done'
```

**Stream Status:**
```bash
# Monitor HTTP/1.1 connection streams (slowloris specific)
docker exec slowloris-*-server sh -c "netstat -an | grep ':80.*ESTABLISHED' | wc -l"

# Track incomplete requests
docker logs slowloris-*-server | grep -E "(incomplete|partial)" | tail -10
```

**Average Connection Duration:**
```bash
# Monitor connection lifetimes
docker exec slowloris-*-server sh -c "ss -o | grep :80 | awk '{print \$6}' | grep -o 'timer:[^,]*'"

# Track persistent connections
docker logs slowloris-*-server | grep -E "(connection|closed)" | tail -10
```

### Real-time Monitoring Loop

```bash
#!/bin/bash
# Save as monitor.sh and run: chmod +x monitor.sh && ./monitor.sh
while true; do
    echo "=== $(date) ==="
    echo "Connections: $(docker exec slowloris-*-server sh -c "awk 'NR>1 && \$4==\"01\" {count++} END {print count+0}' /proc/net/tcp" 2>/dev/null || echo "0")"
    echo -n "Response: "
    curl --no-progress-meter -o /dev/null -w "%{time_total}s\n" http://localhost:8080 2>/dev/null || echo "TIMEOUT"
    echo "Attack containers: $(docker ps --filter name=slowloris-*-attack -q | wc -l)"
    echo ""
    sleep 5
done
```

## Cloud vs Local Performance

### Measuring Performance Delta

Run identical attacks on both environments:

```bash
# Local performance test
./deploy-server.sh latest local
time ./deploy-attack.sh advanced local --connections 500

# Cloud performance test  
./deploy-server.sh latest gcp
time ./deploy-attack.sh advanced gcp --connections 500
```

### Log Analysis

**View all container logs:**
```bash
docker logs $(docker ps -q --filter name=slowloris)
```

**Follow live attack progress:**
```bash
docker logs -f --tail 50 slowloris-*-attack
```

**Analyze attack patterns:**
```bash
# Search for connection attempts
docker logs slowloris-*-attack | grep "connection"

# Monitor server errors
docker logs slowloris-*-server | grep -i error

# Export logs for analysis
docker logs slowloris-advanced-attack > attack-log.txt 2>&1
```

## Troubleshooting

### Common Issues

**"Health check failed"**  
- Verify server is running: `docker ps`
- Check port accessibility: `curl http://localhost:8080` (local) or `curl http://VM_IP:80` (GCP)
- Review server logs: `docker logs slowloris-*-server`

**"GCP VM not found"**  
- Run setup script: `./setup-gcp-infrastructure.sh`
- Verify gcloud auth: `gcloud auth list`
- Check project config: `gcloud config list`

**"Docker build failed"**
- Verify Docker is running: `docker version`
- Clean Docker cache: `docker system prune`
- Check disk space: `df -h`
