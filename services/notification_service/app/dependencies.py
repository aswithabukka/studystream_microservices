"""
Dependencies for JWT validation
"""
from fastapi import Header, HTTPException
import httpx
from app.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)


async def get_current_user(authorization: str = Header(None)):
    """
    Validate JWT token by calling Auth Service
    
    Returns:
        dict: User information from token
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    
    # Call Auth Service to validate token
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{settings.auth_service_url}/auth/verify",
                json={"token": token},
                timeout=5.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid token"
                )
            
            data = response.json()
            
            if not data.get("valid"):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
            
            return {
                "user_id": data["user_id"],
                "email": data["email"]
            }
            
        except httpx.TimeoutException:
            logger.error("Auth service timeout")
            raise HTTPException(
                status_code=503,
                detail="Auth service unavailable"
            )
        except httpx.RequestError as e:
            logger.error(f"Auth service request error: {e}")
            raise HTTPException(
                status_code=503,
                detail="Auth service unavailable"
            )
        except Exception as e:
            logger.error(f"Error validating token: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error"
            )
