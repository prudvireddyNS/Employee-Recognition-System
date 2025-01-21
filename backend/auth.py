from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
import jwt
from fastapi import HTTPException, status, Depends, Security
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from sqlalchemy.orm import Session
from .database import SessionLocal, AdminUser, Base, engine
from .config import get_settings
import os
from pydantic import BaseModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/admin/login",
    scopes={
        "admin": "Full access to admin features"
    }
)

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
    scopes: List[str] = []
    exp: Optional[int] = None

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def initialize_database():
    """Initialize database with required initial data"""
    db = SessionLocal()
    try:
        admin = db.query(AdminUser).filter(AdminUser.username == "admin").first()
        if not admin:
            # Get admin password from environment variable or use default
            admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "change-me-immediately")
            admin_user = AdminUser(
                username="admin",
                password_hash=get_password_hash(admin_password),
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print(f"Created initial admin user with username: admin")
            print("Please change the password immediately after first login!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

def create_initial_admin():
    """Create initial admin user from environment variables"""
    db = SessionLocal()
    try:
        # Check if any admin exists
        admin = db.query(AdminUser).first()
        if not admin:
            username = "admin"
            password = "admin123"  # Default test password
                
            admin = AdminUser(
                username=username,
                password_hash=get_password_hash(password),
                is_active=True
            )
            db.add(admin)
            db.commit()
            print(f"Created test admin user")
    except Exception as e:
        print(f"Error creating initial admin: {e}")
        db.rollback()
    finally:
        db.close()

if not os.path.exists('attendance.db'):
    Base.metadata.create_all(engine)
    create_initial_admin()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def create_access_token(*, data: dict, scopes: List[str] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "iss": settings.JWT_ISSUER,
        "aud": settings.JWT_AUDIENCE,
        "scopes": scopes or []
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(username: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return create_access_token(
        data={"sub": username, "type": "refresh"},
        scopes=["refresh"]
    )

async def get_current_user(
    security_scopes: SecurityScopes,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> AdminUser:
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER
        )
        
        username: str = payload.get("sub")
        token_scopes = payload.get("scopes", [])
        
        if username is None:
            raise credentials_exception
            
        if security_scopes.scopes and not any(scope in token_scopes for scope in security_scopes.scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )
            
        user = get_admin_user_by_username(db, username)
        if user is None or not user.is_active:
            raise credentials_exception
            
        return user
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": authenticate_value},
        )
    except jwt.JWTError:
        raise credentials_exception

def get_admin_user_by_username(db: Session, username: str):
    return db.query(AdminUser).filter(
        AdminUser.username == username
    ).first()

def authenticate_admin_user(db: Session, username: str, password: str):
    user = get_admin_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user
