# Auth Service

Authentication and authorization microservice for StudyStream.

## Responsibilities

- User registration with secure password hashing (bcrypt)
- User authentication and JWT token generation
- Token validation for other services
- User logout and token revocation

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **Cache**: Redis (for token blacklist)
- **Auth**: JWT (PyJWT)
- **Password Hashing**: bcrypt (via passlib)

## Database Schema

### users table
```sql
- id (UUID, primary key)
- email (VARCHAR, unique, not null)
- password_hash (VARCHAR, not null)
- is_active (BOOLEAN, default true)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## API Endpoints

- `POST /register` - Register new user
- `POST /login` - Authenticate and get JWT
- `GET /me` - Get current user info (protected)
- `POST /verify` - Verify JWT token (internal)
- `POST /logout` - Logout and blacklist token

## Environment Variables

```bash
DATABASE_URL=postgresql://user:pass@postgres:5432/auth_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the service
uvicorn app.main:app --reload --port 8001
```

## Testing

```bash
pytest tests/ -v --cov=app
```

## Implementation Status

- [ ] Project structure
- [ ] Database models
- [ ] API routes
- [ ] JWT implementation
- [ ] Password hashing
- [ ] Event publishing (RabbitMQ)
- [ ] Unit tests
- [ ] Integration tests
- [ ] Dockerfile
