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
docker exec http2-adv-slowloris-attacker bash -c 'grep -c " 01 " /proc/net/tcp' 2>/dev/null | \
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
echo "Test completed. If the CONNECTION-LEVEL EXHAUSTION attack is effective:"
echo ""
echo "GOOD signs (attack working):"
echo "- Many TCP connections from attacker (200-300+)"
echo "- Slower response times (2-10+ seconds)"
echo "- HTTP/2.0 protocol in victim logs"
echo "- Server under load (high CPU/memory on victim)"
echo "- Apache processes being stressed"
echo ""
echo "ACCEPTABLE signs (partial effectiveness):"
echo "- Some 200 responses (but with slower times)"
echo "- Moderate connection counts (50-200)"
echo "- Variable response times"
echo ""
echo "BAD signs (attack not working):"
echo "- Very few TCP connections (<50)"
echo "- Consistently fast response times (<0.01s)"
echo "- Many rapid 200 responses"
echo "- No server load indicators"