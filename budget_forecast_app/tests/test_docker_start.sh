#!/bin/bash
set -e

echo "▶ Testing: Docker container starts correctly..."

docker-compose up -d --build

# Wait for container
sleep 5

# Check if container is running
if [ "$(docker ps -q -f name=django-forecast-container)" ]; then
    echo "✔ Container is running"
else
    echo "❌ Container failed to start"
    exit 1
fi

docker-compose down
