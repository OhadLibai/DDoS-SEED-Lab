# Flow Control — Test Report
---

## Table of contents
1. [Overview](#overview)  
2. [Commands (runbook)](#commands-runbook)  
3. [Captured Results (provided)](#captured-results-provided)  
4. [Zero-window attack — snapshot results](#zero-window-attack---snapshot-results)  
5. [Slow incremental attack — snapshot results](#slow-incremental-attack---snapshot-results)  
6. [Observations & quick analysis](#observations--quick-analysis)  
7. [Recommended next steps / data collection playbook](#recommended-next-steps--data-collection-playbook)  
8. [Scripts / one-liners to capture more data](#scripts--one-liners-to-capture-more-data)  
9. [Appendix — placeholders for extra pasted outputs](#appendix--placeholders-for-extra-pasted-outputs)

---

## Overview

This single-file report organizes the flow-control checks and attack snapshots you ran against the Apache/HTTP2 test hosts. It includes the commands you used, the outputs you already provided, quick analysis, and recommended next steps for deeper troubleshooting (socket-level captures, time-series net I/O, and Apache worker checks).

---

## Commands (runbook)

Use these to reproduce checks and collect more data during/after an attack.

### Quick response check
```bash
curl -w "Response: %{time_total}s\n" -s -o /dev/null http://34.31.183.135/
