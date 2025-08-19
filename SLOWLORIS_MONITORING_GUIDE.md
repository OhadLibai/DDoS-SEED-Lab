# Slowloris Lab - Performance Monitoring Guide

## Overview
This guide provides comprehensive instructions for monitoring Slowloris attacks in both Part A (basic attack) and Part B (advanced adaptive attack) deployments. **The guide covers both LOCAL DOCKER and GOOGLE CLOUD PLATFORM (GCP) environments to enable performance comparison between connection exhaustion attacks in different deployment scenarios.**

## Environment Setup

### 🏠 Local Environment Prerequisites
- Docker and Docker Compose installed on local machine
- Available port 8080 on local system
- Basic Apache/Nginx web server knowledge
- Understanding of TCP connection states

### ☁️ GCP Environment Prerequisites
- GCP VM instance with Docker and Docker Compose installed
- SSH access to the GCP instance
- Firewall rules allowing port 8080 traffic
- Apache/Nginx web server knowledge
- Understanding of TCP connection states

## Environment-Specific Setup

### 🏠 LOCAL ENVIRONMENT Setup

```bash
# Navigate to the lab directory
cd DDoS-SEED-lab/slowloris_lab

# Deploy Part A (Basic Slowloris)
cd part_A
docker-compose up -d

# OR Deploy Part B (Advanced Adaptive Slowloris)
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
cd DDoS-SEED-lab/slowloris_lab

# Deploy Part A (Basic Slowloris)
cd part_A
docker-compose up -d

# OR Deploy Part B (Advanced Adaptive Slowloris)
cd part_B
docker-compose up -d

# Get GCP external IP and set target URL
EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/external-ip -H "Metadata-Flavor: Google")
export TARGET_URL="http://$EXTERNAL_IP:8080"
echo "GCP target: $TARGET_URL"

# Verify Apache server status endpoint
curl -s $TARGET_URL/server-status?auto | head -5
```

## Performance Monitoring Methodology

### 📄 UNIVERSAL COMMANDS (Same for Both Environments)

The following commands work identically in both local and GCP environments. **Use $TARGET_URL variable** (set during environment setup) for consistent monitoring.

### Phase 1: Pre-Attack Connection Baseline (60 seconds)

> **🎯 OBJECTIVE**: Establish connection handling baseline for comparison between local vs GCP environments

#### 1.1 Apache Server Connection Monitoring (UNIVERSAL)
```bash
# Terminal 1: Monitor Apache connection pool
watch -n 2 'echo "=== Apache Server Status ===" && curl -s $TARGET_URL/server-status?auto | grep -E "(Total Accesses|Total kBytes|CPULoad|Uptime|ReqPerSec|BytesPerSec|BytesPerReq|BusyWorkers|IdleWorkers)" && echo -e "\n=== Active Connections ===" && ss -tan | grep :8080 | wc -l'

# Terminal 2: Monitor detailed connection states (UNIVERSAL)
watch -n 1 'echo "=== Connection States Distribution ===" && ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c && echo -e "\n=== Total Connections by State ===" && ss -tan state all | grep :8080 | wc -l'

# Terminal 3: Monitor Apache logs (UNIVERSAL)
# Note: Log paths may vary between environments
docker logs -f apache-victim 2>&1 | grep -E "(error|access)" &
```

#### 1.2 Baseline Data Collection for Environment Comparison (UNIVERSAL)
```bash
# Collect baseline connection metrics
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
echo "=== SLOWLORIS BASELINE COLLECTION START ===" > slowloris_baseline_$(date +%Y%m%d_%H%M%S).log
echo "Environment: $ENV_TYPE" >> slowloris_baseline_$(date +%Y%m%d_%H%M%S).log
echo "Target URL: $TARGET_URL" >> slowloris_baseline_$(date +%Y%m%d_%H%M%S).log

# Test normal response times and connection handling
for i in {1..30}; do
  echo "$ENV_TYPE Baseline Test $i: $(date)"
  curl -o /dev/null -s -w "Connect:%{time_connect}s|TTFB:%{time_starttransfer}s|Total:%{time_total}s|HTTP:%{http_code}\n" $TARGET_URL
  sleep 2
done > slowloris_baseline_${ENV_TYPE}_$(date +%Y%m%d_%H%M%S).log

# Test concurrent connection capacity (baseline)
ab -n 50 -c 10 $TARGET_URL/ > baseline_capacity_${ENV_TYPE}.log
```

