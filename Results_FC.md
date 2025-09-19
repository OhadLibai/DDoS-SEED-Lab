# Flow Control Attack Results

---

## Host: 34.31.183.135

### Zero Window Attack
| Metric | Result |
|--------|--------|
| Curl single request | **0.2099 s** |
| Connection state | `2 tcp` |
| Docker Net I/O | `http2-apache-zero-window   2.04MB / 1.22MB` |

### Slow Incremental Attack  
| Metric | Result |
|--------|--------|
| Curl single request | **0.209578 s** |
| Connection state | `2` |
| Docker Net I/O | `http2-apache-slow-incremental   1.11MB / 629kB` |

### Adaptive Slow Attack
| Metric | Result |
|--------|--------|
| Curl single request | Same as slow incremental |
| Connection state | Same as slow incremental |
| Docker Net I/O | Same as slow incremental |

---

## Attack Commands Used
```bash
# Flow control measurement
curl -w "Response: %{time_total}s\n" -s -o /dev/null http://34.31.183.135/

# Connection state breakdown
ss -tuln | grep ':80' | awk '{print $1}' | sort | uniq -c

# Monitor network I/O (bytes per second)
docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"

# Zero window attack
./deploy-attack.sh zero-window 34.31.183.135 --connections 512
```

---

## Observations
- **Response times**: All attacks show similar response times (~0.21s), indicating minimal impact on server performance
- **Network I/O**: Zero window attack generates higher traffic (2.04MB/1.22MB) compared to slow incremental (1.11MB/629kB)
- **Connection count**: Consistently low (2 connections), suggesting effective connection limiting or attack mitigation
- **Attack effectiveness**: Limited success - server maintains normal response times and low connection counts across all flow control attack variants