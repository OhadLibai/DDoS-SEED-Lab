# DDoS Attack Labs - SEED Educational Project

## Overview

This repository contains two comprehensive laboratory exercises designed to explore and understand Distributed Denial of Service (DDoS) attacks in controlled educational environments. The labs provide hands-on experience with different DDoS attack vectors and their impact on web services, while emphasizing defensive cybersecurity practices.

## Educational Context

These labs are part of the broader **SEED (SEcurity EDucation)** project, which provides practical cybersecurity exercises for educational institutions worldwide. The SEED project focuses on learning-by-doing methodology, allowing students to gain practical experience with security concepts through controlled laboratory environments.

## Lab Components

### 🌊 [HTTP Flood Attack Lab](./http_flood_lab/)
Explores volumetric DDoS attacks that overwhelm server resources through high-volume HTTP requests.

**Key Learning Areas:**
- Understanding volumetric attack patterns
- Server resource exhaustion mechanisms  
- Single-threaded vs multi-threaded server resilience
- Performance impact measurement

### 🐌 [Slowloris Attack Lab](./slowloris_lab/)
Investigates connection exhaustion attacks that consume server resources with minimal bandwidth usage.

**Key Learning Areas:**
- Low-bandwidth, high-impact attack techniques
- Connection pool exhaustion strategies
- Stealth attack characteristics
- Adaptive attack methodologies

## Repository Structure

```
DDoS-SEED-lab/
├── README.md                           # This file
├── HTTP_FLOOD_MONITORING_GUIDE.md      # Comprehensive HTTP flood monitoring
├── SLOWLORIS_MONITORING_GUIDE.md       # Detailed Slowloris monitoring  
├── MONITORING_QUICK_REFERENCE.md       # Quick reference commands
├── http_flood_lab/                     # HTTP Flood Attack Lab
│   ├── README.md                       # Lab-specific instructions
│   ├── part_A/                         # Single-threaded Flask server
│   ├── part_B/                         # Multi-threaded Gunicorn server
│   ├── victim_app.py                   # Web application target
│   ├── http_flood.py                   # Attack script
│   └── Dockerfile.flood_attcker        # Attacker container
└── slowloris_lab/                      # Slowloris Attack Lab
    ├── README.md                       # Lab-specific instructions
    ├── part_A/                         # Basic Slowloris attack
    ├── part_B/                         # Advanced adaptive attack
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
- Basic understanding of HTTP protocol
- Familiarity with client-server architecture
- Elementary networking concepts (TCP connections, ports)
- Basic cybersecurity awareness

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
watch -n 1 'curl -w "%{time_total}s\n" http://localhost:8080'
```

## Performance Analysis Framework

This project emphasizes **comparative performance analysis** between different deployment environments:

### Local vs Cloud Comparison
- **Local Environment**: Docker containers on local machine
- **Cloud Environment**: Deployment on Google Cloud Platform
- **Comparison Metrics**: CPU usage, response latency, traffic throughput, scalability limits

### Monitoring Resources
Comprehensive monitoring guides are provided to facilitate detailed performance analysis:

- **[HTTP Flood Monitoring Guide](./HTTP_FLOOD_MONITORING_GUIDE.md)** - Complete monitoring setup for volumetric attacks
- **[Slowloris Monitoring Guide](./SLOWLORIS_MONITORING_GUIDE.md)** - Detailed connection exhaustion monitoring
- **[Quick Reference Guide](./MONITORING_QUICK_REFERENCE.md)** - Essential commands and metrics summary

## Educational Integration

### SEED Lab Ecosystem
These DDoS labs complement other SEED project laboratories:
- **Network Security Labs** - Building foundational networking knowledge
- **Web Security Labs** - Understanding web application vulnerabilities  
- **System Security Labs** - Exploring operating system security mechanisms
- **Cryptography Labs** - Learning security protocols and encryption

### Pedagogical Approach
- **Experiential Learning** - Direct hands-on experience with attack techniques
- **Controlled Environment** - Safe, isolated laboratory settings
- **Comparative Analysis** - Understanding trade-offs and performance characteristics
- **Defensive Perspective** - Emphasis on understanding attacks to build better defenses

## Safety and Ethics

### Laboratory Environment
- All exercises are designed for **controlled educational environments only**
- Use isolated networks and dedicated laboratory systems
- Never deploy against systems you do not own or have explicit permission to test

### Educational Purpose
- Focus on **defensive cybersecurity** education
- Understanding attack vectors to build better defenses
- Responsible disclosure and ethical security practices
- Compliance with institutional policies and local laws

## Support and Resources

### Documentation
- Individual lab README files provide detailed setup instructions
- Monitoring guides offer comprehensive performance analysis procedures
- Quick reference guides enable rapid troubleshooting

### SEED Project Resources
- [SEED Project Website](https://seedsecuritylabs.org/) - Additional security labs and resources
- [SEED Lab Manual](https://github.com/seed-labs/seed-labs) - Comprehensive lab collection
- Community forums and educational support materials

## Contributing

This project follows SEED project principles of open educational resources. Improvements, bug fixes, and educational enhancements are welcome through standard GitHub contribution workflows.

## License

This project is released under educational use licenses consistent with the SEED project framework, promoting open access to cybersecurity education resources.

---

**Note**: These laboratories are designed for educational purposes within controlled environments. Always follow responsible disclosure practices and ethical guidelines when working with security-related technologies.