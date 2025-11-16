#!/bin/bash

# StudyStream Microservices Setup Script
# This script sets up the development environment

set -e

echo "========================================="
echo "StudyStream Microservices Setup"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo -n "Checking Docker installation... "
if ! command -v docker &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Docker is not installed. Please install Docker Desktop."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if Docker Compose is installed
echo -n "Checking Docker Compose installation... "
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}FAILED${NC}"
    echo "Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

# Check if Docker is running
echo -n "Checking if Docker is running... "
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}FAILED${NC}"
    echo "Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo -e "${GREEN}OK${NC}"

echo ""
echo "========================================="
echo "Environment Setup"
echo "========================================="

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file${NC}"
    echo -e "${YELLOW}Please update .env with your configuration before continuing${NC}"
    echo ""
    read -p "Press Enter to continue after updating .env, or Ctrl+C to exit..."
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

echo ""
echo "========================================="
echo "Building Docker Images"
echo "========================================="

cd infra

echo "Building services (this may take a few minutes)..."
docker-compose build

echo ""
echo "========================================="
echo "Starting Services"
echo "========================================="

echo "Starting infrastructure services (PostgreSQL, Redis, RabbitMQ)..."
docker-compose up -d postgres redis rabbitmq

echo "Waiting for infrastructure to be ready..."
sleep 10

echo "Starting microservices..."
docker-compose up -d auth_service user_service task_service notification_service llm_service

echo "Starting API Gateway..."
docker-compose up -d gateway

echo "Starting monitoring services..."
docker-compose up -d prometheus grafana

echo ""
echo "========================================="
echo "Checking Service Health"
echo "========================================="

sleep 5

services=("auth_service:8001" "user_service:8002" "task_service:8003" "notification_service:8004" "llm_service:8005")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    echo -n "Checking $name... "
    
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            echo -e "${GREEN}OK${NC}"
            break
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -eq $max_attempts ]; then
            echo -e "${RED}FAILED${NC}"
            echo "Service $name is not responding. Check logs with: docker-compose logs $name"
        fi
        
        sleep 1
    done
done

echo ""
echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "Services are running:"
echo "  - Auth Service:         http://localhost:8001/docs"
echo "  - User Service:         http://localhost:8002/docs"
echo "  - Task Service:         http://localhost:8003/docs"
echo "  - Notification Service: http://localhost:8004/docs"
echo "  - LLM Service:          http://localhost:8005/docs"
echo "  - API Gateway:          http://localhost:80"
echo ""
echo "Infrastructure:"
echo "  - RabbitMQ Management:  http://localhost:15672 (guest/guest)"
echo "  - Prometheus:           http://localhost:9090"
echo "  - Grafana:              http://localhost:3000 (admin/admin)"
echo ""
echo "Useful commands:"
echo "  - View logs:            docker-compose logs -f [service_name]"
echo "  - Stop all services:    docker-compose down"
echo "  - Restart a service:    docker-compose restart [service_name]"
echo "  - View running services: docker-compose ps"
echo ""
echo -e "${GREEN}Happy coding!${NC}"
