# HTTP Flood Lab - Performance Monitoring Guide

## Overview
This guide provides step-by-step instructions for monitoring HTTP flood attacks in both Part A (single-threaded Flask) and Part B (multi-threaded Gunicorn) deployments. **The guide covers both LOCAL DOCKER and GOOGLE CLOUD PLATFORM (GCP) environments to enable performance comparison between the two deployment scenarios.**

## Environment Setup

### 🏠 Local Environment Prerequisites
- Docker and Docker Compose installed on local machine
- Available port 8080 on local system
- Basic command line knowledge

### ☁️ GCP Environment Prerequisites
- GCP VM instance with Docker and Docker Compose installed
- SSH access to the GCP instance
- Firewall rules allowing port 8080 traffic
- Basic knowledge of command line operations

## Environment-Specific Setup

### 🏠 LOCAL ENVIRONMENT Setup

```bash
# Navigate to the lab directory
cd DDoS-SEED-lab/http_flood_lab

# Deploy Part A (Single-threaded Flask)
cd part_A
docker-compose up -d

# OR Deploy Part B (Multi-threaded Gunicorn)
cd part_B
docker-compose up -d

# Set target URL for local environment
export TARGET_URL="http://localhost:8080"
echo "Local target: $TARGET_URL"
```

### ☁️ GCP ENVIRONMENT Setup

```bash
# SSH into your GCP VM instance
gcloud compute ssh your-vm-name --zone=your-zone

# Clone and navigate to the lab
git clone <your-repo-url>
cd DDoS-SEED-lab/http_flood_lab

# Deploy Part A (Single-threaded Flask)
cd part_A
docker-compose up -d

# OR Deploy Part B (Multi-threaded Gunicorn)
cd part_B
docker-compose up -d

# Get GCP external IP and set target URL
EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/external-ip -H "Metadata-Flavor: Google")
export TARGET_URL="http://$EXTERNAL_IP:8080"
echo "GCP target: $TARGET_URL"

# Alternative method to get external IP
# EXTERNAL_IP=$(gcloud compute instances describe $(hostname) --zone=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4) --format="value(networkInterfaces[0].accessConfigs[0].natIP)")
```

## Performance Monitoring Methodology

### 📄 UNIVERSAL COMMANDS (Same for Both Environments)

The following commands work identically in both local and GCP environments. **Use $TARGET_URL variable** (set during environment setup) for consistent monitoring.

### Phase 1: Pre-Attack Baseline Collection (60 seconds)

> **🎯 OBJECTIVE**: Establish performance baseline for comparison between local vs GCP environments

#### 1.1 Server Performance Baseline (UNIVERSAL)
```bash
# Terminal 1: Monitor response times (run continuously)
watch -n 1 'curl -o /dev/null -s -w "Response Time: %{time_total}s | HTTP Code: %{http_code} | Size: %{size_download} bytes\n" $TARGET_URL'

# Terminal 2: Monitor Docker container stats (UNIVERSAL)
watch -n 1 'docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"'

# Terminal 3: Monitor system resources (UNIVERSAL)
watch -n 1 'echo "=== CPU Usage ===" && top -bn1 | head -5 && echo -e "\n=== Memory Usage ===" && free -h && echo -e "\n=== Network Connections ===" && ss -tuln | grep :8080'
```

#### 1.2 Baseline Data Collection for Environment Comparison
```bash
# Collect baseline metrics (UNIVERSAL - run in both environments)
echo "=== BASELINE COLLECTION START ===" > baseline_$(date +%Y%m%d_%H%M%S).log
echo "Environment: $(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)" >> baseline_$(date +%Y%m%d_%H%M%S).log
echo "Target URL: $TARGET_URL" >> baseline_$(date +%Y%m%d_%H%M%S).log

# Run 30 baseline tests
for i in {1..30}; do
  echo "Baseline Test $i: $(date)" | tee -a baseline_$(date +%Y%m%d_%H%M%S).log
  curl -o /dev/null -s -w "Total:%{time_total}s|Connect:%{time_connect}s|TTFB:%{time_starttransfer}s|HTTP:%{http_code}\n" $TARGET_URL | tee -a baseline_$(date +%Y%m%d_%H%M%S).log
  sleep 2
done
```

#### 1.3 Environment-Specific Monitoring Setup