### Phase 2: Attack Pattern Monitoring (UNIVERSAL)

> **🎯 OBJECTIVE**: Monitor Slowloris attack progression and collect connection exhaustion data for environment comparison

#### 2.1 Slowloris Attack Pattern Detection (UNIVERSAL)
```bash
# Terminal 4: Monitor attack connection establishment
watch -n 1 'echo "=== Connection Timeline ===" && ss -tan | grep :8080 | grep -E "(SYN-SENT|SYN-RECV|ESTABLISHED|CLOSE-WAIT)" | wc -l && echo "=== Partial HTTP Requests ===" && netstat -an | grep :8080 | grep ESTABLISHED | wc -l'

# Terminal 5: Monitor slow connection behavior (UNIVERSAL)
watch -n 3 'echo "=== Long-lived Connections ===" && ss -tan | grep :8080 | grep ESTABLISHED && echo -e "\n=== Connection Duration Analysis ===" && ss -tano | grep :8080 | grep ESTABLISHED | head -10'
```

#### 2.2 Attack Impact Data Collection (UNIVERSAL)
```bash
# Terminal 6: Test legitimate user impact for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
for minute in {1..15}; do
  echo "=== $ENV_TYPE Minute $minute Impact Test ==="
  start_time=$(date +%s)
  
  # Attempt normal connection
  if timeout 15 curl -s -o /dev/null -w "Response Time: %{time_total}s\n" $TARGET_URL; then
    echo "SUCCESS: Connection established in minute $minute"
  else
    echo "FAILED: Connection timeout/refused in minute $minute"
  fi
  
  # Test multiple concurrent connections
  success_count=0
  for test in {1..5}; do
    if timeout 10 curl -s -o /dev/null $TARGET_URL; then
      ((success_count++))
    fi
  done
  
  echo "$ENV_TYPE Minute $minute: $success_count/5 successful connections"
  echo "$(date): $ENV_TYPE Minute $minute: $success_count/5 successful connections" >> slowloris_impact_${ENV_TYPE}_$(date +%Y%m%d).log
  
  sleep 57  # Sleep for remainder of minute
done
```

### Phase 3: Connection Pool Exhaustion Monitoring

#### 3.1 Apache Worker/Connection Pool Analysis
```bash
# Monitor Apache worker processes and connection limits
watch -n 2 'echo "=== Apache Process Count ===" && ps aux | grep apache2 | grep -v grep | wc -l && echo -e "\n=== Apache Configuration Limits ===" && curl -s http://localhost:8080/server-status | grep -E "(Server MPM|Max|workers)" && echo -e "\n=== Current Workers Status ===" && curl -s http://localhost:8080/server-status?auto | grep -E "(BusyWorkers|IdleWorkers)"'

# Monitor connection queue and backlog
watch -n 1 'echo "=== Listen Queue ===" && ss -tln | grep :8080 && echo -e "\n=== TCP Connection Metrics ===" && cat /proc/net/sockstat | grep TCP'
```

#### 3.2 Attack-Specific Connection Monitoring
```bash
# Track slow/partial HTTP requests characteristic of Slowloris
tcpdump -i any -nn -s 0 -A 'port 8080 and tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0' > slowloris_tcp_analysis.log &

# Monitor connection establishment vs completion rates
while true; do
  established=$(ss -tan | grep :8080 | grep ESTABLISHED | wc -l)
  syn_recv=$(ss -tan | grep :8080 | grep SYN-RECV | wc -l)
  close_wait=$(ss -tan | grep :8080 | grep CLOSE-WAIT | wc -l)
  
  echo "$(date): ESTABLISHED:$established SYN-RECV:$syn_recv CLOSE-WAIT:$close_wait"
  echo "$(date): ESTABLISHED:$established SYN-RECV:$syn_recv CLOSE-WAIT:$close_wait" >> connection_states.log
  sleep 5
done &
```

