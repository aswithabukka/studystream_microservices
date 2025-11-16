# StudyStream API Specifications

Complete API documentation for all microservices.

## Table of Contents
- [Auth Service API](#auth-service-api)
- [User Service API](#user-service-api)
- [Task Service API](#task-service-api)
- [Notification Service API](#notification-service-api)
- [LLM Service API](#llm-service-api)
- [Common Responses](#common-responses)

## Common Headers

### Authentication
Protected endpoints require JWT token in header:
```http
Authorization: Bearer <jwt_token>
```

### Content Type
```http
Content-Type: application/json
```

## Common Responses

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { ... }
  }
}
```

### HTTP Status Codes
- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Auth Service API

**Base URL**: `http://localhost:8001` or `/auth` (via gateway)

### 1. Register User

**Endpoint**: `POST /register`

**Description**: Create a new user account

**Authentication**: None

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": "User registered successfully"
}
```

**Validation Rules**:
- Email: Valid email format, unique
- Password: Min 8 characters, at least 1 uppercase, 1 lowercase, 1 digit
- Password confirmation must match

---

### 2. Login

**Endpoint**: `POST /login`

**Description**: Authenticate user and get JWT token

**Authentication**: None

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 3600
  },
  "message": "Login successful"
}
```

**Error** (401 Unauthorized):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

---

### 3. Get Current User

**Endpoint**: `GET /me`

**Description**: Get authenticated user information

**Authentication**: Required (JWT)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2024-11-15T03:45:23Z"
  }
}
```

---

### 4. Verify Token (Internal)

**Endpoint**: `POST /verify`

**Description**: Verify JWT token validity (used by other services)

**Authentication**: None (but requires token in request)

**Request Body**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "valid": true,
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "exp": 1699564800
  }
}
```

---

### 5. Logout

**Endpoint**: `POST /logout`

**Description**: Invalidate JWT token (add to blacklist)

**Authentication**: Required (JWT)

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

---

## User Service API

**Base URL**: `http://localhost:8002` or `/users` (via gateway)

### 1. Get User Profile

**Endpoint**: `GET /users/{user_id}`

**Description**: Get user profile by ID

**Authentication**: Required (JWT)

**Path Parameters**:
- `user_id` (string, UUID): User ID

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "bio": "Full-stack developer and lifelong learner",
    "avatar_url": "https://example.com/avatars/user123.jpg",
    "preferences": {
      "theme": "dark",
      "notifications_enabled": true,
      "study_reminder_time": "09:00"
    },
    "created_at": "2024-11-15T03:45:23Z",
    "updated_at": "2024-11-15T10:30:00Z"
  }
}
```

---

### 2. Update User Profile

**Endpoint**: `PATCH /users/{user_id}`

**Description**: Update user profile (owner only)

**Authentication**: Required (JWT)

**Path Parameters**:
- `user_id` (string, UUID): User ID (must match JWT user_id)

**Request Body** (partial update):
```json
{
  "bio": "Updated bio text",
  "avatar_url": "https://example.com/avatars/newavatar.jpg",
  "preferences": {
    "theme": "light",
    "notifications_enabled": false
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "bio": "Updated bio text",
    "avatar_url": "https://example.com/avatars/newavatar.jpg",
    "preferences": {
      "theme": "light",
      "notifications_enabled": false,
      "study_reminder_time": "09:00"
    },
    "updated_at": "2024-11-15T11:00:00Z"
  },
  "message": "Profile updated successfully"
}
```

---

### 3. Get User Settings

**Endpoint**: `GET /users/{user_id}/settings`

**Description**: Get user settings

**Authentication**: Required (JWT)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "notifications_enabled": true,
    "email_notifications": false,
    "study_reminder_time": "09:00",
    "timezone": "America/New_York",
    "language": "en"
  }
}
```

---

## Task Service API

**Base URL**: `http://localhost:8003` or `/tasks` (via gateway)

### 1. Create Task

**Endpoint**: `POST /tasks`

**Description**: Create a new task/resource

**Authentication**: Required (JWT)

**Request Body**:
```json
{
  "title": "Read Chapter 5: Microservices",
  "content": "Focus on service discovery and API gateways",
  "task_type": "note",
  "metadata": {
    "priority": "high",
    "tags": ["architecture", "backend"]
  }
}
```