**☁️ GCP-Only Commands:**
```bash
# Install GCP monitoring agent (GCP ENVIRONMENT ONLY)
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Verify external connectivity (GCP ENVIRONMENT ONLY)
echo "External IP: $(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/external-ip -H "Metadata-Flavor: Google")"
gcloud compute instances describe $(hostname) --zone=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4) --format="value(networkInterfaces[0].accessConfigs[0].natIP)"
```

**🏠 Local-Only Verification:**
```bash
# Verify local setup (LOCAL ENVIRONMENT ONLY)
echo "Local Docker host: $(docker context show)"
echo "Available ports: $(ss -tuln | grep :8080 || echo 'Port 8080 available')"
```

### Phase 2: Attack Phase Monitoring (UNIVERSAL)

> **🎯 OBJECTIVE**: Monitor attack impact and collect performance degradation data for environment comparison

#### 2.1 Attack Effectiveness Monitoring (UNIVERSAL)
```bash
# Terminal 4: Start the attack (automatically starts with docker-compose up)
# Part A: 32 connections | Part B: 256 connections

# Terminal 5: Monitor attack effectiveness (UNIVERSAL)
watch -n 1 'echo "=== Connection Test ===" && timeout 10 curl -o /dev/null -s -w "Time: %{time_total}s | Connect: %{time_connect}s | TTFB: %{time_starttransfer}s | HTTP: %{http_code}\n" $TARGET_URL || echo "REQUEST TIMEOUT/FAILED"'
```

#### 2.2 Attack Impact Data Collection (UNIVERSAL)
```bash
# Terminal 6: Comprehensive latency testing for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
for i in {1..60}; do
  echo "$ENV_TYPE Test $i: $(date)"
  timeout 15 curl -o /dev/null -s -w "Total:%{time_total}s|DNS:%{time_namelookup}s|Connect:%{time_connect}s|TTFB:%{time_starttransfer}s|HTTP:%{http_code}\n" $TARGET_URL || echo "TIMEOUT/FAILED"
  sleep 2
done > http_flood_attack_${ENV_TYPE}_$(date +%Y%m%d_%H%M%S).log

# Terminal 7: Monitor connection states (UNIVERSAL)
watch -n 2 'echo "=== Active Connections ===" && ss -tan | grep :8080 | wc -l && echo "=== Connection States ===" && ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c'
```

### Phase 3: Resource Impact Analysis (UNIVERSAL)

> **🎯 OBJECTIVE**: Collect resource utilization data for comparing local vs GCP performance characteristics

#### 3.1 Container Resource Monitoring (UNIVERSAL)
```bash
# Continuous container monitoring with environment-specific logging
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}\t{{.PIDs}}" > container_stats_${ENV_TYPE}_$(date +%Y%m%d_%H%M%S).log &

# Monitor container logs for errors (UNIVERSAL)
docker logs -f flood-victim-server-single 2>&1 | tee victim_server_${ENV_TYPE}.log &
docker logs -f flood-attacker-client-A 2>&1 | tee attacker_client_${ENV_TYPE}.log &
```

#### 3.2 System-Level Impact Analysis (UNIVERSAL)
```bash
# Monitor system load and processes (UNIVERSAL)
watch -n 3 'echo "=== Load Average ===" && uptime && echo -e "\n=== Top Processes ===" && ps aux --sort=-%cpu | head -10 && echo -e "\n=== Memory Usage ===" && cat /proc/meminfo | grep -E "(MemTotal|MemFree|MemAvailable|Buffers|Cached)"'

# Monitor network interface statistics (UNIVERSAL)
watch -n 2 'echo "=== Network Interface Stats ===" && cat /proc/net/dev | grep -E "(eth0|ens)" && echo -e "\n=== TCP Stats ===" && cat /proc/net/snmp | grep Tcp'

# Log system metrics for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
while true; do
  echo "$(date),$ENV_TYPE,$(uptime | awk '{print $10}'),$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}'),$(ss -tan | grep :8080 | wc -l)" >> system_metrics_${ENV_TYPE}_$(date +%Y%m%d).csv
  sleep 10
done &
```

### Phase 4: Attack Effectiveness Measurement

