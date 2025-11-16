"""
Integration tests for Auth Service API routes
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, test_user_data):
    """Test user registration"""
    response = await client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == 201
    data = response.json()
    
    assert "access_token" in data
    assert "user_id" in data
    assert data["email"] == test_user_data["email"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user_data):
    """Test registering with duplicate email"""
    # Register first user
    await client.post("/auth/register", json=test_user_data)
    
    # Try to register again with same email
    response = await client.post("/auth/register", json=test_user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_password_mismatch(client: AsyncClient):
    """Test registration with mismatched passwords"""
    data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "password_confirm": "DifferentPassword123!"
    }
    
    response = await client.post("/auth/register", json=data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    """Test registration with weak password"""
    data = {
        "email": "test@example.com",
        "password": "weak",
        "password_confirm": "weak"
    }
    
    response = await client.post("/auth/register", json=data)
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user_data):
    """Test successful login"""
    # Register user first
    await client.post("/auth/register", json=test_user_data)
    
    # Login
    login_data = {
        "email": test_user_data["email"],
        "password": test_user_data["password"]
    }
    response = await client.post("/auth/login", json=login_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "user_id" in data
    assert data["email"] == test_user_data["email"]


@pytest.mark.asyncio
async def test_login_invalid_email(client: AsyncClient):
    """Test login with invalid email"""
    login_data = {
        "email": "nonexistent@example.com",
        "password": "SomePassword123!"
    }
    response = await client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, test_user_data):
    """Test login with invalid password"""
    # Register user first
    await client.post("/auth/register", json=test_user_data)
    
    # Login with wrong password
    login_data = {
        "email": test_user_data["email"],
        "password": "WrongPassword123!"
    }
    response = await client.post("/auth/login", json=login_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user_data):
    """Test getting current user info"""
    # Register user
    register_response = await client.post("/auth/register", json=test_user_data)
    token = register_response.json()["access_token"]
    
    # Get current user
    response = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["email"] == test_user_data["email"]
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_current_user_no_token(client: AsyncClient):
    """Test getting current user without token"""
    response = await client.get("/auth/me")
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_verify_token(client: AsyncClient, test_user_data):
    """Test token verification"""
    # Register user
    register_response = await client.post("/auth/register", json=test_user_data)
    token = register_response.json()["access_token"]
    
    # Verify token
    response = await client.post(
        "/auth/verify",
        json={"token": token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is True
    assert data["email"] == test_user_data["email"]


@pytest.mark.asyncio
async def test_verify_invalid_token(client: AsyncClient):
    """Test verifying invalid token"""
    response = await client.post(
        "/auth/verify",
        json={"token": "invalid.token.here"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["valid"] is False


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, test_user_data):
    """Test logout"""
    # Register user
    register_response = await client.post("/auth/register", json=test_user_data)
    token = register_response.json()["access_token"]
    
    # Logout
    response = await client.post(
        "/auth/logout",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert response.json()["success"] is True


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "healthy"
    assert "service" in data
