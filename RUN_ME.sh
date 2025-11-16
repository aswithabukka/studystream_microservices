#!/bin/bash

# Quick Start Script for StudyStream Microservices
# Run this from the project root

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  StudyStream Microservices - Quick Start"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check Docker
echo -n "Checking Docker... "
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker Desktop."
    exit 1
fi
echo "✅"

# Check Docker Compose
echo -n "Checking Docker Compose... "
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found."
    exit 1
fi
echo "✅"

# Check if Docker is running
echo -n "Checking if Docker is running... "
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Starting All Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd infra

echo "Building and starting services (this may take 2-3 minutes)..."
docker-compose -f docker-compose-simplified.yml up -d --build

echo ""
echo "Waiting for services to be healthy..."
sleep 20

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Service Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check each service
SERVICES=("auth_service:8001" "user_service:8002" "task_service:8003" "notification_service:8004")

for service in "${SERVICES[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "Checking $name... "
    
    if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Running${NC}"
    else
        echo -e "${YELLOW}⏳ Starting...${NC}"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 Services are running!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}Interactive API Documentation:${NC}"
echo "  • Auth Service:         http://localhost:8001/docs"
echo "  • User Service:         http://localhost:8002/docs"
echo "  • Task Service:         http://localhost:8003/docs"
echo "  • Notification Service: http://localhost:8004/docs"
echo ""
echo -e "${BLUE}Infrastructure:${NC}"
echo "  • RabbitMQ (not used):  -"
echo "  • PostgreSQL:           localhost:5432"
echo "  • Redis:                localhost:6379"
echo ""
echo -e "${YELLOW}Quick Test Commands:${NC}"
echo ""
echo "# 1. Register a user"
echo 'curl -X POST http://localhost:8001/auth/register \'
echo '  -H "Content-Type: application/json" \'
echo "  -d '{"
echo '    "email": "test@example.com",'
echo '    "password": "TestPass123!",'
echo '    "password_confirm": "TestPass123!"'
echo "  }'"
echo ""
echo "# 2. Save the access_token from response"
echo ""
echo "# 3. Create a task (replace YOUR_TOKEN)"
echo 'curl -X POST http://localhost:8003/tasks \'
echo '  -H "Content-Type: application/json" \'
echo '  -H "Authorization: Bearer YOUR_TOKEN" \'
echo "  -d '{"
echo '    "title": "Learn Docker",'
echo '    "content": "Complete tutorial",'
echo '    "task_type": "note"'
echo "  }'"
echo ""
echo "# 4. Check notifications"
echo 'curl http://localhost:8004/notifications \'
echo '  -H "Authorization: Bearer YOUR_TOKEN"'
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo "  • View logs:      docker-compose -f infra/docker-compose-simplified.yml logs -f"
echo "  • Stop all:       docker-compose -f infra/docker-compose-simplified.yml down"
echo "  • Restart:        docker-compose -f infra/docker-compose-simplified.yml restart"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Happy coding! 🚀"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
