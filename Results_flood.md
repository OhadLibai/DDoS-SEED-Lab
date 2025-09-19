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
| 10 curl runs | `116.848788s, 138.497857s, ...` |
| H2-Time | **168.487584 s** |
| `ss` timer output | No response |
| Docker logs (tail) | `[2025-09-19 08:52:17 +0000] [1] [INFO] Running on http://0.0.0.0:80 (CTRL + C to quit)` |
| `/proc/net/tcp` count | **4** |

### Advanced
| Metric | Result |
|--------|--------|
| Curl single request | **10.6710 s** |
| Health check JSON | Same as Basic |
| Docker stats | `55b956792a6c   dev-victim-server   476.25% CPU   44.5MiB / 554.9MiB (8.02%)   13.1MB / 1.72MB Net I/O   34.9MB / 709kB Block I/O   PIDS:1` |
| Docker Net I/O | `dev-victim-server   13.2MB / 1.77MB` |
| 10 curl runs | `11.052528s, 11.217986s, 11.003563s, 10.980951s, 11.231363s, 11.023290s, 10.958044s, 11.010556s, 11.000600s, 10.983076s` |
| H2-Time | **11.198685 s** |
| `ss` timer output | No response |
| Docker logs (tail) | `[2025-09-19 08:52:17 +0000] [1] [INFO] Running on http://0.0.0.0:80 (CTRL + C to quit` |
| `/proc/net/tcp` count | **8** |

---

## Part B — Host: 34.31.183.135

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **0.895640 s** |
| Health check JSON | `{"WORKLOAD":5,"message":"Server is running","protocol":"HTTP/2","scenario":"default_scenario","status":"healthy"}` |
| Docker stats | `483fa40bb883   prod-victim-server   0.00% CPU   32.33MiB / 554.9MiB (5.83%)   5.82kB / 4.66kB Net I/O   35.4MB / 299kB Block I/O   PIDS:1` |
| Docker Net I/O | `prod-victim-server   6.01kB / 4.92kB` |
| 10 curl runs | `0.444725s, 0.442419s, 0.446541s, 0.454321s, 0.439549s, 0.441227s, 0.439857s, 0.441172s, 0.437680s, 0.444202s` |
| H2-Time | **0.472098 s** |
| `ss` timer output | No response |
| Docker logs (tail) | `[2025-09-19 08:52:17 +0000] [1] [INFO] Running on http://0.0.0.0:80` |
| `/proc/net/tcp` count | Not provided |

### Advanced
_Not available / not provided in the results._

---

## Observations
- **Dev server (35.232.237.166)**: Very high latency in Basic (~200s) and still high in Advanced (~11s). CPU usage ~480–494% and large Net I/O.  
- **Prod server (34.31.183.135)**: Normal latency (~0.4–0.9s). CPU almost idle, very low Net I/O.  
- **TCP counts**: 4 (Basic) vs 8 (Advanced) on dev, not provided for prod.  
- **`ss` timer output** returned no data in all cases.  
