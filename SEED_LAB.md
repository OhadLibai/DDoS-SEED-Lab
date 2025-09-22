# HTTP/2 DDoS Attack Lab

## Overview

This lab explores Distributed Denial of Service (DDoS) attacks targeting HTTP/2 protocol vulnerabilities. Students will gain hands-on experience with modern web protocol exploitation techniques through controlled environments, understanding both HTTP/2 application flood attacks and flow control mechanism exploitation.

## Learning Objectives

After completing this lab, students should be able to:

1. Understand HTTP/2 protocol fundamentals and security implications
2. Implement and analyze HTTP/2 application flood attacks 
3. Exploit HTTP/2 flow control mechanisms for resource exhaustion
4. Assess the effectiveness of different attack strategies
5. Understand the difference between HTTP/1.1 and HTTP/2 attack vectors
6. Analyze server resource consumption patterns during attacks

## Lab Environment Setup

### Requirements

- Docker and Docker Compose
- Python 3.8+
- 4GB+ RAM recommended
- Network analysis tools (wireshark, netstat, ss)

### Lab Architecture

```
┌─────────────────┐    HTTP/2     ┌─────────────────┐
│ Attack Container│◄─────────────►│Server Container │
│ (Python Scripts)│   Protocol    │ (HTTP/2 Server) │
└─────────────────┘               └─────────────────┘
        │                                   │
        └───────── Bridge Network ──────────┘
```

### Environment Preparation

Described in each attack seperatly.


## Lab Tasks

---

## Task 1: HTTP/2 Application Flood Attack

### Background

HTTP/2 introduces stream multiplexing, allowing multiple requests over a single connection. This feature, while improving performance, can be exploited to overwhelm servers by sending numerous concurrent requests that consume CPU and memory resources.

### Objective

Implement an HTTP/2 application flood attack that exploits stream multiplexing to overwhelm a server with computationally expensive requests.

### Task 1.1: Basic Application Flood

Examine the file `attacks/http2_app_flood.py`. You'll find several `# FILL CODE HERE` sections that need to be completed.

#### Key Components to Implement:

**1. HTTP/2 Connection Establishment**
```python
# FILL CODE HERE - Establish HTTP/2 connection
# Hint: Use h2 library to create HTTP/2 connection
# Consider: How do you initiate an HTTP/2 connection?
# What headers are required for HTTP/2?
```

**Guidance**: 
- Use the `h2.connection.H2Connection` class
- Initialize the connection and send the connection preface
- Handle the HTTP/2 settings frame exchange

**2. Stream Creation and Request Flooding**
```python
# FILL CODE HERE - Create multiple streams for flooding
# Hint: HTTP/2 allows multiple concurrent streams
# Consider: How many streams can you create simultaneously?
# What's the maximum concurrent streams setting?
```

**Guidance**:
- Create multiple streams using different stream IDs
- Send GET requests to CPU-intensive endpoints like `/captcha` or `/crypto`
- Implement a loop to create many concurrent requests
- Consider the server's `SETTINGS_MAX_CONCURRENT_STREAMS` value

**3. Resource-Intensive Request Targeting**
```python
# FILL CODE HERE - Target CPU-intensive endpoints
# Available endpoints: /captcha, /crypto, /gaming, /image, /compute, /database
# Hint: Different endpoints have different resource consumption patterns
```

**Guidance**:
- Test different endpoints to understand their resource impact
- Monitor server CPU and memory usage during attacks
- Experiment with request patterns (burst vs. sustained)

### Task 1.2: Advanced Flood Techniques

Enhance your basic flood attack with advanced techniques:

**1. Stream Priority Manipulation**
```python
# FILL CODE HERE - Implement stream priority manipulation
# Hint: HTTP/2 allows setting stream priorities
# Consider: How can priority manipulation amplify the attack?
```

**Guidance**:
- Use the `PRIORITY` frame to manipulate stream dependencies
- Create complex dependency trees to consume server resources
- Test different priority configurations

**2. Header Compression Exploitation**
```python
# FILL CODE HERE - Exploit HPACK compression
# Hint: Large or complex headers can consume memory
# Consider: How can you craft headers to maximize resource consumption?
```

**Guidance**:
- Send requests with large header tables
- Use dynamic table updates to consume memory
- Create header patterns that defeat compression efficiency

### Analysis Questions for Task 1:

