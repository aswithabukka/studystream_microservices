# StudyStream - Quick Start Guide

Get the microservices system up and running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Git
- 8GB RAM minimum
- Ports available: 80, 5432, 6379, 5672, 8001-8005, 9090, 3000, 15672

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/studystream-microservices.git
cd studystream-microservices
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env if needed (optional for local dev)
# Default values work out of the box
```

### 3. Run Setup Script

```bash
# Make script executable (if not already)
chmod +x scripts/setup.sh

# Run automated setup
./scripts/setup.sh
```

This script will:
- ✅ Check Docker installation
- ✅ Build all service images
- ✅ Start infrastructure (PostgreSQL, Redis, RabbitMQ)
- ✅ Start all microservices
- ✅ Perform health checks
- ✅ Display service URLs

**Alternative: Manual Setup**

```bash
cd infra

# Build images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Verify Installation

### Check Service Health

```bash
# Auth Service
curl http://localhost:8001/health

# User Service
curl http://localhost:8002/health

# Task Service
curl http://localhost:8003/health

# Notification Service
curl http://localhost:8004/health

# LLM Service
curl http://localhost:8005/health
```

All should return: `{"status": "healthy", ...}`

### Access Interactive API Documentation

Open in browser:
- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Task Service: http://localhost:8003/docs
- Notification Service: http://localhost:8004/docs
- LLM Service: http://localhost:8005/docs

### Access Monitoring Tools

- **RabbitMQ Management UI**: http://localhost:15672
  - Username: `guest`
  - Password: `guest`

- **Prometheus**: http://localhost:9090
  - Check targets: http://localhost:9090/targets

- **Grafana**: http://localhost:3000
  - Username: `admin`
  - Password: `admin`

## Quick API Test

### 1. Register a User

```bash
curl -X POST http://localhost:8001/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

**Response**: You'll get a JWT token

### 2. Login

```bash
curl -X POST http://localhost:8001/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!"
  }'
```

Save the `access_token` from the response.

### 3. Create a Task (Protected Endpoint)

```bash
TOKEN="your_token_here"

curl -X POST http://localhost:8003/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Learn Docker",
    "content": "Complete Docker tutorial",
    "task_type": "note"
  }'
```

### 4. Get Your Tasks

```bash
curl -X GET "http://localhost:8003/tasks?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Check Notifications

```bash
curl -X GET http://localhost:8004/notifications \
  -H "Authorization: Bearer $TOKEN"
```

You should see a welcome notification!

## Common Commands

### Start/Stop Services

```bash
# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Restart a specific service
docker-compose restart auth_service

# Rebuild and restart a service
docker-compose up -d --build auth_service
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f auth_service

# Last 100 lines
docker-compose logs --tail=100 auth_service
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U postgres -d auth_db

# List databases
docker-compose exec postgres psql -U postgres -c "\l"
```

### Redis Access

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Check keys
docker-compose exec redis redis-cli KEYS "*"
```

### RabbitMQ

```bash
# List queues
docker-compose exec rabbitmq rabbitmqctl list_queues

# List exchanges
docker-compose exec rabbitmq rabbitmqctl list_exchanges
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service_name

# Check if port is already in use
lsof -i :8001  # Replace with your port

# Restart Docker Desktop
```

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### "Out of Memory" Errors

```bash
# Check Docker resources
docker stats

# Increase Docker Desktop memory:
# Docker Desktop → Preferences → Resources → Memory (8GB+)
```

### Reset Everything

```bash
# Stop and remove all containers, volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Start fresh
./scripts/setup.sh
```

## Project Structure

```
studystream-microservices/
├── services/          # Microservices code
├── infra/            # Docker Compose, K8s configs
├── gateway/          # NGINX API Gateway
├── docs/             # Documentation
├── scripts/          # Utility scripts
└── README.md         # Main documentation
```

## Next Steps

1. **Explore the API**: Use the interactive docs at `/docs` endpoints
2. **Read the Architecture**: See `docs/architecture.md`
3. **Review API Specs**: See `docs/api-specs.md`
4. **Implement Services**: Start with Auth Service (Phase 2)
5. **Add Tests**: Write pytest tests for each service
6. **Deploy to K8s**: Use Kubernetes manifests (Phase 5)

## Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **Docker Compose**: https://docs.docker.com/compose/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Redis**: https://redis.io/documentation
- **RabbitMQ**: https://www.rabbitmq.com/tutorials.html

## Support

- Read the docs: `docs/` folder
- Check issues: GitHub issues (once repository is created)
- Architecture questions: `docs/architecture.md`
- API questions: `docs/api-specs.md`

---

**Happy coding! 🚀**

For detailed implementation guides, proceed to Phase 2 in `docs/PHASE_1_SUMMARY.md`.
