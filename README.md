# DDoS Attack Labs - SEED Educational Project

## Overview

This repository contains two comprehensive laboratory exercises designed to explore and understand Distributed Denial of Service (DDoS) attacks in controlled educational environments. The labs provide hands-on experience with different DDoS attack vectors and their impact on web services, while emphasizing defensive cybersecurity practices.

## Educational Context

These labs are part of the broader **SEED (SEcurity EDucation)** project, which provides practical cybersecurity exercises for educational institutions worldwide. The SEED project focuses on learning-by-doing methodology, allowing students to gain practical experience with security concepts through controlled laboratory environments.

## Lab Components

### 🌊 [HTTP/2 Flood Attack Lab](./http_flood_lab/)
Explores volumetric DDoS attacks that overwhelm server resources through high-volume HTTP/2 multiplexed requests.

**Key Learning Areas:**
- Understanding HTTP/2 multiplexing vulnerabilities
- Server resource exhaustion via stream flooding
- Single vs multi-worker HTTP/2 server resilience
- Performance impact measurement in HTTP/2 environments

### 🐌 [HTTP/2 Slowloris Attack Lab](./slowloris_lab/)
Investigates stream exhaustion attacks that consume HTTP/2 server resources through incomplete requests.

**Key Learning Areas:**
- Low-bandwidth, high-impact HTTP/2 stream exhaustion techniques
- HTTP/2 connection and stream pool exhaustion strategies
- Stealth attack characteristics using legitimate HTTP/2 features
- Adaptive attack methodologies for HTTP/2 environments

## Repository Structure

```
DDoS-SEED-lab/
├── README.md                           # This file
├── HTTP_FLOOD_MONITORING_GUIDE.md      # Comprehensive HTTP/2 flood monitoring
├── SLOWLORIS_MONITORING_GUIDE.md       # Detailed HTTP/2 Slowloris monitoring  
├── MONITORING_QUICK_REFERENCE.md       # Quick reference commands for HTTP/2
├── http_flood_lab/                     # HTTP/2 Flood Attack Lab
│   ├── README.md                       # Lab-specific instructions
│   ├── part_A/                         # Single-worker HTTP/2 server
│   ├── part_B/                         # Multi-worker HTTP/2 server
│   ├── victim_app.py                   # HTTP/2 web application target
│   ├── http_flood.py                   # HTTP/2 attack script
│   └── Dockerfile.flood_attcker        # Attacker container
└── slowloris_lab/                      # HTTP/2 Slowloris Attack Lab
    ├── README.md                       # Lab-specific instructions
    ├── part_A/                         # Basic HTTP/2 Slowloris attack
    ├── part_B/                         # Advanced adaptive HTTP/2 attack
    └── ...                             # Attack scripts and configurations
```

## Key Objectives

### Primary Learning Goals
1. **Attack Vector Understanding** - Comprehend different DDoS attack mechanisms and their characteristics
2. **Infrastructure Impact Analysis** - Observe how different server architectures respond to various attack types
3. **Performance Measurement** - Learn to quantify attack effectiveness and system degradation
4. **Cloud vs Local Comparison** - Evaluate performance differences between local Docker and cloud environments

### Technical Skills Development
- Docker containerization and orchestration
- Network monitoring and analysis
- Performance benchmarking techniques
- Cloud platform deployment (Google Cloud Platform)
- System resource monitoring

## Prerequisites

### Technical Requirements
- **Docker** and **Docker Compose** installed
- Basic command-line proficiency (Linux/Unix)
- **Google Cloud Platform** account (for cloud deployment comparison)
- SSH client for remote access

### Knowledge Prerequisites
- Basic understanding of HTTP/1.1 and HTTP/2 protocols
- Familiarity with client-server architecture
- Elementary networking concepts (TCP connections, ports, multiplexing)
- Basic cybersecurity awareness
- Understanding of HTTP/2 features (multiplexing, server push, header compression)

### System Requirements
- **Local Development:**
  - 4GB+ RAM recommended
  - Docker with at least 2GB allocated memory
  - Available ports: 8080

- **Cloud Deployment (GCP):**
  - VM instance with 2+ vCPUs
  - 4GB+ memory
  - Ubuntu 20.04+ or similar Linux distribution

## Quick Start Guide

### 1. Repository Setup
```bash
git clone <repository-url>
cd DDoS-SEED-lab
```

### 2. Choose Your Lab
- **HTTP Flood Lab**: `cd http_flood_lab/` 
- **Slowloris Lab**: `cd slowloris_lab/`

### 3. Select Lab Variant
- **Part A**: Basic implementation (single-threaded/basic attack)
- **Part B**: Advanced implementation (multi-threaded/adaptive attack)

### 4. Deploy and Monitor
```bash
# Deploy the lab
cd part_A  # or part_B
docker-compose up -d

# Start monitoring (refer to monitoring guides)
watch -n 1 'curl --http2 -w "%{time_total}s\n" http://localhost:8080'
```

## Performance Analysis Framework

This project emphasizes **comparative performance analysis** between different deployment environments and protocols:

### Local vs Cloud Comparison
- **Local Environment**: Docker containers with HTTP/2 support on local machine
- **Cloud Environment**: HTTP/2 deployment on Google Cloud Platform
- **Comparison Metrics**: CPU usage, response latency, traffic throughput, stream multiplexing efficiency, scalability limits

### Monitoring Resources
Comprehensive monitoring guides are provided to facilitate detailed performance analysis:

- **[HTTP/2 Flood Monitoring Guide](./HTTP_FLOOD_MONITORING_GUIDE.md)** - Complete monitoring setup for HTTP/2 volumetric attacks
- **[HTTP/2 Slowloris Monitoring Guide](./SLOWLORIS_MONITORING_GUIDE.md)** - Detailed HTTP/2 stream exhaustion monitoring
- **[Quick Reference Guide](./MONITORING_QUICK_REFERENCE.md)** - Essential HTTP/2 commands and metrics summary

## Educational Integration

### Pedagogical Approach
- **Experiential Learning** - Direct hands-on experience with attack techniques
- **Controlled Environment** - Safe, isolated laboratory settings
- **Comparative Analysis** - Understanding trade-offs and performance characteristics
- **Defensive Perspective** - Emphasis on understanding attacks to build better defenses

## Support and Resources

### Documentation
- Individual lab README files provide detailed setup instructions
- Monitoring guides offer comprehensive performance analysis procedures
- Quick reference guides enable rapid troubleshooting

### SEED Project Resources
- [SEED Project Website](https://seedsecuritylabs.org/) - Additional security labs and resources
- [SEED Lab Manual](https://github.com/seed-labs/seed-labs) - Comprehensive lab collection
