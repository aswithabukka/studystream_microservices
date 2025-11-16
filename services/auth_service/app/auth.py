"""
Authentication utilities: JWT, password hashing
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.config import get_settings
import redis.asyncio as redis

settings = get_settings()

# Redis client for token blacklist
redis_client: Optional[redis.Redis] = None


async def get_redis():
    """Get Redis client"""
    global redis_client
    if redis_client is None:
        redis_client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    # Convert password to bytes and hash
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    # Convert both to bytes for comparison
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def create_access_token(user_id: str, email: str) -> tuple[str, int]:
    """
    Create a JWT access token
    
    Returns:
        tuple: (token, expiration_timestamp)
    """
    expires_delta = timedelta(minutes=settings.jwt_expiration_minutes)
    expire = datetime.utcnow() + expires_delta
    
    to_encode = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    
    return encoded_jwt, int(expire.timestamp())


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token
    
    Returns:
        dict: Token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


async def blacklist_token(token: str, exp: int):
    """
    Add token to blacklist (for logout)
    
    Args:
        token: JWT token
        exp: Token expiration timestamp
    """
    redis_conn = await get_redis()
    ttl = exp - int(datetime.utcnow().timestamp())
    
    if ttl > 0:
        await redis_conn.setex(
            f"blacklist:{token}",
            ttl,
            "1"
        )


async def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    redis_conn = await get_redis()
    result = await redis_conn.get(f"blacklist:{token}")
    return result is not None