### Phase 4: Resource Impact and Server Degradation

#### 4.1 Memory and File Descriptor Monitoring
```bash
# Monitor file descriptor usage (critical for connection attacks)
watch -n 2 'echo "=== File Descriptors ===" && lsof | grep :8080 | wc -l && echo "=== System FD Limits ===" && cat /proc/sys/fs/file-nr && echo -e "\n=== Per-Process Limits ===" && cat /proc/$(pidof apache2 | cut -d" " -f1)/limits | grep "open files"'

# Monitor memory usage patterns
watch -n 3 'echo "=== Memory Usage ===" && free -h && echo -e "\n=== Apache Memory Usage ===" && ps aux | grep apache2 | grep -v grep | awk "{sum+=\$6} END {print \"Total Apache Memory: \" sum/1024 \" MB\"}"'
```

#### 4.2 Attack Progression Timeline
```bash
# Create detailed attack progression log
cat > slowloris_progression.sh << 'EOF'
#!/bin/bash
start_time=$(date +%s)
while true; do
  current_time=$(date +%s)
  elapsed=$((current_time - start_time))
  
  # Get connection statistics
  total_connections=$(ss -tan | grep :8080 | wc -l)
  established=$(ss -tan | grep :8080 | grep ESTABLISHED | wc -l)
  
  # Test server responsiveness
  response_time=$(timeout 5 curl -o /dev/null -s -w "%{time_total}" $TARGET_URL 2>/dev/null || echo "TIMEOUT")
  
  # Check Apache workers
  busy_workers=$(curl -s $TARGET_URL/server-status?auto 2>/dev/null | grep "BusyWorkers:" | cut -d: -f2 || echo "N/A")
  idle_workers=$(curl -s $TARGET_URL/server-status?auto 2>/dev/null | grep "IdleWorkers:" | cut -d: -f2 || echo "N/A")
  
  echo "T+${elapsed}s: Connections:$total_connections Est:$established Response:${response_time}s Busy:$busy_workers Idle:$idle_workers"
  echo "T+${elapsed}s: Connections:$total_connections Est:$established Response:${response_time}s Busy:$busy_workers Idle:$idle_workers" >> attack_progression.log
  
  sleep 10
done &
EOF

chmod +x slowloris_progression.sh
./slowloris_progression.sh
```

### Phase 5: Advanced Attack Analysis (Part B Only)

#### 5.1 Adaptive Attack Behavior Monitoring
```bash
# Monitor adaptive attack behavior changes
watch -n 5 'echo "=== Attack Adaptation Analysis ===" && docker logs flood-attacker-client-B 2>&1 | tail -10 | grep -E "(connections|pace|dropped)" && echo -e "\n=== Connection Pattern Changes ===" && ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c'

# Track attack parameter adjustments
docker logs -f flood-attacker-client-B 2>&1 | grep -E "(Pace|connections|Dropped)" | tee adaptive_attack_log.txt &
```

#### 5.2 Stealth and Evasion Monitoring
```bash
# Monitor attack stealth characteristics
watch -n 10 'echo "=== Bandwidth Usage ===" && cat /proc/net/dev | grep -E "(eth0|ens)" | awk "{print \"RX bytes: \" \$2/1024/1024 \" MB, TX bytes: \" \$10/1024/1024 \" MB\"}" && echo -e "\n=== Connection Variance ===" && ss -tan | grep :8080 | grep ESTABLISHED | wc -l'

# Analyze request patterns for detection evasion
tcpdump -i any -nn -A 'port 8080 and length < 100' | head -50 > stealth_analysis.log &
```

### Phase 6: Environment-Specific Advanced Monitoring

