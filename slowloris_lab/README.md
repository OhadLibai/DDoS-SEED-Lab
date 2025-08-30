# Slowloris Attack Lab

## Overview

The Slowloris Attack Lab demonstrates connection exhaustion Distributed Denial of Service (DDoS) attacks that consume server resources through slow, persistent HTTP connections. This lab explores stealth attack techniques that achieve maximum impact with minimal bandwidth usage, providing hands-on experience with sophisticated connection-based attacks.

## Attack Mechanism

**Slowloris attacks** work by opening multiple connections to a web server and keeping them alive as long as possible by sending partial HTTP requests. This technique exhausts the server's connection pool without requiring high bandwidth, making it particularly effective against many web servers.

### Key Characteristics:
- **Low Bandwidth**: Requires minimal network resources from attacker
- **Connection Exhaustion**: Fills server connection pools with incomplete requests
- **Stealth Operation**: Difficult to detect due to low traffic volume
- **High Impact**: Can effectively DoS servers with limited attacker resources

## Lab Structure

### Part A: Basic Slowloris Attack
- **Target**: Apache web server with standard configuration
- **Attack Method**: Simple slow HTTP request transmission
- **Attack Intensity**: 1024 concurrent connections
- **Expected Behavior**: Gradual connection pool exhaustion
- **Learning Focus**: Understanding basic connection exhaustion principles

### Part B: Advanced Adaptive Slowloris
- **Target**: Apache web server (same as Part A)
- **Attack Method**: Intelligent adaptive attack with evasion techniques
- **Attack Intensity**: 1024 concurrent connections with dynamic adjustment
- **Expected Behavior**: More resilient attack with adaptive pacing
- **Learning Focus**: Advanced attack techniques and detection evasion

## Prerequisites

### Technical Requirements
- Docker and Docker Compose installed
- Available port 8080 on your system
- Basic command-line knowledge
- Google Cloud Platform account (for cloud deployment)

### Knowledge Prerequisites
- Understanding of HTTP protocol and TCP connections
- Basic web server architecture concepts
- Familiarity with connection handling and timeouts
- Elementary network monitoring knowledge

## Quick Start Guide

### Local Deployment

#### Deploy Part A (Basic Slowloris)
```bash
cd part_A
docker-compose up -d

# Verify deployment
curl http://localhost:8080
```

#### Deploy Part B (Advanced Adaptive)
```bash
cd part_B
docker-compose up -d

# Verify deployment
curl http://localhost:8080
```

### Google Cloud Platform Deployment

#### 1. VM Setup
```bash
# Create GCP VM instance
gcloud compute instances create slowloris-lab-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud

# SSH into instance
gcloud compute ssh slowloris-lab-vm --zone=us-central1-a

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

#### 2. Configure Firewall
```bash
# Allow HTTP traffic on port 8080
gcloud compute firewall-rules create allow-slowloris-lab \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow Slowloris Lab traffic"
```

#### 3. Deploy Lab
```bash
# Install git
sudo apt update
sudo apt install git -y
# Clone repository on GCP VM
git clone <repository-url>
cd DDoS-SEED-lab/slowloris_lab

