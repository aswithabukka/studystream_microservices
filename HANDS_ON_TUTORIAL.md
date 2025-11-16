# 🎓 Hands-On Tutorial - Learn By Doing!

## Step-by-Step Guide to Understanding Your System

This tutorial will walk you through **testing every feature** and **understanding what happens behind the scenes**.

---

## 🎯 Tutorial Overview

You'll learn by doing these tasks:
1. ✅ Register a user and understand JWT
2. ✅ Create tasks and see database changes
3. ✅ Trigger notifications automatically
4. ✅ Explore caching with Redis
5. ✅ Understand service communication

**Time needed**: 30-45 minutes

---

## 📋 Prerequisites

Make sure your services are running:
```bash
cd /Users/aswithabukka/CascadeProjects/studystream-microservices
./test_system.sh
```

You should see: ✅ ALL TESTS PASSED!

---

## Part 1: Understanding Authentication (15 minutes)

### Step 1.1: Register Your First User

Open your terminal and run:

```bash
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "AlicePass123!",
    "password_confirm": "AlicePass123!"
  }' | python3 -m json.tool
```

**What you'll see**:
```json
{
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 1763295000,
    "user_id": "f28dd07b-...",
    "email": "alice@example.com"
}
```

**What just happened?**

1. **Your request** sent email and password
2. **Auth Service** received it
3. **Password was hashed** using bcrypt (one-way encryption)
4. **User saved** to `auth_db` database
5. **JWT token created** containing user_id and email
6. **Token returned** to you

**🔍 Deep Dive**: Let's decode your JWT token!

Copy your `access_token` and visit: https://jwt.io

Paste your token in the "Encoded" section. You'll see:

```json
// HEADER
{
  "alg": "HS256",  // Algorithm used
  "typ": "JWT"     // Token type
}

// PAYLOAD (your data!)
{
  "sub": "f28dd07b-...",        // User ID
  "email": "alice@example.com",  // Email
  "exp": 1763295000,             // Expiration time
  "iat": 1763291400              // Issued at time
}

// SIGNATURE (proof it's real)
// Created using your SECRET_KEY
```

**💡 Key Learning**: The token contains your identity. Services can read it without asking Auth Service every time!

---

### Step 1.2: Save Your Token

```bash
# Save for easy reuse
export TOKEN="your-access-token-here"

# Or create a file
echo "your-access-token-here" > my_token.txt
```

---

### Step 1.3: Verify Your Token

```bash
curl -X POST http://localhost:8001/auth/verify-token \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}" | python3 -m json.tool
```

**What you'll see**:
```json
{
    "valid": true,
    "user_id": "f28dd07b-...",
    "email": "alice@example.com"
}
```

**What happened?**
1. Auth Service decoded your JWT
2. Checked the signature (using SECRET_KEY)
3. Verified it hasn't expired
4. Returned user information

---

### Step 1.4: Get Your User Info

```bash
curl http://localhost:8001/auth/me \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**What you'll see**:
```json
{
    "id": "f28dd07b-...",
    "email": "alice@example.com",
    "is_active": true
}
```

**💡 Key Learning**: Notice the `Authorization: Bearer $TOKEN` header? That's how you prove who you are!

---

### Step 1.5: Try Without Token (See It Fail!)

```bash
curl http://localhost:8001/auth/me
```

**What you'll see**:
```json
{
    "detail": "Not authenticated"
}
```

**Why?** No token = No proof of identity = Access denied!

---

## Part 2: Creating Tasks (15 minutes)

### Step 2.1: Create Your First Task

```bash
curl -X POST http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Learn Microservices",
    "content": "Study authentication, databases, and APIs",
    "task_type": "note",
    "task_metadata": {
      "priority": "high",
      "tags": ["learning", "backend"],
      "estimated_hours": 10
    }
  }' | python3 -m json.tool
```

**What you'll see**:
```json
{
    "id": "7af4805d-...",
    "user_id": "f28dd07b-...",
    "title": "Learn Microservices",
    "content": "Study authentication, databases, and APIs",
    "task_type": "note",
    "task_metadata": {
        "priority": "high",
        "tags": ["learning", "backend"],
        "estimated_hours": 10
    },
    "status": "active",
    "created_at": "2025-11-16T05:38:31.230435",
    "updated_at": "2025-11-16T05:38:31.230441"
}
```

**What just happened? (Behind the scenes)**

```
1. Task Service received your request
   ↓
2. Extracted JWT from "Authorization: Bearer ..." header
   ↓
3. Called Auth Service to verify token
   ↓