**Task Types**: `note`, `link`, `video`, `file`, `other`

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "task_id": "660e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Read Chapter 5: Microservices",
    "content": "Focus on service discovery and API gateways",
    "task_type": "note",
    "metadata": {
      "priority": "high",
      "tags": ["architecture", "backend"]
    },
    "status": "active",
    "created_at": "2024-11-15T12:00:00Z",
    "updated_at": "2024-11-15T12:00:00Z"
  },
  "message": "Task created successfully"
}
```

---

### 2. List Tasks

**Endpoint**: `GET /tasks`

**Description**: Get list of tasks for authenticated user

**Authentication**: Required (JWT)

**Query Parameters**:
- `status` (string, optional): Filter by status (`active`, `completed`, `archived`)
- `task_type` (string, optional): Filter by type
- `limit` (integer, optional): Number of results (default: 50, max: 100)
- `offset` (integer, optional): Pagination offset (default: 0)
- `sort_by` (string, optional): Sort field (`created_at`, `updated_at`, `title`)
- `order` (string, optional): Sort order (`asc`, `desc`)

**Example**: `GET /tasks?status=active&limit=20&sort_by=created_at&order=desc`

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "tasks": [
      {
        "task_id": "660e8400-e29b-41d4-a716-446655440001",
        "title": "Read Chapter 5: Microservices",
        "task_type": "note",
        "status": "active",
        "created_at": "2024-11-15T12:00:00Z"
      },
      {
        "task_id": "660e8400-e29b-41d4-a716-446655440002",
        "title": "Watch Docker tutorial",
        "task_type": "video",
        "status": "active",
        "created_at": "2024-11-14T10:30:00Z"
      }
    ],
    "pagination": {
      "total": 45,
      "limit": 20,
      "offset": 0,
      "has_more": true
    }
  }
}
```

---

### 3. Get Task Details

**Endpoint**: `GET /tasks/{task_id}`

**Description**: Get detailed information about a task

**Authentication**: Required (JWT)

**Path Parameters**:
- `task_id` (string, UUID): Task ID

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "task_id": "660e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Read Chapter 5: Microservices",
    "content": "Focus on service discovery and API gateways. Important concepts: ...",
    "task_type": "note",
    "metadata": {
      "priority": "high",
      "tags": ["architecture", "backend"],
      "word_count": 250
    },
    "status": "active",
    "created_at": "2024-11-15T12:00:00Z",
    "updated_at": "2024-11-15T12:00:00Z"
  }
}
```

---

### 4. Update Task

**Endpoint**: `PUT /tasks/{task_id}`

**Description**: Update task (owner only)

**Authentication**: Required (JWT)

**Path Parameters**:
- `task_id` (string, UUID): Task ID

**Request Body**:
```json
{
  "title": "Read Chapter 5: Microservices (Updated)",
  "content": "Updated content...",
  "status": "completed",
  "metadata": {
    "priority": "medium",
    "tags": ["architecture", "backend", "completed"]
  }
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "task_id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Read Chapter 5: Microservices (Updated)",
    "status": "completed",
    "updated_at": "2024-11-15T14:30:00Z"
  },
  "message": "Task updated successfully"
}
```

---

### 5. Delete Task

**Endpoint**: `DELETE /tasks/{task_id}`

**Description**: Delete task (owner only)

**Authentication**: Required (JWT)

**Path Parameters**:
- `task_id` (string, UUID): Task ID

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Task deleted successfully"
}
```

---

## Notification Service API

**Base URL**: `http://localhost:8004` or `/notifications` (via gateway)

### 1. Get Notifications

**Endpoint**: `GET /notifications`

**Description**: Get notifications for authenticated user

**Authentication**: Required (JWT)

**Query Parameters**:
- `is_read` (boolean, optional): Filter by read status
- `notification_type` (string, optional): Filter by type
- `limit` (integer, optional): Number of results (default: 50)
- `offset` (integer, optional): Pagination offset

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "notifications": [
      {
        "notification_id": "770e8400-e29b-41d4-a716-446655440003",
        "notification_type": "welcome",
        "title": "Welcome to StudyStream!",
        "content": "Thank you for joining. Get started by creating your first task.",
        "is_read": false,
        "sent_at": "2024-11-15T03:45:30Z"
      },
      {
        "notification_id": "770e8400-e29b-41d4-a716-446655440004",
        "notification_type": "task_created",
        "title": "Task Created",
        "content": "Your task 'Read Chapter 5' has been created successfully.",
        "is_read": true,
        "sent_at": "2024-11-15T12:00:05Z"
      }
    ],
    "unread_count": 3,
    "pagination": {
      "total": 15,
      "limit": 50,
      "offset": 0
    }
  }
}
```

---

### 2. Mark Notification as Read

**Endpoint**: `PATCH /notifications/{notification_id}/read`

**Description**: Mark notification as read

**Authentication**: Required (JWT)

**Path Parameters**:
- `notification_id` (string, UUID): Notification ID

**Response** (200 OK):
```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

---

### 3. Mark All as Read

**Endpoint**: `PATCH /notifications/read-all`

**Description**: Mark all user notifications as read

**Authentication**: Required (JWT)

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "marked_count": 5
  },
  "message": "All notifications marked as read"
}
```

---

### 4. Send Notification (Manual/Admin)

**Endpoint**: `POST /notifications/send`

**Description**: Manually send a notification

**Authentication**: Required (JWT, admin only)

**Request Body**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "notification_type": "reminder",
  "title": "Study Reminder",
  "content": "Don't forget to complete your tasks for today!"
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "notification_id": "770e8400-e29b-41d4-a716-446655440010",
    "sent_at": "2024-11-15T15:00:00Z"
  },
  "message": "Notification sent successfully"
}
```

