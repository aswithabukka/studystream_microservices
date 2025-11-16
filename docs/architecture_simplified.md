# StudyStream - Simplified Architecture (Medium Scope)

## 🔄 Design Philosophy

**This is the SIMPLIFIED version** - focused on backend engineering fundamentals without heavy infrastructure complexity.

### What Changed from Complex Version

| Component | Complex Version | **Simplified Version** |
|-----------|----------------|----------------------|
| Services | 5 services | **4 services** |
| Communication | REST + gRPC + RabbitMQ | **REST only (httpx)** |
| Message Broker | RabbitMQ/Kafka | **None - BackgroundTasks** |
| Deployment | Kubernetes required | **Docker Compose** |
| Monitoring | Prometheus + Grafana | **Structured logging** |
| Complexity | Production infra | **Interview-focused** |

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                           │
│          (Web Browser, Mobile App, API Client)              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (NGINX)                        │
│                                                               │
│  Responsibilities:                                            │
│  - Route /auth/* → Auth Service                             │
│  - Route /users/* → User Service                            │
│  - Route /tasks/* → Task Service                            │
│  - Route /notifications/* → Notification Service            │
│  - Simple reverse proxy (no rate limiting in v1)            │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┬──────────────┐
         │               │               │              │
         ▼               ▼               ▼              ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│    Auth     │  │    User     │  │    Task     │  │Notification │
│   Service   │  │   Service   │  │   Service   │  │   Service   │
│             │  │             │  │             │  │             │
│ Port: 8001  │  │ Port: 8002  │  │ Port: 8003  │  │ Port: 8004  │
│             │  │             │  │             │  │             │
│ FastAPI     │  │ FastAPI     │  │ FastAPI     │  │ FastAPI     │
│ + SQLAlchemy│  │ + SQLAlchemy│  │ + SQLAlchemy│  │ + SQLAlchemy│
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       │                │                │                │
       ▼                ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   auth_db    │ │   user_db    │ │   task_db    │ │notification_│
│ (PostgreSQL) │ │ (PostgreSQL) │ │ (PostgreSQL) │ │db (Postgres)│
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │   Redis Cache    │
              │   (Shared)       │
              │  - User profiles │
              │  - Token blacklist│
              └──────────────────┘
```

---

## Service Details

### 1. Auth Service

**Port**: 8001  
**Database**: `auth_db`  
**External Dependencies**: Redis, PostgreSQL

**Core Responsibilities:**
- User registration with secure password hashing (bcrypt)
- User authentication and JWT token generation
- Token validation for other services
- Token revocation (logout)

**Database Schema:**
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
```

**Key APIs:**
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT
- `GET /auth/me` - Get current user (protected)
- `POST /auth/verify` - Verify JWT (internal use by other services)
- `POST /auth/logout` - Logout and blacklist token

**Implementation Notes:**
- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens expire after 60 minutes (configurable)
- Blacklisted tokens stored in Redis with TTL matching JWT expiration
- No refresh tokens in v1 (can be added later)

---

### 2. User Service

**Port**: 8002  
**Database**: `user_db`  
**External Dependencies**: Redis, PostgreSQL, Auth Service (REST)

**Core Responsibilities:**
- Manage user profiles (bio, avatar, preferences)
- Cache frequently accessed profiles
- Validate JWT tokens by calling Auth Service

**Database Schema:**
```sql
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE NOT NULL,  -- References auth_db.users.id
    bio TEXT,
    avatar_url VARCHAR(512),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
```

**Key APIs:**
- `GET /users/{user_id}` - Get user profile
- `PATCH /users/{user_id}` - Update profile (owner only)

**Caching Strategy:**
```python
# Cache key format: user:profile:{user_id}
# TTL: 300 seconds (5 minutes)

async def get_user_profile(user_id: str):
    # Try cache first
    cache_key = f"user:profile:{user_id}"
    cached = await redis.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Cache miss - query database
    profile = await db.query(UserProfile).filter_by(user_id=user_id).first()
    
    # Store in cache
    await redis.setex(cache_key, 300, json.dumps(profile.dict()))
    
    return profile

async def update_user_profile(user_id: str, updates: dict):
    # Update database
    profile = await db.query(UserProfile).filter_by(user_id=user_id).first()
    for key, value in updates.items():
        setattr(profile, key, value)
    await db.commit()
    
    # Invalidate cache
    cache_key = f"user:profile:{user_id}"
    await redis.delete(cache_key)
    
    return profile
```

**Inter-Service Communication:**
```python
# Validate JWT by calling Auth Service
async def validate_jwt(token: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/auth/verify",
            json={"token": token},
            timeout=5.0
        )
        
        if response.status_code != 200:
            raise HTTPException(401, "Invalid token")
        
        return response.json()
```

---

### 3. Task Service

**Port**: 8003  
**Database**: `task_db`  
**External Dependencies**: PostgreSQL, Auth Service (REST), Notification Service (REST)

**Core Responsibilities:**
- CRUD operations for tasks/study resources
- Support multiple resource types (notes, links, videos, files)
- Flexible metadata storage with JSONB
- Notify users via Notification Service (background task)

**Database Schema:**
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    task_type VARCHAR(50) DEFAULT 'note',  -- note, link, video, file
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',   -- active, completed, archived
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);
```

**JSONB Metadata Examples:**
```json
// For note
{
  "word_count": 450,
  "tags": ["backend", "microservices"],
  "priority": "high"
}

// For link
{
  "url": "https://example.com/article",
  "domain": "example.com",
  "read_time_minutes": 10
}

// For video
{
  "url": "https://youtube.com/watch?v=...",
  "duration_seconds": 1200,
  "platform": "youtube"
}
```

**Key APIs:**
- `POST /tasks` - Create task (protected)
- `GET /tasks` - List tasks with filters
- `GET /tasks/{task_id}` - Get task details
- `PUT /tasks/{task_id}` - Update task (owner only)
- `DELETE /tasks/{task_id}` - Delete task (owner only)

**Background Task Pattern:**
```python
from fastapi import BackgroundTasks
import httpx

async def notify_task_created(user_id: str, task_id: str, task_title: str):
    """Send notification in background - non-blocking"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/send",
                json={
                    "user_id": user_id,
                    "notification_type": "task_created",
                    "title": "Task Created",
                    "content": f"Your task '{task_title}' has been created successfully."
                },
                timeout=10.0
            )
    except Exception as e:
        # Log error but don't fail the main request
        logger.error(f"Failed to send notification: {e}")

@router.post("/tasks", status_code=201)
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    # Store task in database
    new_task = Task(
        user_id=current_user["user_id"],
        title=task.title,
        content=task.content,
        task_type=task.task_type,
        metadata=task.metadata
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Schedule background notification (non-blocking)
    background_tasks.add_task(
        notify_task_created,
        user_id=new_task.user_id,
        task_id=str(new_task.id),
        task_title=new_task.title
    )
    
    # Return immediately without waiting for notification
    return new_task
```

**Why BackgroundTasks Instead of Message Queue:**
- ✅ Simpler - no external message broker required
- ✅ Built into FastAPI - no additional dependencies
- ✅ Good enough for non-critical operations
- ✅ Easier to debug
- ⚠️ Limited reliability - if service crashes, task is lost
- ⚠️ No retry mechanism - we handle this with try/catch
- 💡 For production: Consider upgrading to Celery + Redis or RabbitMQ

---

### 4. Notification Service

**Port**: 8004  
**Database**: `notification_db`  
**External Dependencies**: PostgreSQL

**Core Responsibilities:**
- Receive notification requests via REST
- Send notifications (simulated email)
- Store notification history
- Provide notification history to users

**Database Schema:**
```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    notification_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_sent_at ON notifications(sent_at DESC);
```

**Key APIs:**
- `POST /notifications/send` - Send notification (internal use)
- `GET /notifications` - Get user notifications (protected)
- `PATCH /notifications/{id}/read` - Mark as read
- `PATCH /notifications/read-all` - Mark all as read

**Email Simulation:**
```python
async def send_notification(notification: NotificationCreate):
    """
    In development: Just log the notification
    In production: Send actual email via SMTP or service like SendGrid
    """
    # Store in database
    db_notification = Notification(**notification.dict())
    db.add(db_notification)
    await db.commit()
    
    # Simulate sending email
    if EMAIL_ENABLED:
        await send_actual_email(notification)
    else:
        logger.info(
            f"📧 SIMULATED EMAIL:\n"
            f"To: User {notification.user_id}\n"
            f"Subject: {notification.title}\n"
            f"Body: {notification.content}"
        )
    
    return db_notification
```

**Notification Types:**
- `welcome` - User registration
- `task_created` - New task created
- `task_completed` - Task marked complete
- `reminder` - Due date reminder

---

## Communication Patterns

### 1. Synchronous REST Calls

**Use Case**: When you need immediate response

**Example**: User Service validates JWT with Auth Service

```python
# In User Service
async def validate_jwt(token: str) -> dict:
    """
    Call Auth Service synchronously to validate JWT
    This blocks until Auth Service responds
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{AUTH_SERVICE_URL}/auth/verify",
                json={"token": token},
                timeout=5.0  # Fail fast
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                raise HTTPException(401, "Invalid token")
                
        except httpx.TimeoutException:
            raise HTTPException(503, "Auth service unavailable")
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise HTTPException(500, "Internal error")
```

**Pros:**
- ✅ Simple request/response pattern
- ✅ Immediate error handling
- ✅ Easy to debug

**Cons:**
- ⚠️ Service dependency - if Auth Service is down, other services fail
- ⚠️ Latency increases with chain length

---

### 2. Asynchronous Background Tasks

**Use Case**: When response can be delayed (notifications, logs, analytics)

**Example**: Task Service notifies Notification Service after task creation

```python
# In Task Service
from fastapi import BackgroundTasks

async def send_notification_background(user_id: str, task_data: dict):
    """
    This runs in background after response is sent to client
    """
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications/send",
                json={
                    "user_id": user_id,
                    "notification_type": "task_created",
                    "title": f"Task '{task_data['title']}' created",
                    "content": "Your task has been created successfully."
                },
                timeout=10.0
            )
    except Exception as e:
        # Log but don't fail - notification is not critical
        logger.error(f"Failed to send notification: {e}")

@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    # 1. Store task (critical operation)
    new_task = await task_repo.create(task, current_user["user_id"])
    
    # 2. Schedule background task (non-critical)
    background_tasks.add_task(
        send_notification_background,
        user_id=current_user["user_id"],
        task_data=new_task.dict()
    )
    
    # 3. Return immediately (client doesn't wait for notification)
    return {"success": True, "data": new_task}
```

**Pros:**
- ✅ Non-blocking - user gets fast response
- ✅ No external dependencies (no RabbitMQ/Kafka)
- ✅ Simple to implement and test

**Cons:**
- ⚠️ No persistence - if service crashes, task is lost
- ⚠️ No retry mechanism (we handle with try/catch)
- ⚠️ Limited to same process

**When to Use:**
- ✅ Notifications (non-critical)
- ✅ Logging/analytics
- ✅ Cache warming
- ❌ Payment processing (use sync or message queue)
- ❌ Critical business logic (use sync)

---

## Authentication Flow

### Complete JWT Flow Across Services

```
1. User Registration/Login
┌────────┐         ┌──────────────┐
│ Client │────────>│ Auth Service │
│        │ POST    │              │
│        │ /login  │ 1. Validate  │
│        │         │ 2. Hash pwd  │
│        │         │ 3. Gen JWT   │
│        │<────────│              │
│        │ 200 OK  │              │
│        │ {token} │              │
└────────┘         └──────────────┘

2. Accessing Protected Resources
┌────────┐         ┌──────────────┐         ┌──────────────┐
│ Client │────────>│ Task Service │────────>│ Auth Service │
│        │ GET     │              │ POST    │              │
│        │ /tasks  │ Authorization│ /verify │ Decode JWT   │
│        │ +JWT    │ header       │ {token} │ Validate     │
│        │         │              │<────────│              │
│        │         │              │ 200 OK  │              │
│        │         │ Extract      │ {user}  │              │
│        │         │ user_id      │         │              │
│        │<────────│              │         │              │
│        │ 200 OK  │              │         │              │
│        │ tasks[] │              │         │              │
└────────┘         └──────────────┘         └──────────────┘

3. Token Validation Logic
Each protected service:
1. Extracts JWT from Authorization header
2. Calls Auth Service /verify endpoint
3. Gets user_id from response
4. Proceeds with business logic
```

### JWT Structure

```json
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "sub": "user-uuid-here",
    "email": "user@example.com",
    "exp": 1699564800,
    "iat": 1699561200
  },
  "signature": "..."
}
```

### Implementation in Each Service

**Auth Service** (generates JWT):
```python
import jwt
from datetime import datetime, timedelta

def create_jwt(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES),
        "iat": datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token
```

**Other Services** (validate JWT):
```python
import httpx
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    # Call Auth Service to validate
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{AUTH_SERVICE_URL}/auth/verify",
            json={"token": token}
        )
        
        if response.status_code != 200:
            raise HTTPException(401, "Invalid or expired token")
        
        return response.json()["data"]

# Usage in routes
@router.get("/tasks")
async def get_tasks(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"]
    # ... fetch tasks for this user
```

---

## Database Design

### Database-per-Service Pattern

Each service has its own PostgreSQL database:
- `auth_db` - User credentials
- `user_db` - User profiles
- `task_db` - Tasks and resources
- `notification_db` - Notification history

**Why Separate Databases:**
- ✅ Services are independently deployable
- ✅ No shared database coupling
- ✅ Can scale databases independently
- ✅ Clear ownership boundaries

**Trade-offs:**
- ⚠️ No foreign key constraints across services
- ⚠️ Join queries impossible - use APIs instead
- ⚠️ Data consistency requires coordination

### Handling Cross-Service Data

**Problem**: User Service needs user email (stored in Auth Service)

**Solution 1**: Store duplicate data
```sql
-- In user_db
CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY,
    email VARCHAR,  -- Duplicated from auth_db
    bio TEXT
);
```

**Solution 2**: Call Auth Service via REST
```python
# In User Service
async def get_user_with_email(user_id: str):
    # Get profile from user_db
    profile = await db.query(UserProfile).filter_by(user_id=user_id).first()
    
    # Call Auth Service for email
    async with httpx.AsyncClient() as client:
        auth_response = await client.get(
            f"{AUTH_SERVICE_URL}/auth/users/{user_id}"
        )
        email = auth_response.json()["email"]
    
    return {**profile.dict(), "email": email}
```

**For this project**: We use Solution 2 (REST calls) to avoid data duplication.

---

## Caching Strategy

### What to Cache

1. **User Profiles** (User Service)
   - Cache key: `user:profile:{user_id}`
   - TTL: 300 seconds (5 minutes)
   - Invalidate on: Profile update

2. **JWT Blacklist** (Auth Service)
   - Cache key: `jwt:blacklist:{token_id}`
   - TTL: Matches JWT expiration
   - Invalidate on: Never (auto-expires)

### Cache Patterns

**Read-Through (Lazy Loading)**:
```python
async def get_with_cache(key: str, fetch_func):
    # Try cache
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    
    # Cache miss - fetch from DB
    data = await fetch_func()
    
    # Store in cache
    await redis.setex(key, TTL, json.dumps(data))
    
    return data
```

**Write-Through**:
```python
async def update_with_cache(key: str, data: dict, update_func):
    # Update database
    result = await update_func(data)
    
    # Invalidate cache
    await redis.delete(key)
    
    return result
```

---

## Testing Strategy

### Test Pyramid

```
        /\
       /  \      E2E Tests (5%)
      /    \     - Full user flows
     /______\    - All services running
    /        \   
   /          \  Integration Tests (15%)
  /            \ - API endpoint tests
 /______________\- Test database
/                \
|  Unit Tests    | Unit Tests (80%)
|    (80%)      | - Business logic
|________________|- Pure functions
```

### Test Examples

**Unit Test** (Auth Service):
```python
def test_password_hashing():
    password = "SecurePass123!"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) == True
    assert verify_password("wrong", hashed) == False
```

**Integration Test** (Auth Service):
```python
@pytest.mark.asyncio
async def test_register_endpoint(client, test_db):
    response = await client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!"
    })
    
    assert response.status_code == 201
    assert "access_token" in response.json()["data"]
    
    # Verify in database
    user = await test_db.query(User).filter_by(email="test@example.com").first()
    assert user is not None
```

**E2E Test** (All Services):
```python
async def test_complete_task_flow():
    # 1. Register user
    register_response = await client.post("/auth/register", json=...)
    token = register_response.json()["data"]["access_token"]
    
    # 2. Create task
    task_response = await client.post(
        "/tasks",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Task"}
    )
    assert task_response.status_code == 201
    
    # 3. Check notification was created
    notif_response = await client.get(
        "/notifications",
        headers={"Authorization": f"Bearer {token}"}
    )
    notifications = notif_response.json()["data"]["notifications"]
    assert any(n["type"] == "task_created" for n in notifications)
```

---

## Deployment with Docker Compose

### Local Development Setup

```bash
# Start all services
cd infra
docker-compose -f docker-compose-simplified.yml up --build

# Services start in order:
# 1. PostgreSQL (wait for healthy)
# 2. Redis (wait for healthy)
# 3. Auth Service (wait for healthy)
# 4. User, Task, Notification Services (wait for Auth)
# 5. Gateway
```

### Health Checks

Each service implements:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth_service",
        "timestamp": datetime.utcnow().isoformat()
    }
```

Docker Compose health check:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

---

## Future Enhancements (Optional)

These can be mentioned in interviews as "what I'd add next":

1. **Message Queue**: Replace BackgroundTasks with RabbitMQ/Kafka for reliability
2. **Kubernetes**: Add K8s manifests for production deployment
3. **Monitoring**: Add Prometheus metrics and Grafana dashboards
4. **gRPC**: Use gRPC for performance-critical inter-service calls
5. **API Versioning**: Implement `/v1/`, `/v2/` versioning
6. **Rate Limiting**: Add per-user rate limiting
7. **Distributed Tracing**: OpenTelemetry for request tracing across services

---

## Interview Discussion Points

### "Why 4 services instead of monolith?"

**Answer**:
- "Demonstrates microservices architecture understanding"
- "Each service has clear responsibility and can be developed independently"
- "In real-world: start with monolith, extract services as needed"
- "For this project: 4 is enough to show patterns without over-engineering"

### "Why REST only and not gRPC?"

**Answer**:
- "REST is simpler and more debuggable for portfolio project"
- "FastAPI has excellent REST support with automatic OpenAPI docs"
- "gRPC would add protocol buffers complexity for marginal benefit in this scale"
- "In production: I'd use gRPC for high-frequency service-to-service calls"

### "Why no message queue?"

**Answer**:
- "FastAPI BackgroundTasks are sufficient for non-critical operations like notifications"
- "Reduces infrastructure complexity - no need to manage RabbitMQ/Kafka"
- "For production: I'd add RabbitMQ for reliability and retry mechanisms"
- "Trade-off: Simplicity vs. guaranteed delivery"

### "How does this scale?"

**Answer**:
- "Services are stateless - can run multiple instances behind load balancer"
- "Database-per-service allows independent scaling"
- "Redis caching reduces database load"
- "For production: Add horizontal pod autoscaling in Kubernetes"

---

**This architecture balances practical implementation with demonstrating key microservices concepts - perfect for SDE interviews!** 🚀
