from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from .config import get_settings
from typing import Optional, Dict
import time

settings = get_settings()

class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True, required_scopes: Optional[list] = None):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.required_scopes = required_scopes or []

    async def __call__(self, request: Request) -> Dict:
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization code."
            )
            
        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme."
            )
            
        payload = self.verify_jwt(credentials.credentials)
        if not payload:
            raise HTTPException(
                status_code=401,
                detail="Invalid token or expired token."
            )
            
        # Verify scopes if required
        if self.required_scopes:
            token_scopes = payload.get("scopes", [])
            for scope in self.required_scopes:
                if scope not in token_scopes:
                    raise HTTPException(
                        status_code=403,
                        detail="Not enough permissions"
                    )
                    
        return payload

    def verify_jwt(self, jwt_token: str) -> Dict:
        try:
            payload = jwt.decode(
                jwt_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

async def log_request_middleware(request: Request, call_next):
    """Simple request logger"""
    start_time = time.time()
    response = await call_next(request)
    
    # Print basic request info
    print(
        f"Path: {request.url.path}, "
        f"Method: {request.method}, "
        f"Status: {response.status_code}, "
        f"Duration: {time.time() - start_time:.3f}s"
    )
    
    return response

async def validate_request_middleware(request: Request, call_next):
    """Simple request validator"""
    
    # Only check content type for POST/PUT requests
    if request.method in ["POST", "PUT"]:
        content_type = request.headers.get("content-type", "")
        if not content_type.startswith("application/json"):
            raise HTTPException(400, "Content-Type must be application/json")

    response = await call_next(request)
    return response
