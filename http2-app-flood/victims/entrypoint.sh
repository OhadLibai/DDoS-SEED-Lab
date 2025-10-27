#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Check the value of the SERVER_TYPE environment variable.
if [ "$SERVER_TYPE" = "multi-worker" ]; then
    # Production: Run with Gunicorn with Uvicorn workers for better performance and multiple processes.
    echo "Starting production server (multi-worker)..."
    exec hypercorn --workers ${WORKERS:-4} --bind 0.0.0.0:80 victim_app:app
else
    # Development: Run the standard Quart development server (single-worker).
    echo "Starting development server (single-worker)..."
    exec python -u victim_app.py
fi