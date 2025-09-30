# HTTP Flood Experiment Results

---

## Part A — Host: 35.232.237.166

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **214.720336 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `55b956792a6c   dev-victim-server   493.87% CPU   50.08MiB / 554.9MiB (9.03%)   11.6MB / 992kB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |
| Docker Net I/O | `dev-victim-server   10.7MB / 937kB` |

### Advanced
| Metric | Result |
|--------|--------|
| Curl single request | **10.6710 s** |
| Health check JSON | Same as Basic |
| Docker stats | `55b956792a6c   dev-victim-server   476.25% CPU   44.5MiB / 554.9MiB (8.02%)   13.1MB / 1.72MB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |
| Docker Net I/O | `dev-victim-server   13.2MB / 1.77MB` |

---

## Part B — Host: 34.31.183.135

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **0.895640 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `483fa40bb883   prod-victim-server   0.00% CPU   32.33MiB / 554.9MiB (5.83%)   5.82kB / 4.66kB Net I/O   35.4MB / 299kB Block I/O   PIDS:1` |
| Docker Net I/O | `prod-victim-server   6.01kB / 4.92kB` |s

### Advanced
_Not available / not provided in the results._

---

## Observations
- **Dev server (35.232.237.166)**: Very high latency in Basic (~200s) and still high in Advanced (~11s). CPU usage ~480–494% and large Net I/O.  
- **Prod server (34.31.183.135)**: Normal latency (~0.4–0.9s). CPU almost idle, very low Net I/O.  
- **TCP counts**: 4 (Basic) vs 8 (Advanced) on dev, not provided for prod.  
- **`ss` timer output** returned no data in all cases.  
