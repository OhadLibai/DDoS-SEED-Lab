# Flow Control Attack Results

### Zero Window
| Metric | Result |
|--------|--------|
| Curl single request | **curl: (7) Failed to connect to 34.58.142.149 port 8080 after 103 ms: Couldn't connect to server Time: 0.103466s** |
| Health check JSON | Not Reachable |
| Docker stats | `55b956792a6c   http2-apache-zero-window   0.17% CPU   108.9MiB / 554.9MiB  (19.62%)   1.2MB / 747kB I/O   19.1MB / 28.7kB Block I/O   PIDS:657` |

### Slow Incremental
| Metric | Result |
|--------|--------|
| Curl single request | **10.6710 s** |
| Health check JSON | Same as Basic |
| Docker stats | `55b956792a6c   dev-victim-server   476.25% CPU   44.5MiB / 554.9MiB (8.02%)   13.1MB / 1.72MB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |

### Adaptive Slow
| Metric | Result |
|--------|--------|
| Curl single request | **0.895640 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `483fa40bb883   prod-victim-server   0.00% CPU   32.33MiB / 554.9MiB (5.83%)   5.82kB / 4.66kB Net I/O   35.4MB / 299kB Block I/O   PIDS:1` |

---
