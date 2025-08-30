#!/bin/bash
# slow-incremental GCP Deployment
# Uses shared deployment script

# Call shared deployment script with lab-specific parameters
../../shared/gcp/deploy-base.sh "slow-incremental" "2.4.62" "slow_inc_window_attack.py" "512"