#### 6.1 GCP-Specific Monitoring (☁️ GCP ENVIRONMENT ONLY)
```bash
# Monitor GCP VM network performance (GCP ONLY)
INSTANCE_NAME=$(hostname)
ZONE=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google" | cut -d/ -f4)
gcloud compute instances describe your-vm-name --zone=your-zone --format="get(networkInterfaces[0].accessConfigs[0].natIP)"

# Monitor GCP logging for connection events
gcloud logging read "resource.type=gce_instance AND textPayload:\"connection\"" --limit=50 --format="table(timestamp,severity,textPayload)"

# Set up GCP monitoring alerts
gcloud alpha monitoring policies create --policy-from-file=slowloris_policy.yaml
```

#### 6.2 Custom GCP Metrics Collection
```bash
# Create GCP-specific monitoring script
cat > gcp_slowloris_metrics.sh << 'EOF'
#!/bin/bash
while true; do
  timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  # Connection metrics
  total_conn=$(ss -tan | grep :8080 | wc -l)
  established_conn=$(ss -tan | grep :8080 | grep ESTABLISHED | wc -l)
  
  # Server metrics
  cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
  memory_usage=$(free | grep Mem | awk '{printf "%.2f", $3/$2 * 100.0}')
  
  # Apache metrics
  apache_procs=$(ps aux | grep apache2 | grep -v grep | wc -l)
  
  echo "$timestamp,TotalConn:$total_conn,EstConn:$established_conn,CPU:$cpu_usage%,Mem:$memory_usage%,Apache:$apache_procs"
  
  # Send to GCP monitoring (requires Cloud Monitoring API setup)
  # gcloud logging write slowloris-attack "$timestamp,TotalConn:$total_conn,EstConn:$established_conn,CPU:$cpu_usage%,Mem:$memory_usage%,Apache:$apache_procs"
  
  sleep 15
done > gcp_slowloris_metrics.log &
EOF

chmod +x gcp_slowloris_metrics.sh
./gcp_slowloris_metrics.sh
```

## Expected Attack Progression and Results

### Part A (Basic Slowloris) Timeline:
- **0-30s**: Normal connection establishment, building connection pool
- **30-120s**: Connection pool gradually fills, response times increase
- **120-300s**: Server connection limit reached, new connections refused
- **300s+**: Complete denial of service for new connections

### Part B (Advanced Adaptive Slowloris) Timeline:
- **0-60s**: Intelligent connection establishment with adaptive pacing
- **60-180s**: Dynamic adjustment based on server responses
- **180-450s**: Sustained attack with evasion techniques
- **450s+**: Optimized attack maintaining maximum impact with minimal resources

### Key Indicators of Successful Attack:
1. **Connection Pool Exhaustion**: BusyWorkers approaches MaxRequestWorkers
2. **Response Degradation**: Normal requests timeout or take >30 seconds
3. **New Connection Refusal**: "Connection refused" errors for legitimate users
4. **Sustained Impact**: Attack maintains effectiveness over extended periods

### Phase 7: Performance Delta Analysis

> **🎯 CRITICAL**: This section helps you compare Slowloris attack effectiveness between LOCAL and GCP environments

#### 7.1 Connection Data Consolidation (Run after both environments tested)
```bash
# Consolidate connection data for environment comparison
echo "=== SLOWLORIS PERFORMANCE COMPARISON ANALYSIS ===" > slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt

# Compare baseline connection handling
echo "\n=== BASELINE CONNECTION COMPARISON ===" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "LOCAL Environment Baseline:" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" slowloris_baseline_*LOCAL*.log | awk -F: '{print $2}' | awk -F\| '{print $3}' | sort -n >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "\nGCP Environment Baseline:" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "Total:" slowloris_baseline_*GCP*.log | awk -F: '{print $2}' | awk -F\| '{print $3}' | sort -n >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt

# Compare attack impact
echo "\n=== ATTACK IMPACT COMPARISON ===" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "LOCAL Attack Success Rate:" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "SUCCESS\|FAILED" slowloris_impact_LOCAL*.log | tail -15 >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
echo "\nGCP Attack Success Rate:" >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
grep "SUCCESS\|FAILED" slowloris_impact_GCP*.log | tail -15 >> slowloris_comparison_$(date +%Y%m%d_%H%M%S).txt
```

