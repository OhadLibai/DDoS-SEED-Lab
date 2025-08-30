# HTTP/2 Slowloris Attack Lab

## Overview

The HTTP/2 Slowloris Attack Lab demonstrates advanced stream exhaustion Distributed Denial of Service (DDoS) attacks that exploit HTTP/2 multiplexing to overwhelm servers through slow, persistent streams. This lab explores stealth attack techniques that achieve maximum impact with minimal bandwidth usage, providing hands-on experience with sophisticated HTTP/2 stream-based attacks.

## Attack Mechanism

**HTTP/2 Slowloris attacks** work by opening multiple HTTP/2 connections to a web server and creating numerous slow streams within each connection, keeping them alive as long as possible by sending partial HTTP/2 frames. This technique exhausts the server's stream pools and connection resources without requiring high bandwidth, making it particularly effective against HTTP/2 servers.

### Key Characteristics:
- **Low Bandwidth**: Requires minimal network resources from attacker
- **Stream Exhaustion**: Fills server HTTP/2 stream pools with incomplete requests
- **Multiplexing Abuse**: Exploits HTTP/2's multiplexing feature for efficiency
- **Stealth Operation**: Difficult to detect due to low traffic volume and legitimate HTTP/2 appearance
- **High Impact**: Can effectively DoS HTTP/2 servers with limited attacker resources

## Lab Structure

### Part A: Basic HTTP/2 Slowloris Attack
- **Target**: Quart HTTP/2 server with single-worker configuration
- **Attack Method**: Simple slow HTTP/2 stream transmission with partial frames
- **Attack Intensity**: 256 concurrent connections with 10 streams each
- **Expected Behavior**: Gradual HTTP/2 stream pool exhaustion
- **Learning Focus**: Understanding basic HTTP/2 stream exhaustion principles

### Part B: Advanced Adaptive HTTP/2 Slowloris
- **Target**: Multi-worker Quart HTTP/2 server
- **Attack Method**: Intelligent adaptive HTTP/2 attack with stealth features and evasion techniques
- **Attack Intensity**: 100 concurrent connections with 25 streams each, adaptive adjustment
- **Expected Behavior**: More resilient attack with adaptive pacing and stealth features
- **Learning Focus**: Advanced HTTP/2 attack techniques and detection evasion

## Prerequisites

### Technical Requirements
- Docker and Docker Compose installed
- Available port 8080 on your system
- Basic command-line knowledge
- Google Cloud Platform account (for cloud deployment)

### Knowledge Prerequisites
- Understanding of HTTP/1.1 and HTTP/2 protocols
- Basic web server architecture concepts (async processing, multiplexing)
- Familiarity with HTTP/2 stream handling and connection management
- Elementary network monitoring knowledge

## Quick Start Guide

### Local Deployment

#### Deploy Part A (Basic Slowloris)
```bash
cd part_A
docker-compose up -d

# Verify HTTP/2 deployment
curl --http2-prior-knowledge http://localhost:8080
```

#### Deploy Part B (Advanced Adaptive)
```bash
cd part_B
docker-compose up -d

# Verify HTTP/2 deployment
curl --http2-prior-knowledge http://localhost:8080
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
# Allow HTTP/2 traffic on port 8080
gcloud compute firewall-rules create allow-http2-slowloris-lab \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP/2 Slowloris Lab traffic"
```

#### 3. Deploy Lab
```bash
# Clone repository on GCP VM
git clone <repository-url>
cd DDoS-SEED-lab/slowloris_lab

# Deploy chosen part
cd part_A  # or part_B
docker-compose up -d
```

## Lab Components

### 1. Target Server (Quart HTTP/2)
Configured Quart HTTP/2 web server that serves as the attack target:
- Hypercorn ASGI server with HTTP/2 multiplexing support
- Async processing with configurable worker counts
- Runs on port 80 inside container (mapped to 8080 on host)
- Configured with typical HTTP/2 stream handling

### 2. Attack Scripts