4. Auth Service said "Valid! user_id = f28dd07b"
   ↓
5. Task Service created task in task_db
   ↓
6. Task Service added notification to background queue
   ↓
7. Returned task to you immediately (fast!)
   ↓
8. Background worker called Notification Service
   ↓
9. Notification saved to notification_db
   ✅ Done!
```

**💡 Key Learning**: You got response immediately, but notification happened in background!

---

### Step 2.2: Check Your Notifications

Wait 2 seconds, then:

```bash
curl http://localhost:8004/notifications \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**What you'll see**:
```json
[
    {
        "id": "c25da9d7-...",
        "user_id": "f28dd07b-...",
        "notification_type": "task_created",
        "title": "Task Created",
        "content": "Your task 'Learn Microservices' has been created successfully.",
        "is_read": false,
        "sent_at": "2025-11-16T05:38:31.258327"
    }
]
```

**🎉 Magic!** The notification was created automatically when you created the task!

---

### Step 2.3: Create More Tasks

```bash
# Task 2
curl -X POST http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Build Portfolio Website",
    "content": "Create personal website showcasing projects",
    "task_type": "note",
    "task_metadata": {
      "priority": "medium",
      "tags": ["frontend", "portfolio"]
    }
  }' | python3 -m json.tool

# Task 3
curl -X POST http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Study System Design",
    "content": "Learn about scalability, databases, caching",
    "task_type": "note",
    "task_metadata": {
      "priority": "high",
      "tags": ["learning", "interviews"]
    }
  }' | python3 -m json.tool
```

---

### Step 2.4: List All Your Tasks

```bash
curl http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**What you'll see**: Array with all 3 tasks!

**💡 Key Learning**: The API only returns YOUR tasks (filtered by user_id from token)

---

### Step 2.5: Get a Specific Task

```bash
# Copy a task ID from the list above
TASK_ID="7af4805d-03db-4370-b055-ef915b8d842c"

curl http://localhost:8003/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### Step 2.6: Update a Task

```bash
curl -X PUT http://localhost:8003/tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "task_metadata": {
      "priority": "high",
      "tags": ["learning", "backend", "completed"],
      "completion_date": "2025-11-16"
    }
  }' | python3 -m json.tool
```

**What happened?** Task marked as completed!

---

## Part 3: Exploring User Profiles (10 minutes)

### Step 3.1: Create Your Profile

```bash
curl -X POST http://localhost:8002/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Alice Johnson",
    "bio": "Software Engineer learning microservices",
    "avatar_url": "https://i.pravatar.cc/150?u=alice",
    "preferences": {
      "theme": "dark",
      "notifications_enabled": true,
      "language": "en"
    }
  }' | python3 -m json.tool
```

---

### Step 3.2: Get Your Profile (First Time - Slow)

```bash
# Extract user_id from token or use the one from registration
USER_ID="f28dd07b-0ce4-4be6-98b7-9d29192d05b1"

time curl http://localhost:8002/profile/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Notice the time!** This queries PostgreSQL.

---

### Step 3.3: Get Profile Again (Second Time - Fast!)

```bash
time curl http://localhost:8002/profile/$USER_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**Much faster!** This time it came from Redis cache!

**What happened?**
```
First Request:
1. Check Redis → Not found
2. Query PostgreSQL → Found
3. Store in Redis (5-min expiry)
4. Return data

Second Request:
1. Check Redis → Found! ✅
2. Return immediately (10x faster!)
```

---

### Step 3.4: Update Profile (Invalidates Cache)

```bash
curl -X PUT http://localhost:8002/profile/$USER_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Senior Software Engineer | Microservices Expert",
    "preferences": {
      "theme": "dark",
      "notifications_enabled": true
    }
  }' | python3 -m json.tool
```

**What happened?**
1. Profile updated in PostgreSQL
2. Cache deleted from Redis
3. Next request will be slow again (needs to re-cache)

---

## Part 4: Understanding Notifications (10 minutes)

### Step 4.1: List All Notifications

```bash
curl http://localhost:8004/notifications \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**You should see 3 notifications** (one for each task you created)!

---

### Step 4.2: Check Unread Count

```bash
curl http://localhost:8004/notifications/unread-count \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**What you'll see**:
```json
{
    "unread_count": 3
}
```

---

### Step 4.3: Mark a Notification as Read

```bash
# Copy a notification ID from Step 4.1
NOTIF_ID="c25da9d7-367b-4f0b-b129-e2caeb09c28a"

curl -X PATCH http://localhost:8004/notifications/$NOTIF_ID/read \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

---

### Step 4.4: Check Unread Count Again

```bash
curl http://localhost:8004/notifications/unread-count \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

