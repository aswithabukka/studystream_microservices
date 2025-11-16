"""
Unit tests for authentication logic
"""
import pytest
from app.auth import hash_password, verify_password, create_access_token, decode_access_token


def test_password_hashing():
    """Test password hashing and verification"""
    password = "TestPassword123!"
    hashed = hash_password(password)
    
    # Hash should be different from password
    assert hashed != password
    
    # Verification should work
    assert verify_password(password, hashed) is True
    
    # Wrong password should not verify
    assert verify_password("WrongPassword", hashed) is False


def test_create_access_token():
    """Test JWT token creation"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "test@example.com"
    
    token, exp = create_access_token(user_id, email)
    
    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Expiration should be an integer timestamp
    assert isinstance(exp, int)
    assert exp > 0


def test_decode_access_token():
    """Test JWT token decoding"""
    user_id = "123e4567-e89b-12d3-a456-426614174000"
    email = "test@example.com"
    
    token, exp = create_access_token(user_id, email)
    payload = decode_access_token(token)
    
    # Payload should contain user info
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["email"] == email
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_token():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    payload = decode_access_token(invalid_token)
    
    # Should return None for invalid token
    assert payload is None
