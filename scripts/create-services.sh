#!/bin/bash

# Script to create directory structure for all services
# Run this from the project root

set -e

echo "Creating service directory structures..."

SERVICES=("user_service" "task_service" "notification_service")

for SERVICE in "${SERVICES[@]}"; do
    echo "Creating structure for $SERVICE..."
    
    # Create directories
    mkdir -p services/$SERVICE/app
    mkdir -p services/$SERVICE/tests
    
    # Create __init__.py files
    touch services/$SERVICE/app/__init__.py
    touch services/$SERVICE/tests/__init__.py
    
    # Create main app files
    touch services/$SERVICE/app/main.py
    touch services/$SERVICE/app/models.py
    touch services/$SERVICE/app/schemas.py
    touch services/$SERVICE/app/routes.py
    touch services/$SERVICE/app/database.py
    touch services/$SERVICE/app/config.py
    touch services/$SERVICE/app/dependencies.py
    
    # Create test files
    touch services/$SERVICE/tests/conftest.py
    touch services/$SERVICE/tests/test_routes.py
    
    # Create other files
    touch services/$SERVICE/Dockerfile
    touch services/$SERVICE/requirements.txt
    touch services/$SERVICE/README.md
    
    echo "✅ $SERVICE structure created"
done

echo ""
echo "✅ All service structures created!"
echo ""
echo "Next steps:"
echo "1. Copy code from IMPLEMENTATION_GUIDE.md into each service"
echo "2. Update config.py for each service (ports, database URLs)"
echo "3. Implement routes.py following the patterns shown"
echo "4. Run: docker-compose -f infra/docker-compose-simplified.yml up --build"
