| Metric / Command | Zero window (attack: `zero-window 34.31.183.135 --connections 512`) | Slow incremental (`http2-apache-slow-incremental`) | Notes |
|---|---:|---:|---|
| `curl -w "Response: %{time_total}s\n" -s -o /dev/null http://34.31.183.135/` | **0.2099 s** | **0.209578 s** | Single-run response time |
| Connection state breakdown (`ss -tuln | grep ':80' | awk '{print $1}' | sort | uniq -c`) | **2 tcp** | **2** | Provided as `2 tcp` and `2` respectively |
| Docker Net I/O (`docker stats --no-stream --format "table {{.Name}}\t{{.NetIO}}"`) |  
`NAME                       NET I/O`  
`http2-apache-zero-window   2.04MB / 1.22MB` |  
`NAME                            NET I/O`  
`http2-apache-slow-incremental   1.11MB / 629kB` | Net I/O snapshot for the container(s) during the test |
| `watch -n 5 'docker stats ...'` (bandwidth over time) | N/A | N/A | No `watch` output pasted |
| Apache worker threads (`ps aux | grep apache2 | wc -l`) | N/A | N/A | No output provided |
| Apache status (`apache2ctl status`) | N/A | N/A | No output provided / Status module possibly unavailable |
| Latency distribution (5 × `curl -w "%{time_total}s\n" -o /dev/null -s http://localhost/`) | N/A | N/A | No 5-run list provided |
| Baseline vs current detection (script) | N/A | N/A | No baseline/current outputs provided |
| Connection lifetime (`ss -o | grep :80 | head -5`) | N/A | N/A | No `ss -o` output provided |
| Persistent connections (docker logs grep) | N/A | N/A | No log tail provided |