#### 4.1 Success Rate Testing
```bash
# Test request success rate over time
for minute in {1..10}; do
  echo "=== Minute $minute Test ==="
  success=0
  failed=0
  total_time=0
  
  for test in {1..10}; do
    start_time=$(date +%s.%N)
    if timeout 10 curl -s -o /dev/null $TARGET_URL; then
      ((success++))
      end_time=$(date +%s.%N)
      response_time=$(echo "$end_time - $start_time" | bc)
      total_time=$(echo "$total_time + $response_time" | bc)
    else
      ((failed++))
    fi
    sleep 1
  done
  
  avg_time=$(echo "scale=3; $total_time / $success" | bc 2>/dev/null || echo "N/A")
  echo "Minute $minute: Success: $success/10, Failed: $failed/10, Avg Response Time: ${avg_time}s"
  echo "$(date): Success: $success/10, Failed: $failed/10, Avg Response Time: ${avg_time}s" >> success_rate.log
  sleep 50
done
```

#### 4.2 Throughput Testing (UNIVERSAL)
```bash
# Measure requests per second capacity for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)

echo "=== Throughput Test (Normal Load) - $ENV_TYPE ==="
ab -n 100 -c 5 $TARGET_URL/ > throughput_normal_${ENV_TYPE}.log

echo "=== Throughput Test (During Attack) - $ENV_TYPE ==="
ab -n 100 -c 5 $TARGET_URL/ > throughput_attack_${ENV_TYPE}.log
```

### Phase 5: Environment-Specific Advanced Monitoring

#### 5.1 GCP-Specific Monitoring (☁️ GCP ENVIRONMENT ONLY)
```bash
# Monitor GCP VM metrics (GCP ONLY)
INSTANCE_NAME=$(hostname)
ZONE=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4)

gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=$INSTANCE_NAME" --limit=50 --format="table(timestamp,severity,textPayload)"

# Monitor network metrics (GCP ONLY)
gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

#### 5.2 Local Environment Monitoring (🏠 LOCAL ENVIRONMENT ONLY)
```bash
# Monitor local Docker performance (LOCAL ONLY)
docker system df
docker system events --filter container=flood-victim-server-single &

# Monitor local network interfaces (LOCAL ONLY)
netstat -i
ss -tuln | grep :8080
```

### Phase 6: Performance Delta Analysis

> **🎯 CRITICAL**: This section helps you compare performance between LOCAL and GCP environments

#### 6.1 Data Consolidation (Run after both environments tested)
```bash
# Consolidate all collected data for comparison
echo "=== PERFORMANCE COMPARISON ANALYSIS ===" > performance_comparison_$(date +%Y%m%d_%H%M%S).txt

# Compare baseline performance
echo "\n=== BASELINE COMPARISON ===" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "LOCAL Environment:" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" baseline_*LOCAL*.log | awk -F: '{print $2}' | awk -F\| '{print $1}' | sort -n >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "\nGCP Environment:" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" baseline_*GCP*.log | awk -F: '{print $2}' | awk -F\| '{print $1}' | sort -n >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt

# Compare attack impact
echo "\n=== ATTACK IMPACT COMPARISON ===" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "LOCAL Attack Response Times:" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" http_flood_attack_LOCAL*.log | head -20 >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "\nGCP Attack Response Times:" >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" http_flood_attack_GCP*.log | head -20 >> performance_comparison_$(date +%Y%m%d_%H%M%S).txt
```

#### 6.2 Statistical Analysis
```bash
# Calculate statistical differences
cat > analyze_performance.sh << 'EOF'
#!/bin/bash
echo "=== STATISTICAL ANALYSIS ==="

# Calculate average baseline response times
local_avg=$(grep "Total:" baseline_*LOCAL*.log | awk -F: '{print $2}' | awk -F\| '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}')
gcp_avg=$(grep "Total:" baseline_*GCP*.log | awk -F: '{print $2}' | awk -F\| '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}')

echo "Average Baseline Response Time:"
echo "  LOCAL: ${local_avg}s"
echo "  GCP: ${gcp_avg}s"
echo "  Performance Delta: $(echo "scale=4; $gcp_avg - $local_avg" | bc)s"

# Calculate attack impact
local_attack_avg=$(grep "Total:" http_flood_attack_LOCAL*.log | head -20 | awk -F: '{print $2}' | awk -F\| '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}')
gcp_attack_avg=$(grep "Total:" http_flood_attack_GCP*.log | head -20 | awk -F: '{print $2}' | awk -F\| '{print $1}' | awk '{sum+=$1; count++} END {print sum/count}')

echo "\nAverage Attack Response Time:"
echo "  LOCAL: ${local_attack_avg}s"
echo "  GCP: ${gcp_attack_avg}s"
echo "  Attack Impact Delta: $(echo "scale=4; $gcp_attack_avg - $local_attack_avg" | bc)s"
EOF