#### Part A: Basic HTTP/2 Slowloris (`slowloris.py`)
- Simple implementation of slow HTTP/2 stream transmission
- Maintains multiple concurrent HTTP/2 connections with multiple streams each
- Sends incomplete HTTP/2 frames at slow intervals
- Designed for educational demonstration of HTTP/2 stream exhaustion

#### Part B: Advanced Adaptive HTTP/2 (`advanced_slowloris.py`)
- Intelligent attack adaptation based on HTTP/2 server responses
- Dynamic connection and stream management with adaptive pacing
- Stealth techniques and evasion to avoid detection
- Adaptive sleep intervals and HTTP/2 frame patterns

### 3. Container Architecture

#### Part A Configuration:
- **Victim**: Single-worker Quart HTTP/2 server
- **Attacker**: Basic HTTP/2 Slowloris with 256 connections and 10 streams each
- **Expected Impact**: HTTP/2 stream pool exhaustion over time

#### Part B Configuration:
- **Victim**: Multi-worker Quart HTTP/2 server
- **Attacker**: Advanced adaptive HTTP/2 attack with 100 connections and 25 streams each
- **Expected Impact**: More sustained and resilient HTTP/2 stream exhaustion

## Performance Monitoring and Analysis

### Monitoring Setup
This lab includes comprehensive connection and performance monitoring capabilities. Refer to the detailed monitoring guide for complete instructions:

**📋 [Slowloris Monitoring Guide](../SLOWLORIS_MONITORING_GUIDE.md)**

### Key Metrics to Monitor

#### HTTP/2 Stream Analysis:
- **Active Connections**: Number of established HTTP/2 connections to port 8080
- **Stream States**: Distribution of HTTP/2 stream states within connections
- **Stream Duration**: How long individual streams remain active
- **HTTP/2 Multiplexing**: Stream counts per connection and overall utilization

#### Server Performance:
- **Response Time**: Normal vs degraded response times
- **New Connection Success**: Ability to establish new HTTP/2 connections
- **Service Availability**: Overall HTTP/2 server responsiveness
- **Stream Pool Status**: HTTP/2 stream utilization and worker load

#### Attack Effectiveness:
- **Stream Persistence**: How long attack streams and connections survive
- **Resource Consumption**: HTTP/2 server resource usage patterns
- **Legitimate User Impact**: Effect on normal HTTP/2 user connections
- **Detection Evasion**: Stealth characteristics of HTTP/2 attack patterns

### Quick Monitoring Commands

```bash
# Monitor active connections
watch -n 2 'ss -tan | grep :8080 | wc -l'

# Monitor connection states
watch -n 3 'ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c'

# Monitor HTTP/2 server health status
watch -n 5 'curl --http2-prior-knowledge -s http://localhost:8080/health'

# Test legitimate user impact with HTTP/2
timeout 10 curl --http2-prior-knowledge -o /dev/null -s -w "Response: %{time_total}s | HTTP: %{http_code}\n" http://localhost:8080
```

## Expected Attack Progression

### Part A (Basic HTTP/2 Slowloris) Timeline:
- **0-60s**: Initial HTTP/2 connection establishment and stream creation
- **60-180s**: HTTP/2 stream pools gradually fill across connections
- **180-300s**: Server stream limits approached, multiplexing degraded
- **300s+**: New streams refused, HTTP/2 DoS achieved

### Part B (Advanced Adaptive HTTP/2) Timeline:
- **0-90s**: Intelligent HTTP/2 connection establishment with adaptive stream pacing
- **90-240s**: Dynamic adjustment based on HTTP/2 server behavior and stream responses
- **240-600s**: Sustained HTTP/2 attack with stealth evasion techniques
- **600s+**: Long-term persistence with minimal detection through HTTP/2 legitimacy

### Key Attack Indicators:
1. **Gradual Stream Increase**: Steady rise in HTTP/2 streams across connections
2. **Response Degradation**: Increasing response times for legitimate HTTP/2 requests
3. **Stream Pool Exhaustion**: HTTP/2 server stream handling becomes saturated
4. **Connection/Stream Refusal**: New HTTP/2 connections or streams timeout or are refused