# Deploy chosen part
cd part_A  # or part_B
docker-compose up -d
```

## Lab Components

### 1. Target Server (Apache)
Configured Apache web server that serves as the attack target:
- Standard Apache configuration with connection limits
- Server status module enabled for monitoring
- Runs on port 80 inside container (mapped to 8080 on host)
- Configured with typical production connection handling

### 2. Attack Scripts

#### Part A: Basic Slowloris (`slowloris_attack.py`)
- Simple implementation of slow HTTP request transmission
- Maintains multiple concurrent connections
- Sends incomplete HTTP headers at slow intervals
- Designed for educational demonstration of the core concept

#### Part B: Advanced Adaptive (`advanced_slowloris_attack.py`)
- Intelligent attack adaptation based on server responses
- Dynamic connection management and pacing
- Evasion techniques to avoid detection
- Adaptive sleep intervals and request patterns

### 3. Container Architecture

#### Part A Configuration:
- **Victim**: Apache web server with standard settings
- **Attacker**: Basic Slowloris with 1024 connections
- **Expected Impact**: Connection pool exhaustion over time

#### Part B Configuration:
- **Victim**: Same Apache server configuration
- **Attacker**: Advanced adaptive attack with intelligent pacing
- **Expected Impact**: More sustained and resilient attack

## Performance Monitoring and Analysis

### Monitoring Setup
This lab includes comprehensive connection and performance monitoring capabilities. Refer to the detailed monitoring guide for complete instructions:

**📋 [Slowloris Monitoring Guide](../SLOWLORIS_MONITORING_GUIDE.md)**

### Key Metrics to Monitor

#### Connection Analysis:
- **Active Connections**: Number of established connections to port 8080
- **Connection States**: Distribution of TCP connection states
- **Connection Duration**: How long connections remain active
- **Apache Workers**: Busy vs idle worker processes

#### Server Performance:
- **Response Time**: Normal vs degraded response times
- **New Connection Success**: Ability to establish new connections
- **Service Availability**: Overall server responsiveness
- **Connection Pool Status**: Apache worker utilization

#### Attack Effectiveness:
- **Connection Persistence**: How long attack connections survive
- **Resource Consumption**: Server resource usage patterns
- **Legitimate User Impact**: Effect on normal user connections
- **Detection Evasion**: Stealth characteristics of the attack

### Quick Monitoring Commands

```bash
# Monitor active connections
watch -n 2 'ss -tan | grep :8080 | wc -l'

# Monitor connection states
watch -n 3 'ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c'

# Monitor Apache server status
watch -n 5 'curl -s http://localhost:8080/server-status?auto | grep -E "(BusyWorkers|IdleWorkers)"'

# Test legitimate user impact
timeout 10 curl -o /dev/null -s -w "Response: %{time_total}s | HTTP: %{http_code}\n" http://localhost:8080
```

## Expected Attack Progression

### Part A (Basic Slowloris) Timeline:
- **0-60s**: Initial connection establishment phase
- **60-180s**: Connection pool gradually fills
- **180-300s**: Server connection limits approached
- **300s+**: New connections refused, DoS achieved

### Part B (Advanced Adaptive) Timeline:
- **0-90s**: Intelligent connection establishment with adaptive pacing
- **90-240s**: Dynamic adjustment based on server behavior
- **240-600s**: Sustained attack with evasion techniques
- **600s+**: Long-term persistence with minimal detection

### Key Attack Indicators:
1. **Gradual Connection Increase**: Steady rise in established connections
2. **Response Degradation**: Increasing response times for legitimate requests
3. **Worker Exhaustion**: All Apache workers become busy
4. **Connection Refusal**: New connections timeout or are refused

## Container Management

### Useful Commands

```bash
# View running containers
docker-compose ps

# View attack progress
docker-compose logs attacker

# View Apache server logs
docker-compose logs victim

# Stop the lab
docker-compose down

# Restart with fresh state
docker-compose down && docker-compose up -d
```

### Monitoring Attack Progress

```bash
# Monitor attack container output
docker logs -f slowloris-attacker-client

# Check Apache access logs
docker exec apache-victim tail -f /var/log/apache2/access.log

# Monitor Apache error logs
docker exec apache-victim tail -f /var/log/apache2/error.log
```

## Advanced Attack Analysis

### Connection Pattern Analysis
```bash
# Analyze connection establishment patterns
tcpdump -i any -nn -s 0 'port 8080 and tcp[tcpflags] & tcp-syn != 0' > connection_analysis.log

# Monitor partial HTTP requests
tcpdump -i any -nn -A 'port 8080 and length < 100' > partial_requests.log
```

### Server Behavior Analysis
```bash
# Track Apache worker process behavior
watch -n 5 'ps aux | grep apache2 | grep -v grep | wc -l'

