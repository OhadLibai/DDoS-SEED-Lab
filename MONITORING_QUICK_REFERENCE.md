# DDoS Lab Monitoring - Quick Reference Guide

## Environment Setup (CRITICAL FIRST STEP)

### 🏠 Local Environment
```bash
export TARGET_URL="http://localhost:8080"
echo "Local target: $TARGET_URL"
```

### ☁️ GCP Environment
```bash
EXTERNAL_IP=$(curl -s http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/external-ip -H "Metadata-Flavor: Google")
export TARGET_URL="http://$EXTERNAL_IP:8080"
echo "GCP target: $TARGET_URL"
```

## Quick Start Commands (UNIVERSAL)

### HTTP Flood Lab
```bash
# One-line monitoring setup
watch -n 1 'curl -o /dev/null -s -w "%{time_total}s\n" $TARGET_URL' &
watch -n 1 'docker stats --no-stream' &
watch -n 2 'ss -tan | grep :8080 | wc -l' &

# Performance test
curl -o /dev/null -s -w "Total:%{time_total}s|Connect:%{time_connect}s|TTFB:%{time_starttransfer}s|HTTP:%{http_code}\n" $TARGET_URL
```

### Slowloris Lab
```bash
# Connection monitoring
watch -n 2 'ss -tan | grep :8080 | awk "{print \$1}" | sort | uniq -c' &
watch -n 3 'curl -s $TARGET_URL/server-status?auto | grep -E "(BusyWorkers|IdleWorkers)"' &

# Impact testing
timeout 10 curl -s -o /dev/null -w "Response: %{time_total}s\n" $TARGET_URL
```

## Key Metrics Summary

| Lab | Metric | Normal Value | Under Attack | Command |
|-----|--------|-------------|--------------|---------|
| HTTP Flood | Response Time | 0.01-0.05s | 3-30s+ | `curl -w "%{time_total}s"` |
| HTTP Flood | CPU Usage | <20% | 80-100% | `docker stats` |
| HTTP Flood | Success Rate | 100% | 10-30% | Success/failure counting |
| Slowloris | Active Connections | <10 | 50-200+ | `ss -tan \| grep :8080 \| wc -l` |
| Slowloris | Apache Workers | Mostly idle | All busy | `curl server-status` |
| Slowloris | New Connections | Immediate | Refused/timeout | Connection testing |

## GCP Monitoring Commands
```bash
# VM monitoring
gcloud compute instances describe your-vm-name --zone=your-zone

# Firewall check
gcloud compute firewall-rules list --filter="name~'.*8080.*'"

# Logging
gcloud logging read "resource.type=gce_instance" --limit=20
```

## Performance Comparison Commands

### Environment Detection
```bash
ENV_TYPE=$(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)
echo "Current environment: $ENV_TYPE"
```

### Data Collection with Environment Labels
```bash
# Baseline collection
curl -o /dev/null -s -w "$ENV_TYPE Baseline: %{time_total}s\n" $TARGET_URL

# Attack impact logging
echo "$(date): $ENV_TYPE attack impact test" >> attack_comparison.log
```

## Emergency Commands
```bash
# Stop attack
docker-compose down

# Kill monitoring processes
pkill -f "watch"; pkill -f "curl"; pkill -f "tcpdump"

# Check system health
uptime && free -h && ss -tan | grep :8080 | wc -l

# Quick environment check
echo "Target: $TARGET_URL" && echo "Environment: $(if [[ $TARGET_URL == *localhost* ]]; then echo 'LOCAL'; else echo 'GCP'; fi)"
```