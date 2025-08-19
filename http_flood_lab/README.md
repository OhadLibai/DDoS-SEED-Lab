# HTTP Flood Attack Lab

## Overview

The HTTP Flood Attack Lab demonstrates volumetric Distributed Denial of Service (DDoS) attacks that overwhelm web servers through high-volume HTTP request flooding. This lab explores how different server architectures respond to sustained HTTP request attacks and provides hands-on experience with measuring attack effectiveness.

## Attack Mechanism

**HTTP Flood attacks** work by overwhelming web servers with a large volume of seemingly legitimate HTTP requests. Unlike network-layer attacks, these operate at the application layer (Layer 7), making them harder to distinguish from normal traffic and more challenging to defend against.

### Key Characteristics:
- **High Volume**: Generates numerous concurrent HTTP requests
- **Resource Exhaustion**: Consumes server CPU, memory, and connection pools
- **Application Layer**: Targets web application resources specifically
- **Legitimate Appearance**: Requests appear valid to basic filtering systems

## Lab Structure

### Part A: Single-Threaded Flask Server
- **Target**: Basic Flask development server (single-threaded)
- **Attack Intensity**: 32 concurrent connections
- **Expected Behavior**: Severe performance degradation due to single-threaded nature
- **Learning Focus**: Understanding baseline server vulnerabilities

### Part B: Multi-Threaded Gunicorn Server  
- **Target**: Production-grade Gunicorn WSGI server (multi-worker)
- **Attack Intensity**: 128 concurrent connections
- **Expected Behavior**: Better resilience but eventual degradation under sustained load
- **Learning Focus**: Comparing production server architectures

## Prerequisites

### Technical Requirements
- Docker and Docker Compose installed
- Available port 8080 on your system
- Basic command-line knowledge
- Google Cloud Platform account (for cloud deployment)

### Knowledge Prerequisites
- Basic understanding of HTTP protocol
- Familiarity with web server concepts
- Elementary networking knowledge (TCP/IP, ports)

## Quick Start Guide

### Local Deployment

#### Deploy Part A (Single-Threaded)
```bash
cd part_A
docker-compose up -d

# Verify deployment
curl http://localhost:8080
```

#### Deploy Part B (Multi-Threaded)
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
gcloud compute instances create ddos-lab-vm \
    --zone=us-central1-a \
    --machine-type=e2-standard-2 \
    --image-family=ubuntu-2004-lts \
    --image-project=ubuntu-os-cloud

# SSH into instance
gcloud compute ssh ddos-lab-vm --zone=us-central1-a

# Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
```

#### 2. Configure Firewall
```bash
# Allow HTTP traffic on port 8080
gcloud compute firewall-rules create allow-http-flood-lab \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow HTTP Flood Lab traffic"
```

#### 3. Deploy Lab
```bash
# Clone repository on GCP VM
git clone <repository-url>
cd DDoS-SEED-lab/http_flood_lab

# Deploy chosen part
cd part_A  # or part_B
docker-compose up -d
```

## Lab Components

### 1. Target Application (`victim_app.py`)
Simple Flask web application that serves as the attack target:
- Basic HTTP endpoint responding to GET requests
- Minimal processing to highlight infrastructure impact
- Runs on port 80 inside container (mapped to 8080 on host)

### 2. Attack Script (`http_flood.py`)
Multithreaded HTTP flood attack implementation:
- Configurable number of concurrent connections
- Continuous request generation
- Realistic browser user-agent headers
- Designed for educational demonstration

### 3. Container Architecture

#### Part A Configuration:
- **Victim**: Single-threaded Flask development server
- **Attacker**: 32 concurrent connections
- **Expected Impact**: Severe performance degradation

#### Part B Configuration:
- **Victim**: Gunicorn WSGI server with multiple workers
- **Attacker**: 128 concurrent connections  
- **Expected Impact**: Better resilience, gradual degradation

## Performance Monitoring and Analysis

### Monitoring Setup
This lab includes comprehensive monitoring capabilities. Refer to the detailed monitoring guide for complete instructions:

**=� [HTTP Flood Monitoring Guide](../HTTP_FLOOD_MONITORING_GUIDE.md)**

### Key Metrics to Monitor

#### Server Performance:
- **Response Time**: Normal (0.01-0.05s) vs Under Attack (3-30s+)
- **Throughput**: Requests per second capacity
- **HTTP Status Codes**: Success rate vs error rate
- **Connection Handling**: Time to establish connections

#### Resource Utilization:
- **CPU Usage**: Expected increase to 80-100% during attack
- **Memory Consumption**: Monitor for memory exhaustion
- **Network I/O**: Bandwidth utilization patterns
- **Container Stats**: Docker resource usage metrics

#### Attack Effectiveness:
- **Success Rate**: Percentage of successful requests
- **Service Availability**: Uptime during attack
- **Recovery Time**: System restoration after attack cessation

### Quick Monitoring Commands

```bash
# Monitor response times in real-time
watch -n 1 'curl -o /dev/null -s -w "%{time_total}s\n" http://localhost:8080'