#### 7.2 Connection Exhaustion Analysis
```bash
# Create connection analysis script
cat > analyze_slowloris_performance.sh << 'EOF'
#!/bin/bash
echo "=== SLOWLORIS STATISTICAL ANALYSIS ==="

# Calculate baseline connection times
local_baseline=$(grep "Total:" slowloris_baseline_*LOCAL*.log | awk -F: '{print $2}' | awk -F\| '{print $3}' | awk '{sum+=$1; count++} END {print sum/count}')
gcp_baseline=$(grep "Total:" slowloris_baseline_*GCP*.log | awk -F: '{print $2}' | awk -F\| '{print $3}' | awk '{sum+=$1; count++} END {print sum/count}')

echo "Average Baseline Connection Time:"
echo "  LOCAL: ${local_baseline}s"
echo "  GCP: ${gcp_baseline}s"
echo "  Connection Delta: $(echo "scale=4; $gcp_baseline - $local_baseline" | bc)s"

# Calculate attack success rates
local_success=$(grep "SUCCESS" slowloris_impact_LOCAL*.log | wc -l)
local_total=$(grep "Minute" slowloris_impact_LOCAL*.log | wc -l)
gcp_success=$(grep "SUCCESS" slowloris_impact_GCP*.log | wc -l)
gcp_total=$(grep "Minute" slowloris_impact_GCP*.log | wc -l)

local_success_rate=$(echo "scale=2; $local_success * 100 / $local_total" | bc)
gcp_success_rate=$(echo "scale=2; $gcp_success * 100 / $gcp_total" | bc)

echo "\nAttack Success Rate (% of successful connections during attack):"
echo "  LOCAL: $local_success_rate% ($local_success/$local_total)"
echo "  GCP: $gcp_success_rate% ($gcp_success/$gcp_total)"
echo "  Resilience Delta: $(echo "scale=2; $gcp_success_rate - $local_success_rate" | bc)%"
EOF

chmod +x analyze_slowloris_performance.sh
./analyze_slowloris_performance.sh
```

## Environment Comparison Results

### 🏠 LOCAL ENVIRONMENT Expected Behavior

**Part A (Basic Slowloris):**
- **Connection Build-up**: 0-120s gradual connection accumulation
- **Pool Exhaustion**: 120-300s, reaching local Docker connection limits
- **Impact**: Severe degradation, 10-30% success rate for new connections
- **Recovery**: 30-60s after attack stops
- **Local Characteristics**: Limited by Docker networking and host resources

**Part B (Advanced Adaptive):**
- **Intelligent Adaptation**: 0-180s with dynamic pacing adjustments
- **Sustained Attack**: 180-600s maintaining connection exhaustion
- **Impact**: More efficient attack, 5-20% success rate
- **Recovery**: 60-120s due to persistent connections
- **Local Characteristics**: May hit Docker container limits

### ☁️ GCP ENVIRONMENT Expected Behavior

**Part A (Basic Slowloris):**
- **Connection Build-up**: 0-180s slower but more stable accumulation
- **Pool Exhaustion**: 180-450s, higher connection capacity
- **Impact**: Moderate degradation, 20-40% success rate
- **Recovery**: 15-30s with better resource cleanup
- **Cloud Characteristics**: Higher connection limits, better isolation

**Part B (Advanced Adaptive):**
- **Intelligent Adaptation**: 0-240s with more sophisticated evasion
- **Sustained Attack**: 240-900s extended effectiveness
- **Impact**: Highly effective, 10-25% success rate
- **Recovery**: 30-60s with automatic resource scaling
- **Cloud Characteristics**: Better handling of persistent connections

### 📈 Expected Performance Deltas