---

## LLM Service API

**Base URL**: `http://localhost:8005` or `/llm` (via gateway)

### 1. Summarize Tasks

**Endpoint**: `POST /llm/summarize`

**Description**: Generate AI summary of user's tasks

**Authentication**: Required (JWT)

**Request Body**:
```json
{
  "task_ids": [
    "660e8400-e29b-41d4-a716-446655440001",
    "660e8400-e29b-41d4-a716-446655440002"
  ],
  "max_length": 500
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "summary_id": "880e8400-e29b-41d4-a716-446655440005",
    "summary": "Your current focus is on microservices architecture and containerization. Key areas include: service discovery, API gateways, and Docker fundamentals. Recommended next steps: hands-on practice with Kubernetes and study service mesh patterns.",
    "task_count": 2,
    "model_used": "gpt-3.5-turbo",
    "generated_at": "2024-11-15T16:00:00Z"
  }
}
```

---

### 2. Generate Study Plan

**Endpoint**: `POST /llm/study-plan`

**Description**: Generate AI-powered study plan

**Authentication**: Required (JWT)

**Request Body**:
```json
{
  "goal": "Learn microservices architecture",
  "duration_days": 30,
  "current_level": "intermediate"
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "plan_id": "880e8400-e29b-41d4-a716-446655440006",
    "study_plan": {
      "week_1": {
        "topic": "Microservices Fundamentals",
        "tasks": [
          "Read Martin Fowler's microservices article",
          "Watch intro to microservices video",
          "Practice: Build a simple REST API"
        ]
      },
      "week_2": {
        "topic": "Service Communication",
        "tasks": [
          "Study REST vs gRPC",
          "Learn about message queues",
          "Practice: Implement inter-service communication"
        ]
      }
    },
    "generated_at": "2024-11-15T16:30:00Z"
  }
}
```

---

### 3. Get Summary History

**Endpoint**: `GET /llm/history`

**Description**: Get user's LLM generation history

**Authentication**: Required (JWT)

**Query Parameters**:
- `limit` (integer, optional): Number of results (default: 20)
- `offset` (integer, optional): Pagination offset

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "history": [
      {
        "summary_id": "880e8400-e29b-41d4-a716-446655440005",
        "type": "summarize",
        "task_count": 2,
        "created_at": "2024-11-15T16:00:00Z"
      },
      {
        "summary_id": "880e8400-e29b-41d4-a716-446655440006",
        "type": "study_plan",
        "created_at": "2024-11-15T16:30:00Z"
      }
    ],
    "pagination": {
      "total": 8,
      "limit": 20,
      "offset": 0
    }
  }
}
```

---

## Health & Status Endpoints

All services implement these endpoints:

### Health Check
**Endpoint**: `GET /health`
**Response**:
```json
{
  "status": "healthy",
  "service": "auth_service",
  "version": "1.0.0",
  "timestamp": "2024-11-15T17:00:00Z"
}
```

### Readiness Probe
**Endpoint**: `GET /health/ready`
**Response**:
```json
{
  "status": "ready",
  "database": "connected",
  "cache": "connected"
}
```

### Liveness Probe
**Endpoint**: `GET /health/live`
**Response**:
```json
{
  "status": "alive"
}
```

---

## API Versioning

Currently at version 1.0. Future versions may use URL versioning:
- `/v1/auth/...`
- `/v2/auth/...`

Or header versioning:
```http
Accept: application/vnd.studystream.v1+json
```

---

## Rate Limiting

Default rate limits (via NGINX):
- Standard endpoints: 10 requests/second per IP
- LLM endpoints: 5 requests/second per IP
- Burst: 20 requests

**Rate Limit Headers** (returned in response):
```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 7
X-RateLimit-Reset: 1699564800
```

---

## Pagination

List endpoints support pagination:

**Query Parameters**:
- `limit`: Items per page (default: 50, max: 100)
- `offset`: Number of items to skip

**Response**:
```json
{
  "data": [...],
  "pagination": {
    "total": 245,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `INVALID_CREDENTIALS` | Wrong email or password |
| `TOKEN_EXPIRED` | JWT token has expired |
| `TOKEN_INVALID` | JWT token is malformed or invalid |
| `UNAUTHORIZED` | Authentication required |
| `FORBIDDEN` | Insufficient permissions |
| `NOT_FOUND` | Resource not found |
| `VALIDATION_ERROR` | Input validation failed |
| `DUPLICATE_EMAIL` | Email already registered |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INTERNAL_ERROR` | Server error |

---

For interactive API documentation, visit:
- Auth Service: http://localhost:8001/docs
- User Service: http://localhost:8002/docs
- Task Service: http://localhost:8003/docs
- Notification Service: http://localhost:8004/docs
- LLM Service: http://localhost:8005/docs