# Monitor file descriptor usage
watch -n 3 'lsof | grep :8080 | wc -l'

# Check connection limits
cat /proc/sys/net/core/somaxconn
```

## Expected Learning Outcomes

### Understanding Stealth Attacks
- Comprehend how low-bandwidth attacks can achieve high impact
- Understand the difference between volumetric and connection-based attacks
- Learn about attack persistence and evasion techniques

### Connection Management Analysis
- Analyze how web servers handle connection pools
- Understand the impact of connection timeouts and limits
- Observe connection state transitions during attacks

### Detection and Mitigation Insights
- Identify characteristics that distinguish attack from legitimate traffic
- Understand the challenges of detecting stealth attacks
- Learn about adaptive attack techniques that evade simple defenses

### Cloud vs Local Performance
- Compare attack effectiveness between local Docker and GCP deployment
- Analyze how cloud infrastructure affects connection handling
- Evaluate scalability and resource differences in different environments

## Troubleshooting

### Common Issues
- **Attack not effective**: Check Apache MaxRequestWorkers configuration
- **Connections dropping quickly**: Verify KeepAlive timeout settings
- **Port conflicts**: Ensure port 8080 is available

### Apache Configuration Check
```bash
# Check Apache configuration
docker exec apache-victim apache2ctl -S

# View current settings
docker exec apache-victim grep -E "(MaxRequestWorkers|KeepAlive)" /etc/apache2/apache2.conf
```

### Attack Debugging
```bash
# Check attack script output
docker logs slowloris-attacker-client

# Monitor attack connection count
docker exec apache-victim ss -tan | grep :8080 | wc -l

# Verify attack script is running
docker exec slowloris-attacker-client ps aux | grep python
```

## Educational Integration

### SEED Lab Connections
This lab complements other SEED cybersecurity exercises:
- **Network Security**: Understanding TCP connection management
- **Web Security**: Server-side resource management and protection
- **System Security**: Process and connection monitoring techniques

### Defensive Learning Perspective
While demonstrating attack techniques, this lab emphasizes:
- **Understanding attack vectors** to develop effective countermeasures
- **Connection monitoring** for attack detection and prevention
- **Server hardening** through configuration analysis
- **Incident response** through attack pattern recognition

## Advanced Experiments

### Custom Attack Variations
```bash
# Modify attack parameters in docker-compose.yml
# Test different connection counts and timing patterns

# Implement custom attack scripts
# Create variations with different evasion techniques

# Test against different server configurations
# Modify Apache settings to test various defensive measures
```

### Detection Experiments
- Implement connection monitoring scripts
- Develop attack signature detection
- Test rate limiting and connection filtering
- Analyze attack traffic patterns

## Data Collection and Analysis

### Performance Metrics
Students should focus on collecting and analyzing:
- Connection count progression over time
- Response time degradation patterns
- Server resource utilization during attacks
- Attack persistence and recovery characteristics

### Comparative Analysis Framework
- **Environment Comparison**: Local Docker vs GCP connection handling
- **Attack Variation**: Basic vs advanced attack effectiveness
- **Server Configuration**: Impact of different Apache settings
- **Detection Analysis**: Identifying attack signatures in connection patterns

## Safety Considerations

### Controlled Environment Usage
- Deploy only in dedicated laboratory environments
- Monitor system resources to prevent overload
- Use isolated networks when possible
- Ensure proper cleanup after experiments

### Educational Ethics
- Focus on defensive cybersecurity applications
- Understand attacks to build better protections
- Respect system resources and shared computing environments
- Follow institutional policies for security research

---

**📋 For detailed monitoring procedures, refer to [Slowloris Monitoring Guide](../SLOWLORIS_MONITORING_GUIDE.md)**

**🏠 Return to [Main Lab Overview](../README.md)**