## Container Management

### Useful Commands

```bash
# View running containers
docker-compose ps

# View attack progress
docker-compose logs attacker

# View HTTP/2 server logs
docker-compose logs victim

# Stop the lab
docker-compose down

# Restart with fresh state
docker-compose down && docker-compose up -d
```

### Monitoring Attack Progress

```bash
# Monitor HTTP/2 attack container output
docker logs -f http2-slowloris-attacker-client

# Check HTTP/2 server access patterns
docker-compose logs victim | grep -E "(connection|stream|request)"

# Monitor HTTP/2 server errors
docker-compose logs victim | grep -i error
```

## Advanced Attack Analysis

### HTTP/2 Stream Pattern Analysis
```bash
# Analyze HTTP/2 connection establishment patterns
tcpdump -i any -nn -s 0 'port 8080 and tcp[tcpflags] & tcp-syn != 0' > http2_connection_analysis.log

# Monitor HTTP/2 frames and partial streams (requires HTTP/2 analysis tools)
tcpdump -i any -nn -A 'port 8080 and length < 200' > http2_partial_streams.log
```

### HTTP/2 Server Behavior Analysis
```bash
# Track HTTP/2 server process behavior
watch -n 5 'ps aux | grep hypercorn | grep -v grep | wc -l'

# Monitor file descriptor usage for HTTP/2 connections
watch -n 3 'lsof | grep :8080 | wc -l'

# Check HTTP/2 connection and stream limits
cat /proc/sys/net/core/somaxconn
```

## Expected Learning Outcomes

### Understanding HTTP/2 Stealth Attacks
- Comprehend how low-bandwidth HTTP/2 attacks can achieve high impact through stream multiplexing
- Understand the difference between volumetric and HTTP/2 stream-based attacks
- Learn about HTTP/2 attack persistence and evasion techniques

### HTTP/2 Stream Management Analysis
- Analyze how HTTP/2 servers handle stream pools and multiplexing
- Understand the impact of stream timeouts, limits, and flow control
- Observe HTTP/2 stream state transitions during attacks

### HTTP/2 Detection and Mitigation Insights
- Identify characteristics that distinguish HTTP/2 attack streams from legitimate traffic
- Understand the challenges of detecting stealth HTTP/2 attacks that appear legitimate
- Learn about adaptive HTTP/2 attack techniques that evade simple defenses

### Cloud vs Local Performance
- Compare HTTP/2 attack effectiveness between local Docker and GCP deployment
- Analyze how cloud infrastructure affects HTTP/2 connection and stream handling
- Evaluate scalability and resource differences in different environments

## Troubleshooting

### Common Issues
- **Attack not effective**: Check HTTP/2 server worker configuration and stream limits
- **Connections/streams dropping quickly**: Verify HTTP/2 timeout settings and flow control
- **Port conflicts**: Ensure port 8080 is available

### HTTP/2 Server Configuration Check
```bash
# Check HTTP/2 server configuration
docker-compose logs victim | grep -i config

# View current HTTP/2 settings
docker-compose exec victim env | grep -E "(WORKERS|TIMEOUT)"
```

### HTTP/2 Attack Debugging
```bash
# Check HTTP/2 attack script output
docker logs http2-slowloris-attacker-client

# Monitor HTTP/2 attack connection count
docker-compose exec victim ss -tan | grep :8080 | wc -l

# Verify HTTP/2 attack script is running
docker-compose exec attacker ps aux | grep python
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
- HTTP/2 connection and stream count progression over time
- Response time degradation patterns for HTTP/2 requests
- HTTP/2 server resource utilization during attacks
- Attack persistence and recovery characteristics

### Comparative Analysis Framework
- **Environment Comparison**: Local Docker vs GCP HTTP/2 connection handling
- **Attack Variation**: Basic vs advanced HTTP/2 attack effectiveness
- **Server Configuration**: Impact of different HTTP/2 server settings
- **Detection Analysis**: Identifying attack signatures in HTTP/2 stream patterns

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