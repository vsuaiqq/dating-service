#!/bin/bash

set -e

ENV=${1:-dev}

case "$ENV" in
  dev)
    echo "Starting in DEV mode..."
    docker compose up --build
    ;;
  prod)
    echo "Starting in PROD mode..."
    docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
    ;;
  *)
    echo "Unknown mode: $ENV"
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
    ;;
esac
