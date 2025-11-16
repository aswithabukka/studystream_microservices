# StudyStream - System Architecture

## Table of Contents
- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Service Interactions](#service-interactions)
- [Data Flow](#data-flow)
- [Authentication & Authorization](#authentication--authorization)
- [Database Design](#database-design)
- [Caching Strategy](#caching-strategy)
- [Message Queue Architecture](#message-queue-architecture)
- [Scalability & Performance](#scalability--performance)
- [Failure Modes & Resilience](#failure-modes--resilience)

## Overview

StudyStream is built using a **microservices architecture** where each service is:
- **Independently deployable**: Can be deployed without affecting other services
- **Loosely coupled**: Services communicate through well-defined APIs
- **Technology agnostic**: Each service can use different tech stacks (though we use Python/FastAPI consistently)
- **Business-capability focused**: Each service handles a specific domain (auth, tasks, notifications)

### Design Principles

1. **Single Responsibility**: Each service has one clear purpose
2. **API-First**: All inter-service communication through APIs (REST/gRPC)
3. **Database per Service**: Each service owns its data (no shared databases)
4. **Async Communication**: Use message queues for non-critical, eventual consistency needs
5. **Stateless Services**: Services don't store session state (use Redis/JWT)
6. **Observability**: Structured logging, metrics, and health checks built-in

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│   (Web Browser, Mobile App, Postman, curl, etc.)                │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         │ HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              NGINX Ingress Controller                    │   │
│  │  - Routing: /auth/* → Auth Service                      │   │
│  │           /users/* → User Service                       │   │
│  │           /tasks/* → Task Service                       │   │
│  │  - Load Balancing                                       │   │
│  │  - SSL Termination                                      │   │
│  │  - Rate Limiting                                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
         ▼               ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    Auth     │  │    User     │  │    Task     │  │ Notification│
│   Service   │  │   Service   │  │   Service   │  │   Service   │
│             │  │             │  │             │  │             │
│ Port: 8001  │  │ Port: 8002  │  │ Port: 8003  │  │ Port: 8004  │
│             │  │             │  │             │  │             │
│ - Register  │  │ - Profile   │  │ - CRUD      │  │ - Listen    │
│ - Login     │  │ - Settings  │  │   Tasks     │  │   Events    │
│ - JWT Gen   │  │ - Cache     │  │ - Filters   │  │ - Send      │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       │                │                │                │
       ▼                ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   auth_db    │ │   user_db    │ │   task_db    │ │notification_│
│ (PostgreSQL) │ │ (PostgreSQL) │ │ (PostgreSQL) │ │db (Postgres)│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
       │                │                │                │
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   Redis Cache        │
              │  - User sessions     │
              │  - Token blacklist   │
              │  - Profile cache     │
              └──────────────────────┘
                         │
                         ▼
              ┌──────────────────────────────┐
              │  Message Queue (RabbitMQ)    │
              │                               │
              │  Topics:                      │
              │  - user.registered            │
              │  - task.created               │
              │  - task.updated               │
              │  - task.deleted               │
              └──────────┬───────────────────┘
                         │
         ┌───────────────┴──────────────┐
         │                              │
         ▼                              ▼
┌─────────────────┐          ┌─────────────────┐
│  Notification   │          │   LLM Service   │
│    Service      │          │                 │
│  (Consumer)     │          │  Port: 8005     │
│                 │          │                 │
│  - user.reg     │          │  - Summarize    │
│  - task.*       │          │  - Study Plan   │
└─────────────────┘          │  - Mock LLM     │
                             └─────────┬───────┘
                                       │
                                       ▼
                             ┌──────────────────┐
                             │     llm_db       │
                             │  (PostgreSQL)    │
                             └──────────────────┘
```

### Technology Stack per Layer

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Gateway** | NGINX Ingress | Routing, Load Balancing, SSL |
| **Services** | FastAPI + Python 3.11 | REST APIs, Business Logic |
| **Databases** | PostgreSQL 15 | Persistent storage per service |
| **Cache** | Redis 7 | Session cache, profile cache |
| **Messaging** | RabbitMQ 3.12 | Async event-driven communication |
| **Containerization** | Docker | Service isolation |
| **Orchestration** | Kubernetes | Deployment, scaling, management |
| **Monitoring** | Prometheus + Grafana | Metrics and dashboards |
| **Logging** | JSON structured logs | Centralized logging |

## Service Interactions

### 1. User Registration Flow

```
┌────────┐      ┌─────────┐      ┌──────────┐      ┌──────────────┐
│ Client │      │   Auth  │      │ RabbitMQ │      │ Notification │
│        │      │ Service │      │          │      │   Service    │
└───┬────┘      └────┬────┘      └────┬─────┘      └──────┬───────┘
    │                │                │                    │
    │ POST /register │                │                    │
    ├───────────────>│                │                    │
    │                │                │                    │
    │                │ Hash password  │                    │
    │                │ Store in DB    │                    │
    │                │                │                    │
    │                │ Publish        │                    │
    │                │ 'user.reg'     │                    │
    │                ├───────────────>│                    │
    │                │                │                    │
    │    200 OK      │                │ Consume event      │
    │<───────────────┤                ├───────────────────>│
    │    + JWT       │                │                    │
    │                │                │    Send welcome    │
    │                │                │    email/notif     │
    │                │                │<───────────────────┤
```

**Steps:**
1. Client sends registration data (email, password)
2. Auth Service validates input
3. Auth Service hashes password (bcrypt)
4. Auth Service stores user in `auth_db`
5. Auth Service publishes `user.registered` event to RabbitMQ
6. Auth Service returns JWT token to client
7. Notification Service consumes event asynchronously
8. Notification Service sends welcome notification

### 2. Task Creation Flow (with JWT Auth)

```
┌────────┐   ┌──────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Client │   │ Task │   │   Auth   │   │ RabbitMQ │   │Analytics │
│        │   │Service│   │ Service  │   │          │   │ Service  │
└───┬────┘   └───┬──┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
    │            │            │               │              │
    │ POST /tasks│            │               │              │
    │ + JWT      │            │               │              │
    ├───────────>│            │               │              │
    │            │            │               │              │
    │            │ Validate   │               │              │
    │            │ JWT token  │               │              │
    │            │ (decode)   │               │              │
    │            │            │               │              │
    │            │ Store task │               │              │
    │            │ in task_db │               │              │
    │            │            │               │              │
    │            │ Publish    │               │              │
    │            │ 'task.created'             │              │
    │            ├───────────────────────────>│              │
    │            │            │               │              │
    │  201       │            │               │ Consume      │
    │  Created   │            │               ├─────────────>│
    │<───────────┤            │               │              │
    │            │            │               │ Update metrics│
```

**Steps:**
1. Client sends task data with JWT in `Authorization` header
2. Task Service extracts and validates JWT
3. Task Service decodes JWT to get `user_id`
4. Task Service stores task in `task_db`
5. Task Service publishes `task.created` event
6. Task Service returns task details to client
7. Analytics Service consumes event and updates metrics

### 3. User Profile Fetch (with Caching)

```
┌────────┐      ┌──────────┐      ┌───────┐      ┌──────────┐
│ Client │      │   User   │      │ Redis │      │ user_db  │
│        │      │ Service  │      │       │      │          │
└───┬────┘      └────┬─────┘      └───┬───┘      └────┬─────┘
    │                │                 │               │
    │ GET /users/123 │                 │               │
    ├───────────────>│                 │               │
    │                │                 │               │
    │                │ Check cache     │               │
    │                ├────────────────>│               │
    │                │                 │               │
    │                │  Cache MISS     │               │
    │                │<────────────────┤               │
    │                │                 │               │
    │                │  Query user                     │
    │                ├─────────────────────────────────>
    │                │                 │               │
    │                │  User data                      │
    │                │<─────────────────────────────────
    │                │                 │               │
    │                │ Store in cache  │               │
    │                │ (TTL 5 min)     │               │
    │                ├────────────────>│               │
    │                │                 │               │
    │   200 OK       │                 │               │
    │<───────────────┤                 │               │
```

**Subsequent requests hit cache:**
```
    │ GET /users/123 │
    ├───────────────>│
    │                │ Check cache
    │                ├────────────────>│
    │                │  Cache HIT      │
    │                │<────────────────┤
    │   200 OK       │
    │<───────────────┤
```

## Authentication & Authorization

### JWT Token Flow

**Token Structure:**
```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user_id_123",
    "email": "user@example.com",
    "exp": 1699564800,
    "iat": 1699561200
  },
  "signature": "..."
}
```

**Token Lifecycle:**
1. **Generation**: Auth Service creates JWT on successful login
2. **Distribution**: Token sent to client (usually stored in localStorage/cookie)
3. **Validation**: Each protected service validates token on every request
4. **Refresh**: Client requests new token before expiration (optional refresh token flow)
5. **Revocation**: Blacklist tokens in Redis for logout/security

**How Services Validate JWT:**

Each service has a shared secret (`JWT_SECRET_KEY`) or public key to validate tokens:

```python
# In each service's auth middleware
def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET_KEY, 
            algorithms=[JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")
```

### Authorization Levels

1. **Public Endpoints**: No authentication required
   - `POST /auth/register`
   - `POST /auth/login`

2. **Authenticated Endpoints**: Valid JWT required
   - `GET /users/{id}` (any authenticated user)
   - `GET /tasks` (see own tasks)

3. **Owner-Only Endpoints**: JWT + resource ownership check
   - `PATCH /users/{id}` (can only update own profile)
   - `DELETE /tasks/{id}` (can only delete own tasks)

4. **Admin Endpoints** (optional): JWT + admin role check
   - `GET /admin/users`
   - `POST /admin/notifications/broadcast`

## Database Design

### Auth Service Database (auth_db)

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### User Service Database (user_db)

```sql
-- User Profiles table
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,  -- References auth_db.users.id (logically)
    bio TEXT,
    avatar_url VARCHAR(512),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

### Task Service Database (task_db)

```sql
-- Tasks table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    task_type VARCHAR(50) DEFAULT 'note',  -- note, link, video, file
    metadata JSONB DEFAULT '{}',  -- Additional data (URL, file size, etc.)
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

### Notification Service Database (notification_db)

```sql
-- Notifications table
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    notification_type VARCHAR(100) NOT NULL,  -- welcome, task_created, reminder
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at);
```

### LLM Service Database (llm_db)

```sql
-- Summaries table
CREATE TABLE summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    task_ids UUID[] NOT NULL,  -- Array of task IDs summarized
    summary_text TEXT NOT NULL,
    model_used VARCHAR(100) DEFAULT 'mock-gpt',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_summaries_user_id ON summaries(user_id);
CREATE INDEX idx_summaries_created_at ON summaries(created_at);
```

## Caching Strategy

### What to Cache

1. **User Profiles** (User Service)
   - Key: `user:profile:{user_id}`
   - TTL: 5 minutes
   - Reason: Profiles rarely change, frequently accessed

2. **JWT Blacklist** (Auth Service)
   - Key: `jwt:blacklist:{token_id}`
   - TTL: Same as JWT expiration
   - Reason: Fast logout/revocation

3. **Task Lists** (Task Service)
   - Key: `user:tasks:{user_id}`
   - TTL: 1 minute
   - Reason: Tasks change frequently, short TTL

### Cache Invalidation

**Write-Through Pattern:**
```
Update Request → Update DB → Invalidate Cache → Return Response
```

**Lazy Loading Pattern:**
```
Read Request → Check Cache → If Miss: Read DB → Store in Cache → Return
```

## Message Queue Architecture

### RabbitMQ Setup

**Exchange Type**: Topic Exchange

**Topics:**
- `user.registered` - New user created
- `user.updated` - User profile updated
- `task.created` - New task created
- `task.updated` - Task modified
- `task.deleted` - Task removed
- `task.due_soon` - Task due date approaching (scheduled)

### Event Schema

**Standard Event Format:**
```json
{
  "event_id": "uuid",
  "event_type": "task.created",
  "timestamp": "2024-11-15T03:45:00Z",
  "payload": {
    "task_id": "uuid",
    "user_id": "uuid",
    "title": "Read Chapter 5",
    "type": "note"
  },
  "metadata": {
    "source_service": "task_service",
    "version": "1.0"
  }
}
```

### Producers & Consumers

| Service | Produces | Consumes |
|---------|----------|----------|
| Auth Service | `user.registered`, `user.updated` | - |
| Task Service | `task.created`, `task.updated`, `task.deleted` | - |
| Notification Service | - | All user/task events |
| Analytics Service | - | All events (optional) |
| LLM Service | - | `task.created` (optional trigger) |

## Scalability & Performance

### Horizontal Scaling

All services are **stateless** and can scale horizontally:

**Kubernetes Horizontal Pod Autoscaler (HPA):**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: task-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: task-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Database Optimization

1. **Connection Pooling**: SQLAlchemy with pool size 20, max overflow 10
2. **Indexes**: All foreign keys and frequently queried columns indexed
3. **Read Replicas**: PostgreSQL read replicas for read-heavy workloads (future)
4. **Partitioning**: Time-based partitioning for notifications/logs (future)

### Load Testing Targets

- **Throughput**: 1000 requests/second per service
- **Latency**: P95 < 200ms, P99 < 500ms
- **Availability**: 99.9% uptime

## Failure Modes & Resilience

### Circuit Breaker Pattern

Prevent cascading failures when a service is down:

```python
# Example with tenacity library
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_external_service():
    # Make HTTP call
    pass
```

### Health Checks

Each service implements:
- **Liveness Probe**: `/health/live` (Is the service running?)
- **Readiness Probe**: `/health/ready` (Can it handle traffic?)

### Graceful Degradation

**Scenario**: Notification Service is down
- **Impact**: Notifications not sent
- **Mitigation**: Events queued in RabbitMQ, processed when service recovers
- **User Experience**: No impact on core functionality (task CRUD still works)

**Scenario**: Redis is down
- **Impact**: Cache misses for all requests
- **Mitigation**: Fall back to database queries
- **User Experience**: Slower response times but no errors

### Retry Logic

**Message Queue Consumers:**
- Failed message processing → Retry 3 times with exponential backoff
- After 3 failures → Move to dead letter queue for manual review

**HTTP Inter-Service Calls:**
- Network errors → Retry 3 times
- 5xx errors → Retry 2 times
- 4xx errors → No retry (client error)

## Monitoring & Observability

### Metrics (Prometheus)

**Service-level metrics:**
- `http_requests_total{service, method, endpoint, status}`
- `http_request_duration_seconds{service, endpoint}`
- `db_connections_active{service, database}`
- `cache_hits_total{service}`
- `cache_misses_total{service}`
- `message_queue_messages_processed{service, topic}`

### Logging

**Structured JSON logs:**
```json
{
  "timestamp": "2024-11-15T03:45:23.123Z",
  "level": "INFO",
  "service": "task_service",
  "request_id": "abc-123-def",
  "user_id": "user-456",
  "message": "Task created successfully",
  "task_id": "task-789",
  "duration_ms": 45
}
```

### Tracing (Future)

OpenTelemetry for distributed tracing across services

---

**Next Steps**: See [API Specifications](api-specs.md) for detailed endpoint documentation.