1. **Resource Impact**: Monitor the server during your attack. How does CPU and memory usage change?
2. **Connection Limits**: What happens when you exceed the server's concurrent stream limit?
3. **Attack Efficiency**: Compare the effectiveness of targeting different endpoints. Which consumes the most server resources?
4. **Detection Evasion**: How might you modify your attack to evade basic rate limiting?

---

## Task 2: HTTP/2 Flow Control Attack

### Background

HTTP/2 implements flow control at both connection and stream levels using WINDOW_UPDATE frames. By manipulating window sizes, attackers can force servers to buffer data indefinitely, leading to memory exhaustion and thread blocking.

### Objective

Implement flow control attacks that exploit HTTP/2's window update mechanism to cause resource exhaustion and denial of service.

### Task 2.1: Zero-Window Attack

Examine the file `attacks/flow_control_zero_window.py`.

#### Key Implementation Areas:

**1. Connection Initialization with Zero Window**
```python
# FILL CODE HERE - Initialize connection with zero flow control window
# Hint: Use SETTINGS frame to set SETTINGS_INITIAL_WINDOW_SIZE to 0
# Consider: What happens when the server can't send response data?
```

**Guidance**:
- Send a SETTINGS frame with `SETTINGS_INITIAL_WINDOW_SIZE = 0`
- This forces the server to buffer all response data
- Multiple connections amplify the memory consumption

**2. Request Generation Without Window Updates**
```python
# FILL CODE HERE - Send requests but never send WINDOW_UPDATE frames
# Hint: Server will buffer responses waiting for window updates
# Consider: How many requests before the server exhausts memory?
```

**Guidance**:
- Send GET requests to data-heavy endpoints
- Never send WINDOW_UPDATE frames to expand the window
- Monitor server memory usage as responses accumulate

**3. Connection Multiplication**
```python
# FILL CODE HERE - Create multiple connections for amplification
# Hint: Each connection can have its own zero window
# Consider: How does increasing connections affect server resources?
```

**Guidance**:
- Create multiple parallel connections
- Each connection maintains its own zero window
- Test scalability limits of your attack

### Task 2.2: Slow Incremental Attack

Examine the file `attacks/flow_control_slow_increment.py`.

#### Key Implementation Areas:

**1. Minimal Window Updates**
```python
# FILL CODE HERE - Send minimal WINDOW_UPDATE frames periodically
# Hint: Update window by 1 byte at a time with delays
# Consider: How does this prolong the attack while appearing legitimate?
```

**Guidance**:
- Send WINDOW_UPDATE frames with increment=1
- Add delays between updates (e.g., 1-5 seconds)
- This maintains the connection while severely limiting throughput

**2. Adaptive Timing**
```python
# FILL CODE HERE - Implement adaptive timing to avoid detection
# Hint: Vary the timing pattern to appear more natural
# Consider: How can you randomize timing while maintaining attack effectiveness?
```

**Guidance**:
- Use random intervals between window updates
- Monitor server behavior and adapt timing accordingly
- Implement exponential backoff patterns

### Task 2.3: Advanced Flow Control Exploitation

**1. Mixed Window Sizes**
```python
# FILL CODE HERE - Use different window sizes for different streams
# Hint: Some streams can have normal windows, others zero
# Consider: How does this help evade detection?
```

**Guidance**:
- Alternate between normal and restricted windows
- Create patterns that appear like legitimate slow clients
- Mix legitimate and malicious streams

**2. Connection-Level vs Stream-Level Control**
```python
# FILL CODE HERE - Coordinate connection and stream level flow control
# Hint: HTTP/2 has separate flow control for connections and streams
# Consider: How can you exploit both levels simultaneously?
```

**Guidance**:
- Understand the interaction between connection and stream windows
- Block at both levels for maximum impact
- Test different combinations of window restrictions

### Analysis Questions for Task 2:

1. **Memory Consumption**: How does server memory usage change during zero-window attacks?
2. **Thread Blocking**: Monitor server thread pools. How many threads get blocked waiting for window updates?
3. **Attack Duration**: How long can you maintain a flow control attack before the server times out?
4. **Evasion Techniques**: How do slow incremental updates help evade basic DDoS detection?

---

## Task 3: Attack Analysis and Mitigation

### Task 3.1: Performance Impact Measurement

Create scripts to measure attack effectiveness:

**1. Response Time Analysis**
```python
# FILL CODE HERE - Measure server response times during attacks
# Hint: Use curl or Python requests to measure response latency
# Consider: How do response times change as attacks intensify?
```

