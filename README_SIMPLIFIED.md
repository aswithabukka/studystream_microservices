# StudyStream - Microservices Portfolio Project (Medium Scope)

> A practical, interview-ready microservices application demonstrating backend engineering fundamentals

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

## 📋 Table of Contents

- [Overview](#overview)
- [Simplified Architecture](#simplified-architecture)
- [Tech Stack](#tech-stack)
- [Services](#services)
- [Getting Started](#getting-started)
- [Development](#development)
- [Testing](#testing)
- [Resume Highlights](#resume-highlights)

## 🎯 Overview

**StudyStream** is a microservices-based platform for managing study resources. This project demonstrates:

- ✅ **4 focused microservices** with clear responsibilities
- ✅ **RESTful communication** between services
- ✅ **JWT authentication** across services
- ✅ **Docker containerization** with docker-compose
- ✅ **Clean architecture** with proper separation of concerns
- ✅ **Comprehensive testing** with pytest
- ✅ **Background task processing** with FastAPI

**Build Time**: 1-2 weeks | **Lines of Code**: ~3000-4000 | **Realistic & Interview-Ready**

## 🏗️ Simplified Architecture

### Service Overview (4 Services)

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────────────┐
│     NGINX API Gateway (Port 80)          │
│  Routes: /auth, /users, /tasks, /notify  │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴───────────┬──────────────┬─────────────┐
       │                   │              │             │
       ▼                   ▼              ▼             ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Auth Service │   │ User Service │   │ Task Service │   │ Notification │
│  Port 8001   │   │  Port 8002   │   │  Port 8003   │   │   Service    │
│              │   │              │   │              │   │  Port 8004   │
│ - Register   │   │ - Profiles   │   │ - CRUD Tasks │   │              │
│ - Login      │   │ - Settings   │   │ - Metadata   │   │ - Send Email │
│ - JWT Issue  │   │ - Cache      │   │ - Rich Data  │   │ - History    │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                   │                  │
       │                  │                   │                  │
       │                  │                   │ REST Call        │
       │                  │                   │ (Background)     │
       │                  │                   ├─────────────────>│
       │                  │                   │                  │
       ▼                  ▼                   ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   auth_db    │   │   user_db    │   │   task_db    │   │ notification │
│ (PostgreSQL) │   │ (PostgreSQL) │   │ (PostgreSQL) │   │     _db      │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
       │                  │                   │                  │
       └──────────────────┴───────────────────┴──────────────────┘
                          │
                          ▼
                  ┌───────────────┐
                  │ Redis Cache   │
                  │ (Shared)      │
                  └───────────────┘
```

### Communication Pattern: REST Only

**No Message Queues** - Instead we use:
1. **Synchronous REST calls** for critical operations (e.g., User Service validates JWT with Auth Service)
2. **Background tasks** for non-critical operations (e.g., Task Service notifies Notification Service)

```python
# Example: Task Service calling Notification Service in background
from fastapi import BackgroundTasks
import httpx

async def notify_task_created(user_id: str, task_id: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{NOTIFICATION_SERVICE_URL}/notifications/send",
            json={
                "user_id": user_id,
                "type": "task_created",
                "task_id": task_id
            }
        )

@router.post("/tasks")
async def create_task(task: TaskCreate, background_tasks: BackgroundTasks):
    # Store task in database
    new_task = await task_repository.create(task)
    
    # Notify in background (non-blocking)
    background_tasks.add_task(notify_task_created, task.user_id, new_task.id)
    
    return new_task
```

### Key Design Decisions

| Aspect | Decision | Reasoning |
|--------|----------|-----------|
| **# of Services** | 4 services | Enough to show microservices without overwhelming complexity |
| **Communication** | REST with httpx | Simple, debuggable, no message broker overhead |
| **Async Operations** | FastAPI BackgroundTasks | Built-in, no external dependencies |
| **Deployment** | Docker Compose | Easy local dev, realistic for SDE interviews |
| **Databases** | 4 separate PostgreSQL DBs | Database-per-service pattern |
| **Caching** | Shared Redis | Simple setup, optional but recommended |

## 🛠️ Tech Stack

### Core Technologies
- **Language**: Python 3.11+
- **Framework**: FastAPI (async REST APIs)
- **Auth**: JWT (PyJWT)
- **Validation**: Pydantic v2

### Data Layer
- **Primary DB**: PostgreSQL 15 (4 databases, one per service)
- **Cache**: Redis 7 (optional but recommended)
- **ORM**: SQLAlchemy 2.0

### Inter-Service Communication
- **HTTP Client**: httpx (async)
- **Background Tasks**: FastAPI BackgroundTasks
- **No message queues** (simplified from original design)

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Gateway**: NGINX (simple reverse proxy)

### Testing & Quality
- **Testing**: Pytest + pytest-asyncio
- **Coverage**: pytest-cov
- **Linting**: flake8, black (optional)

### CI/CD
- **Pipeline**: GitHub Actions
- **Tasks**: Run tests, build images

## 🔧 Services

### 1. Auth Service (Port 8001)

**Purpose**: Authentication & authorization

**Responsibilities:**
- User registration with bcrypt password hashing
- Login with JWT token generation
- Token validation for other services

**Database**: `auth_db`
```sql
users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  password_hash VARCHAR,
  created_at TIMESTAMP
)
```

**Key Endpoints:**
- `POST /auth/register` - Create user
- `POST /auth/login` - Get JWT
- `GET /auth/me` - Current user (protected)
- `POST /auth/verify` - Validate token (internal use)

**Dependencies**: PostgreSQL, Redis (for token blacklist)

---

### 2. User Service (Port 8002)

**Purpose**: User profile & settings management

**Responsibilities:**
- Manage user profiles
- Store preferences
- Cache frequently accessed data

**Database**: `user_db`
```sql
user_profiles (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE,  -- References auth_db.users.id
  bio TEXT,
  avatar_url VARCHAR,
  preferences JSONB,
  created_at TIMESTAMP
)
```

**Key Endpoints:**
- `GET /users/{user_id}` - Get profile
- `PATCH /users/{user_id}` - Update profile (protected)

**Dependencies**: PostgreSQL, Redis (caching), Auth Service (JWT validation)

**Cache Strategy:**
- User profiles cached with 5-minute TTL
- Cache invalidation on profile updates

---

### 3. Task Service (Port 8003)

**Purpose**: Study resource & task management

**Responsibilities:**
- CRUD operations for tasks/resources
- Support multiple resource types (notes, links, videos, files)
- Rich metadata storage
- Call Notification Service on task creation

**Database**: `task_db`
```sql
tasks (
  id UUID PRIMARY KEY,
  user_id UUID,
  title VARCHAR,
  content TEXT,
  task_type VARCHAR,  -- note, link, video, file
  metadata JSONB,     -- Flexible additional data
  status VARCHAR,     -- active, completed, archived
  created_at TIMESTAMP,
  updated_at TIMESTAMP
)
```

**Key Endpoints:**
- `POST /tasks` - Create task (protected)
- `GET /tasks` - List tasks with filters
- `GET /tasks/{id}` - Get task
- `PUT /tasks/{id}` - Update task (protected)
- `DELETE /tasks/{id}` - Delete task (protected)

**Dependencies**: PostgreSQL, Auth Service (JWT), Notification Service (REST calls)

**Background Operations:**
- On task creation → Notify user via Notification Service (background task)

---

### 4. Notification Service (Port 8004)

**Purpose**: User notifications & communication

**Responsibilities:**
- Receive notification requests via REST
- Send notifications (simulated email)
- Store notification history

**Database**: `notification_db`
```sql
notifications (
  id UUID PRIMARY KEY,
  user_id UUID,
  notification_type VARCHAR,
  title VARCHAR,
  content TEXT,
  is_read BOOLEAN,
  sent_at TIMESTAMP
)
```

**Key Endpoints:**
- `POST /notifications/send` - Send notification (internal)
- `GET /notifications` - List user notifications (protected)
- `PATCH /notifications/{id}/read` - Mark as read

**Dependencies**: PostgreSQL

**Notification Types:**
- `welcome` - User registration
- `task_created` - New task created
- `task_updated` - Task modified
- `reminder` - Due date reminders

---

## 🚀 Getting Started

### Prerequisites

- Docker Desktop (20.10+)
- Docker Compose (2.0+)
- Python 3.11+ (for local development)
- Git

### Quick Start

```bash
# 1. Clone repository
git clone https://github.com/yourusername/studystream-microservices.git
cd studystream-microservices

# 2. Create environment file
cp .env.example .env

# 3. Start all services
cd infra
docker-compose up --build

# 4. Wait for services to be healthy (30-60 seconds)

# 5. Verify services
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # User Service
curl http://localhost:8003/health  # Task Service
curl http://localhost:8004/health  # Notification Service

# 6. Access interactive API docs
# Open browser: http://localhost:8001/docs (and 8002, 8003, 8004)
```

### Project Structure

```
studystream-microservices/
├── services/
│   ├── auth_service/
│   │   ├── app/
│   │   │   ├── main.py           # FastAPI app
│   │   │   ├── models.py         # SQLAlchemy models
│   │   │   ├── schemas.py        # Pydantic schemas
│   │   │   ├── routes.py         # API endpoints
│   │   │   ├── auth.py           # JWT logic
│   │   │   ├── database.py       # DB connection
│   │   │   └── config.py         # Settings
│   │   ├── tests/
│   │   │   ├── test_auth.py
│   │   │   └── test_routes.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── README.md
│   ├── user_service/
│   │   └── (same structure)
│   ├── task_service/
│   │   └── (same structure)
│   └── notification_service/
│       └── (same structure)
├── gateway/
│   └── nginx.conf                # NGINX config
├── infra/
│   ├── docker-compose.yml        # Main orchestration
│   └── scripts/
│       └── init-db.sh
├── docs/
│   ├── architecture.md           # Simplified architecture
│   ├── api-specs.md              # API documentation
│   └── development.md
├── .github/
│   └── workflows/
│       └── ci.yml                # GitHub Actions
├── .env.example
├── .gitignore
└── README.md
```

## 💻 Development

### Running Services Individually

```bash
# Navigate to service
cd services/auth_service

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/auth_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key"

# Run service
uvicorn app.main:app --reload --port 8001
```

### Common Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f auth_service

# Restart service
docker-compose restart auth_service

# Rebuild and restart
docker-compose up -d --build auth_service

# Stop all
docker-compose down

# Clean everything (including volumes)
docker-compose down -v
```

## 🧪 Testing

### Run All Tests

```bash
# From project root
pytest services/*/tests/ -v --cov

# Or use docker-compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

### Run Tests for Specific Service

```bash
cd services/auth_service
pytest tests/ -v --cov=app --cov-report=html
```

### Test Coverage

Target: **80%+ coverage** for all services

```bash
# Generate coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## 📝 Environment Variables

Key variables (see `.env.example` for complete list):

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Database URLs
AUTH_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/auth_db
USER_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/user_db
TASK_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/task_db
NOTIFICATION_DATABASE_URL=postgresql://postgres:postgres@postgres:5432/notification_db

# Redis
REDIS_URL=redis://redis:6379/0

# Service URLs (for inter-service communication)
AUTH_SERVICE_URL=http://auth_service:8001
USER_SERVICE_URL=http://user_service:8002
TASK_SERVICE_URL=http://task_service:8003
NOTIFICATION_SERVICE_URL=http://notification_service:8004
```

## 🎓 Resume Highlights

Use these for your resume/LinkedIn:

### Project Description
```
StudyStream - Microservices Application with REST APIs

• Architected 4-service microservices system with FastAPI and Python demonstrating 
  separation of concerns and independent deployability
• Implemented JWT-based authentication with bcrypt password hashing and token validation 
  across services
• Designed RESTful inter-service communication using httpx with async/await patterns
• Built database-per-service architecture with PostgreSQL and Redis caching layer
• Containerized all services with Docker and orchestrated using Docker Compose
• Implemented background task processing with FastAPI for non-blocking operations
• Achieved 80%+ test coverage using pytest with unit and integration tests
• Built CI/CD pipeline with GitHub Actions for automated testing

Technologies: Python, FastAPI, PostgreSQL, Redis, Docker, JWT, httpx, pytest
```

### Bullet Points for Resume

- Architected **4-microservice REST API system** with FastAPI serving 15+ endpoints with async patterns
- Implemented **JWT authentication** and **bcrypt password hashing** with token validation across services
- Designed **database-per-service pattern** with PostgreSQL and proper schema design using SQLAlchemy ORM
- Integrated **Redis caching** reducing database queries by 60% for frequently accessed user profiles
- Built **inter-service communication** using httpx async client and FastAPI BackgroundTasks
- Containerized services with **Docker** and orchestrated with **Docker Compose** using health checks
- Achieved **85% test coverage** using **pytest** with unit, integration, and API tests
- Established **CI/CD pipeline** with **GitHub Actions** for automated testing and Docker image builds

### Interview Talking Points

1. **Architecture**: "4-service microservices with clear separation - Auth, User, Task, Notification"
2. **Communication**: "REST-based with httpx for sync calls, BackgroundTasks for async operations"
3. **Auth**: "JWT tokens validated by all services using shared secret"
4. **Database**: "Database-per-service pattern, each service owns its data"
5. **Performance**: "Redis caching with strategic TTLs and invalidation"
6. **Testing**: "Comprehensive pytest suite with 80%+ coverage"

## 📚 Documentation

- **[Simplified Architecture](docs/architecture_simplified.md)** - System design & patterns
- **[API Specifications](docs/api-specs_simplified.md)** - Complete API docs
- **[Development Guide](docs/development.md)** - Setup & workflows
- **[Testing Guide](docs/testing.md)** - Test strategy

## 🔮 Future Enhancements

These are **optional** additions you can mention in interviews:

- Add Kubernetes deployment manifests (show you understand K8s)
- Implement Prometheus metrics (observability)
- Add gRPC for performance-critical calls (show versatility)
- Message queue for better decoupling (RabbitMQ/Kafka)
- API versioning strategy
- Rate limiting per user
- Distributed tracing with OpenTelemetry

**But the core project is complete without these** - they're "nice to haves" not "must haves".

## 🤝 Contributing

This is a portfolio project. Feedback welcome!

## 📄 License

MIT License - see LICENSE file

## 👤 Author

**Your Name**
- GitHub: [@yourusername](https://github.com/yourusername)
- LinkedIn: [Your Profile](https://linkedin.com/in/yourprofile)

---

⭐ **This is a realistic, buildable microservices project perfect for SDE interviews!**

**Estimated Build Time**: 1-2 weeks | **Complexity**: Medium | **Interview Impact**: High
