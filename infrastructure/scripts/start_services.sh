#!/bin/bash
# start_services.sh - Start all services

set -e

echo "Starting CI/CD AI Optimizer services..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found"
    echo "Please run setup.sh first or copy .env.example to .env"
    exit 1
fi

# Start services
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Service Status:"
docker-compose ps

echo ""
echo "=========================================="
echo "Services started successfully!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "  - Grafana:    http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - API Docs:   http://localhost:8000/docs"
echo "  - Backend:    http://localhost:8000"
echo "  - ML Engine:  http://localhost:8001"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop services: ./infrastructure/scripts/stop_services.sh"
echo ""