**What you'll see**:
```json
{
    "unread_count": 2
}
```

**It decreased!** ✅

---

## Part 5: Exploring the Database (5 minutes)

### Step 5.1: Connect to PostgreSQL

```bash
docker exec -it studystream-postgres psql -U postgres
```

---

### Step 5.2: List All Databases

```sql
\l
```

**You should see**:
- auth_db
- user_db
- task_db
- notification_db

---

### Step 5.3: Explore Auth Database

```sql
-- Connect to auth_db
\c auth_db

-- List tables
\dt

-- View your user
SELECT id, email, is_active, created_at FROM users;

-- Exit
\q
```

---

### Step 5.4: Explore Task Database

```bash
docker exec -it studystream-postgres psql -U postgres -d task_db
```

```sql
-- List all tasks
SELECT id, title, status, task_type FROM tasks;

-- View task metadata (JSONB!)
SELECT title, task_metadata FROM tasks;

-- Exit
\q
```

**💡 Key Learning**: `task_metadata` is JSONB - can store any JSON structure!

---

## Part 6: Interactive API Documentation (5 minutes)

### Step 6.1: Open Swagger UI

Open your browser:
- **Auth Service**: http://localhost:8001/docs
- **Task Service**: http://localhost:8003/docs

---

### Step 6.2: Authorize in Swagger

1. Click the **"Authorize"** button (top right)
2. Enter: `Bearer your-token-here`
3. Click "Authorize"
4. Click "Close"

Now all requests will include your token!

---

### Step 6.3: Try Endpoints

1. Expand any endpoint (e.g., `GET /tasks`)
2. Click "Try it out"
3. Click "Execute"
4. See the response!

**💡 This is the easiest way to test your APIs!**

---

## 🎓 What You Learned

### ✅ Concepts Mastered
- **JWT Authentication**: How tokens work and why they're secure
- **REST APIs**: GET, POST, PUT, PATCH, DELETE methods
- **Microservices**: How services communicate via HTTP
- **Databases**: Database-per-service pattern
- **Caching**: Redis makes things 10x faster
- **Async Processing**: Background tasks don't block users
- **Authorization**: Owner-only access control

### ✅ Technologies Used
- FastAPI for web services
- PostgreSQL for data storage
- Redis for caching
- JWT for authentication
- Bcrypt for password security
- SQLAlchemy as ORM
- Pydantic for validation

### ✅ Architectural Patterns
- Microservices architecture
- Database-per-service
- Cache-aside pattern
- Background task processing
- RESTful API design
- Token-based authentication

---

## 🚀 Next Steps

### Challenge 1: Add a New Feature
Try adding a task priority filter:
```bash
# Should only return high-priority tasks
curl "http://localhost:8003/tasks?priority=high" \
  -H "Authorization: Bearer $TOKEN"
```

**Hint**: Modify `services/task_service/app/routes.py`

---

### Challenge 2: Create a Second User
Register another user and try to access the first user's tasks. What happens?

```bash
# Register Bob
curl -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "password": "BobPass123!",
    "password_confirm": "BobPass123!"
  }'

# Try to access Alice's tasks with Bob's token
# It won't work! Each user only sees their own data ✅
```

---

### Challenge 3: Test Error Cases
```bash
# Expired token
curl http://localhost:8003/tasks \
  -H "Authorization: Bearer expired-token"

# Missing token
curl http://localhost:8003/tasks

# Invalid JSON
curl -X POST http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d 'invalid json'
```

---

## 📝 Summary

**You just learned**:
1. ✅ How to authenticate with JWT tokens
2. ✅ How to create, read, update data via REST APIs
3. ✅ How microservices communicate
4. ✅ How caching improves performance
5. ✅ How background tasks work
6. ✅ How to explore databases
7. ✅ How to use interactive API docs

**You're now ready to**:
- Explain your project in interviews
- Add new features
- Debug issues
- Deploy to production

---

## 🎉 Congratulations!

You've completed the hands-on tutorial! You now understand your microservices system from end to end.

**Keep practicing**:
- Try the challenges above
- Read through the code
- Modify existing features
- Add new endpoints

**Questions?** Re-run any section of this tutorial anytime!

---

**Related Guides**:
- Full theory: `LEARNING_GUIDE.md`
- Quick reference: `QUICK_REFERENCE.md`
- Test script: `./test_system.sh`
