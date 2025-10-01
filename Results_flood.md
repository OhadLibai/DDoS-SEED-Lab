# HTTP Flood Experiment Results

---

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **214.720336 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `55b956792a6c   dev-victim-server   493.87% CPU   50.08MiB / 554.9MiB (9.03%)   11.6MB / 992kB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |

### Advanced
| Metric | Result |
|--------|--------|
| Curl single request | **10.6710 s** |
| Health check JSON | Same as Basic |
| Docker stats | `55b956792a6c   dev-victim-server   476.25% CPU   44.5MiB / 554.9MiB (8.02%)   13.1MB / 1.72MB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |
---

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **0.895640 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `483fa40bb883   prod-victim-server   0.00% CPU   32.33MiB / 554.9MiB (5.83%)   5.82kB / 4.66kB Net I/O   35.4MB / 299kB Block I/O   PIDS:1` |

### Advanced
Similar (qualitative) results as basic attack. 

---
