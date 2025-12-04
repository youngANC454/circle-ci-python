#!/bin/bash

cat > infrastructure/scripts/stop_services.sh << 'STOPEOF'
#!/bin/bash
# stop_services.sh - Stop all services

set -e

echo "Stopping CI/CD AI Optimizer services..."

docker-compose down

echo ""
echo "Services stopped successfully!"
echo ""
echo "To remove volumes (WARNING: deletes all data):"
echo "  docker-compose down -v"
echo ""
STOPEOF

chmod +x infrastructure/scripts/stop_services.sh
