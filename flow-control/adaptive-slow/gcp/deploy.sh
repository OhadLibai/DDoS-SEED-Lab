#!/bin/bash
# adaptive-slow GCP Deployment
# Uses shared deployment script

# Call shared deployment script with lab-specific parameters
../../shared/gcp/deploy-base.sh "adaptive-slow" "2.4.62" "adv_slow_inc_window_attack.py" "512"