# Monitor container resource usage
watch -n 1 'docker stats --no-stream'

# Monitor connection count
watch -n 2 'ss -tan | grep :8080 | wc -l'

# Test service availability
timeout 10 curl -o /dev/null -s -w "Response: %{time_total}s | HTTP: %{http_code}\n" http://localhost:8080
```

## Expected Learning Outcomes

### Understanding Attack Vectors
- Comprehend how volumetric attacks overwhelm server resources
- Observe differences between application-layer and network-layer attacks
- Learn to identify HTTP flood attack patterns

### Infrastructure Analysis
- Compare single-threaded vs multi-threaded server resilience
- Understand the impact of server architecture on attack resistance
- Analyze resource consumption patterns during attacks

### Performance Measurement
- Develop skills in quantifying attack effectiveness
- Learn to use monitoring tools for performance analysis
- Practice comparative analysis between different environments

### Cloud vs Local Performance
- Evaluate performance differences between local Docker and GCP deployment
- Understand how cloud infrastructure affects attack dynamics
- Analyze scalability characteristics in different environments

## Container Management

### Useful Commands

```bash
# View running containers
docker-compose ps

# View container logs
docker-compose logs victim
docker-compose logs attacker

# Stop the lab
docker-compose down

# Restart with fresh containers
docker-compose down && docker-compose up -d

# Scale attacker for more intensive testing
docker-compose up --scale attacker=3
```

### Troubleshooting

#### Common Issues:
- **Port 8080 in use**: Stop conflicting services or use different port
- **Attack not effective**: Increase attacker connections or reduce server resources
- **Containers failing**: Check Docker logs for specific error messages

#### Quick Fixes:
```bash
# Check port availability
ss -tuln | grep :8080

# Restart Docker if needed
sudo systemctl restart docker

# Check container health
docker-compose ps
docker-compose logs
```

## Advanced Experiments

### Scaling Experiments
```bash
# Test different attack intensities
# Modify docker-compose.yml to adjust connection counts

# Multi-attacker deployment
docker-compose up --scale attacker=5

# Resource-constrained victim
# Add resource limits to victim container
```

### Custom Configurations
- Modify `http_flood.py` to test different request patterns
- Adjust Gunicorn worker counts in Part B
- Implement custom monitoring scripts
- Test with different target applications

## Data Collection and Analysis

### Performance Data
Students should focus on collecting and analyzing:
- Response time distributions under normal vs attack conditions
- Resource utilization patterns across different server architectures
- Attack effectiveness metrics across local vs cloud environments
- Recovery characteristics after attack cessation

### Comparative Analysis Framework
- **Environment Comparison**: Local Docker vs GCP performance
- **Architecture Comparison**: Single-threaded vs multi-threaded resilience  
- **Attack Intensity**: Scaling effects on server performance
- **Detection Metrics**: Identifying attack signatures in monitoring data

## Safety Considerations

### Controlled Environment Usage
- Deploy only in dedicated laboratory environments
- Use isolated networks when possible
- Monitor resource usage to prevent system overload
- Ensure proper cleanup after experiments

---

**=� For detailed monitoring procedures, refer to [HTTP Flood Monitoring Guide](../HTTP_FLOOD_MONITORING_GUIDE.md)**

**<� Return to [Main Lab Overview](../README.md)**