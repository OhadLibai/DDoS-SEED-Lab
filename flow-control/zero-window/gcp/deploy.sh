#!/bin/bash
# zero-window GCP Deployment
# Uses shared deployment script

# Call shared deployment script with lab-specific parameters
../../shared/gcp/deploy-base.sh "zero-window" "2.4.55" "zero_window_attack.py" "512"