**2. Resource Consumption Monitoring**
```python
# FILL CODE HERE - Monitor server CPU, memory, and network usage
# Hint: Use Docker stats or system monitoring tools
# Consider: Which attack consumes which resources most effectively?
```

### Task 3.2: Attack Comparison

Compare the effectiveness of different attack strategies:

1. **Throughput Impact**: Which attack reduces server throughput the most?
2. **Resource Efficiency**: Which attack achieves maximum impact with minimal attacker resources?
3. **Detection Difficulty**: Which attack is hardest to detect and block?

### Task 3.3: Defense Analysis

Research and discuss potential mitigations:

1. **Server Configuration**: How can HTTP/2 settings be tuned to resist these attacks?
2. **Rate Limiting**: What rate limiting strategies work against HTTP/2 attacks?
3. **Flow Control Limits**: How can servers protect against flow control exploitation?

---

## Submission Requirements

### Code Submissions

1. Completed `http2_app_flood.py` with all FILL CODE HERE sections implemented
2. Completed `flow_control_zero_window.py` with all sections implemented  
3. Completed `flow_control_slow_increment.py` with all sections implemented
4. Analysis scripts for performance measurement

### Lab Report

Write a comprehensive report addressing:

1. **Attack Implementation**: Describe your implementation approach for each attack
2. **Effectiveness Analysis**: Compare attack effectiveness using metrics and graphs
3. **Resource Impact**: Document server resource consumption during attacks
4. **Evasion Techniques**: Discuss how attacks can evade detection
5. **Mitigation Strategies**: Propose and evaluate potential defenses
6. **Ethical Implications**: Discuss responsible disclosure and legal considerations

### Demonstration

Prepare a 15-minute demonstration showing:
1. Successful execution of both attack types
2. Performance impact measurement
3. Server resource monitoring during attacks
4. Discussion of results and implications

---

## Technical Hints and Guidelines

### HTTP/2 Protocol Considerations

- **Stream IDs**: Must be odd numbers for client-initiated streams
- **Flow Control**: Both connection and stream level windows must be considered
- **Settings Exchange**: Proper settings negotiation is crucial for attack success
- **Error Handling**: Implement proper error handling to maintain connections

### Python Implementation Tips

- **h2 Library**: Use the `h2` library for HTTP/2 protocol handling
- **Asynchronous I/O**: Consider using `asyncio` for handling multiple connections
- **Socket Programming**: Direct socket manipulation may be needed for advanced attacks
- **Threading**: Use threading for concurrent attack streams

### Performance Monitoring

- **Docker Stats**: Use `docker stats` to monitor container resource usage
- **Network Tools**: Use `ss`, `netstat`, and `tcpdump` for connection analysis
- **System Monitoring**: Monitor host system resources during attacks

### Safety and Ethics

- **Controlled Environment**: Only run attacks in isolated lab environments
- **Legal Compliance**: Ensure all testing complies with local laws and policies
- **Responsible Disclosure**: Understand principles of responsible vulnerability disclosure
- **Academic Use Only**: These techniques are for educational purposes only

---

## Troubleshooting

### Common Issues

**Connection Refused**: 
- Verify the HTTP/2 server is running
- Check port availability (default: 8080)
- Ensure Docker containers are properly networked

**HTTP/2 Negotiation Failures**:
- Verify HTTP/2 support in your client library
- Check ALPN negotiation
- Ensure proper protocol version negotiation

**Attack Not Effective**:
- Monitor actual server resource usage
- Verify attack traffic is reaching the server
- Check server configuration and limits

### Debugging Tips

- Use Wireshark to capture and analyze HTTP/2 traffic
- Enable verbose logging in both client and server
- Monitor server logs for error messages and connection statistics
- Use curl with HTTP/2 support for testing basic connectivity

---

## References and Further Reading

1. RFC 7540: Hypertext Transfer Protocol Version 2 (HTTP/2)
2. RFC 7541: HPACK: Header Compression for HTTP/2
3. HTTP/2 Security Considerations
4. DDoS Attack Vectors and Mitigation Strategies
5. Network Protocol Security Analysis

---

**Lab Authors**: Ohad Libai and Roei Ben Zion
**Version**: 1.0  
**Last Updated**: 2025

*This lab is designed for educational purposes only. All attacks should be performed only in controlled, authorized environments.*