**Connection Handling:**
- **GCP typically handles 2-4x more** concurrent connections
- **Attack duration** 40-60% longer on GCP before full exhaustion
- **Recovery time** 50-70% faster on GCP

**Attack Effectiveness:**
- **Local environment** more vulnerable to connection exhaustion
- **GCP shows 15-30% better** resilience to Slowloris attacks
- **Advanced attacks** more effective on GCP due to longer persistence

**Key Comparison Metrics:**
- **Connection Capacity**: GCP typically 2-4x higher limits
- **Attack Duration**: GCP sustains attacks 40-60% longer
- **Recovery Efficiency**: GCP 50-70% faster cleanup
- **Detection Resistance**: Advanced attacks 25-40% more stealthy on GCP

## Data Analysis Commands

### Connection Analysis (UNIVERSAL)
```bash
# Analyze connection patterns for environment comparison
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
grep "ESTABLISHED" connection_states.log | wc -l
awk -F: '{print $2}' attack_progression.log | grep -o 'Connections:[0-9]*' | cut -d: -f2 | sort -n | tail -1

# Calculate attack efficiency with environment context
total_time=$(tail -1 attack_progression.log | grep -o 'T+[0-9]*' | cut -d+ -f2 | cut -ds -f1)
max_connections=$(grep -o 'Est:[0-9]*' attack_progression.log | cut -d: -f2 | sort -n | tail -1)
echo "$ENV_TYPE Peak connections: $max_connections over ${total_time}s"
```

### Performance Impact Measurement (UNIVERSAL)
```bash
# Calculate service degradation with environment awareness
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
baseline_response=$(awk '{sum+=$1; count++} END {print sum/count}' slowloris_baseline_${ENV_TYPE}*.log)
echo "$ENV_TYPE Baseline average response time: $baseline_response seconds"

# Measure attack success rate
success_rate=$(grep "SUCCESS" slowloris_impact_${ENV_TYPE}*.log | wc -l)
total_tests=$(grep "Minute" slowloris_impact_${ENV_TYPE}*.log | wc -l)
echo "$ENV_TYPE Attack effectiveness: Blocked $(($total_tests - $success_rate))/$total_tests connection attempts"
echo "$ENV_TYPE Success rate: $(echo "scale=2; $success_rate * 100 / $total_tests" | bc)%"
```

## Troubleshooting

### Common Issues:
1. **Attack not effective**: Check Apache MaxRequestWorkers configuration
2. **Connections dropping too quickly**: Adjust KeepAlive timeout settings
3. **Monitoring tools interfering**: Use separate monitoring instances

### Apache Configuration Check:
```bash
# Check current Apache configuration
apache2ctl -S
grep -E "(MaxRequestWorkers|KeepAlive)" /etc/apache2/apache2.conf
```

### GCP-Specific Troubleshooting:
```bash
# Check GCP firewall and network settings
gcloud compute firewall-rules list --filter="name~'.*80.*'"
gcloud compute networks describe default
```

## Cleanup and Log Analysis

```bash
# Stop all monitoring processes
pkill -f "tcpdump"
pkill -f "watch"
pkill -f "slowloris_progression"

# Analyze collected data
echo "=== Attack Summary ==="
echo "Total duration: $(tail -1 attack_progression.log | grep -o 'T+[0-9]*')"
echo "Peak connections: $(grep -o 'Est:[0-9]*' attack_progression.log | cut -d: -f2 | sort -n | tail -1)"
echo "Server availability: $(grep SUCCESS slowloris_impact.log | wc -l)/$(grep Minute slowloris_impact.log | wc -l)"

# Clean up containers and logs
docker-compose down
rm -f *.log *.txt
```

## Security and Ethical Notes

⚠️ **WARNING**: This lab is for educational purposes only. Slowloris attacks can cause significant service disruption. Only use in controlled environments with proper authorization.

- Always run in isolated lab environments
- Never target systems you don't own
- Follow responsible disclosure practices
- Use for defensive security training only