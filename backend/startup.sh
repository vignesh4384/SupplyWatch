#!/bin/bash
# Azure App Service startup script for SupplyWatch backend.

# Persistent data directory — /home survives deployments on Azure App Service
mkdir -p /home/data
export DB_PATH="/home/data/supplywatch.db"

# Azure sets PORT env var; default to 8000 if not set
PORT="${PORT:-8000}"

python -m gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:$PORT" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
