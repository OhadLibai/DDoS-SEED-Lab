# Flow Control Attack Results

### Basic
| Metric | Result |
|--------|--------|
| Curl single request | **Response: 0.103466s** |
| Docker stats | `55b956792a6c   http2-apache-zero-window   0.17% CPU   108.9MiB / 554.9MiB  (19.62%)   1.2MB / 747kB I/O   19.1MB / 28.7kB Block I/O   PIDS:657` |

### Advanced
| Metric | Result |
|--------|--------|
| Curl single request | **Response: 0.103885s** |
| Docker stats | cf8c7c0ff5d9 http2-apache-slow-incremental 0.01% CPU 10.77MiB / 554.9MiB (1.94%) 4.68kB / 3.64kB Net I/O 6.37MB / 28.7kB Block I/O PIDS:158 |

### Cloud
| Metric | Result |
|--------|--------|
| Curl single request | **Response: 0.104652s** |
| Docker stats | 5b32d1b44834 http2-apache-adaptive-slow 1.80% CPU 106.2MiB / 554.9MiB (19.15%) 912kB / 620kB Net I/O 10MB / 28.7kB Block I/O PIDS:657 |

---
