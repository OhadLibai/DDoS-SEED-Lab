#!/bin/bash

# Test script to validate HTTP/2 Slowloris attack effectiveness
# Run this AFTER starting the attack to monitor its impact

echo "HTTP/2 Slowloris Attack Effectiveness Test"
echo "=========================================="

# Test server response time
echo "1. Testing server response time..."
for i in {1..5}; do
    echo -n "  Test $i: "
    time_result=$(curl -o /dev/null -s -w "Time: %{time_total}\n" http://localhost:8080 2>/dev/null)
    echo "$time_result"
    sleep 1
done

echo ""

# Monitor TCP connections from attacker container
echo "2. Checking TCP connections from attack container..."
docker exec http2-slowloris-attacker bash -c 'grep -c " 01 " /proc/net/tcp' 2>/dev/null | \
    while read count; do echo "  Established connections from attacker: $count"; done

echo ""

# Monitor victim server load
echo "3. Checking victim server status..."
docker exec loris-victim-apache-latest bash -c 'ps aux | grep httpd | wc -l' 2>/dev/null | \
    while read count; do echo "  Apache processes: $count"; done

# Check for HTTP/2 in logs  
echo "4. Checking for HTTP/2.0 requests in victim logs..."
docker logs loris-victim-apache-latest 2>&1 | tail -10 | grep "HTTP/2.0" | wc -l | \
    while read count; do echo "  Recent HTTP/2.0 requests: $count"; done

# Check for incomplete requests (POST without corresponding data)
echo "4.1. Checking for incomplete POST requests..."
docker logs loris-victim-apache-latest 2>&1 | tail -20 | grep "POST" | wc -l | \
    while read count; do echo "  Recent POST requests: $count (may indicate slow attacks)"; done

echo ""

# Test concurrent connections
echo "5. Testing server under concurrent load..."
echo "   Starting 5 concurrent curl requests..."
for i in {1..5}; do
    (curl -o /dev/null -s -w "Request $i time: %{time_total}\n" http://localhost:8080) &
done
wait

echo ""

# New test - check for 200 responses in logs (should be ZERO if attack works)
echo "6. Checking for 200 responses (should be ZERO if attack is working)..."
docker logs loris-victim-apache-latest 2>&1 | tail -20 | grep "200" | wc -l | \
    while read count; do echo "  Recent 200 responses: $count (should be 0!)"; done

echo ""
echo "Test completed. If the LOW AND SLOW attack is effective:"
echo ""
echo "GOOD signs (attack working):"
echo "- Moderate TCP connections from attacker (50-75)"
echo "- Degraded response times (0.1-2+ seconds)" 
echo "- HTTP/2.0 protocol in victim logs"
echo "- Reduced successful 200 responses compared to baseline"
echo "- Sustained connections over time"
echo "- Evidence of incomplete HTTP/2 streams in logs"
echo ""
echo "ACCEPTABLE signs (partial effectiveness):"
echo "- Some 200 responses but with degraded performance"
echo "- Variable response times showing server stress"
echo "- Moderate connection counts (50-100)"
echo ""
echo "BAD signs (attack not working):"
echo "- Very few TCP connections (<25)"
echo "- Consistently fast response times (<0.1s)"
echo "- Many rapid 200 responses"
echo "- No evidence of server resource consumption"
echo ""
echo "Note: Low and slow attacks focus on resource exhaustion over time,"
echo "not overwhelming with volume. Success is measured by sustained"
echo "server degradation with minimal attacker resources."