chmod +x analyze_performance.sh
./analyze_performance.sh
```

## Expected Results and Environment Comparison

### 🏠 LOCAL ENVIRONMENT Expected Behavior

**Part A (Single-threaded Flask):**
- **Pre-attack**: Response time ~0.01-0.05 seconds
- **During attack**: Response time increases to 3-30+ seconds
- **CPU Usage**: Increases to 80-100% (may hit local machine limits)
- **Success Rate**: Drops to 10-30%
- **Recovery**: Immediate after attack stops
- **Local Characteristics**: Resource contention with host OS

**Part B (Multi-threaded Gunicorn):**
- **Pre-attack**: Response time ~0.01-0.05 seconds  
- **During attack**: Response time increases to 1-5 seconds
- **CPU Usage**: Distributed across workers, 60-90%
- **Success Rate**: Higher resilience, 50-80% success rate
- **Recovery**: Faster recovery due to worker isolation
- **Local Characteristics**: Limited by Docker resource allocation

### ☁️ GCP ENVIRONMENT Expected Behavior

**Part A (Single-threaded Flask):**
- **Pre-attack**: Response time ~0.01-0.1 seconds (may include network latency)
- **During attack**: Response time increases to 2-20+ seconds
- **CPU Usage**: Increases to 80-100% (dedicated VM resources)
- **Success Rate**: May be slightly better than local (10-40%)
- **Recovery**: Immediate after attack stops
- **Cloud Characteristics**: Dedicated CPU, potential network overhead

**Part B (Multi-threaded Gunicorn):**
- **Pre-attack**: Response time ~0.01-0.1 seconds
- **During attack**: Response time increases to 0.5-3 seconds (better performance)
- **CPU Usage**: Better distribution across VM cores, 50-80%
- **Success Rate**: Higher resilience, 60-90% success rate
- **Recovery**: Faster recovery, better resource isolation
- **Cloud Characteristics**: Dedicated resources, scalable architecture

### 📈 Expected Performance Deltas

**Baseline Performance:**
- **GCP typically 2-5x better** baseline performance due to dedicated resources
- **Network latency** may add 10-50ms to GCP responses
- **CPU performance** generally superior on GCP VMs

**Attack Resilience:**
- **GCP shows 20-40% better** attack resilience
- **Recovery time** typically 30-50% faster on GCP
- **Resource scaling** more effective in cloud environment

**Key Comparison Metrics:**
- **Response Time Delta**: GCP usually 10-30% faster
- **CPU Efficiency**: GCP 15-25% more efficient resource usage
- **Throughput**: GCP typically handles 20-40% more concurrent requests
- **Scalability**: GCP shows better performance under sustained load

## Quick Monitoring Setup (UNIVERSAL)

### Environment Setup
```bash
# Set target URL based on environment
# FOR LOCAL:
export TARGET_URL="http://localhost:8080"
# FOR GCP:
EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/external-ip -H "Metadata-Flavor: Google")
export TARGET_URL="http://$EXTERNAL_IP:8080"
```

### Quick Monitoring Commands (UNIVERSAL)
```bash
# Essential monitoring setup (run all in separate terminals)
watch -n 1 'curl -o /dev/null -s -w "%{time_total}s\n" $TARGET_URL'
watch -n 1 'docker stats --no-stream'
watch -n 2 'ss -tan | grep :8080 | wc -l'
watch -n 3 'uptime && free -h'

# Data logging for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
docker stats --format "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}}" > performance_data_${ENV_TYPE}_$(date +%Y%m%d_%H%M%S).csv &
```

## Troubleshooting

### Common Issues:
1. **Port 8080 not accessible**: Check firewall rules
2. **Attack not effective**: Increase connection count or reduce server resources
3. **Container exits**: Check Docker logs for errors

### GCP-Specific:
```bash
# Check GCP firewall rules
gcloud compute firewall-rules list --filter="name~'.*8080.*'"

# Update firewall if needed
gcloud compute firewall-rules create allow-port-8080 --allow tcp:8080 --source-ranges 0.0.0.0/0
```

## Cleanup
```bash
# Stop monitoring processes
pkill -f "watch"
pkill -f "docker stats"

# Stop containers
docker-compose down

# Remove logs (optional)
rm -f *.log *.csv
```