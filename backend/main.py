import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, status, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from .database import SessionLocal, Employee, Attendance  # Import models directly from database
from . import schemas, face_recognition
from . import admin, database
from .middleware import log_request_middleware, JWTBearer
from .auth import get_current_user
from .config import get_settings
import redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from prometheus_fastapi_instrumentator import Instrumentator
import sentry_sdk
import logging
from prometheus_client import Counter, Histogram
import time
from fastapi.openapi.utils import get_openapi
from fastapi.security import OAuth2PasswordBearer, SecurityScopes
from contextlib import asynccontextmanager

# Configure logger
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Sentry for error tracking only if DSN is provided
SENTRY_DSN = os.getenv("SENTRY_DSN")
if SENTRY_DSN:
    try:
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            traces_sample_rate=1.0,
            environment=os.getenv("ENVIRONMENT", "development"),
            enable_tracing=True
        )
        logger.info("Sentry initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
else:
    logger.info("Sentry DSN not provided, skipping initialization")

# Define tags metadata
tags_metadata = [
    {
        "name": "default",
        "description": "Default operations for face recognition and attendance"
    },
    {
        "name": "admin",
        "description": "Administrative operations requiring authentication"
    }
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    redis_client = redis.from_url(settings.REDIS_URL, encoding="utf8")
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    yield
    # Shutdown
    await FastAPICache.clear()

app = FastAPI(
    title="Employee Recognition System",
    description="API for employee registration and face recognition",
    version="1.0.0",
    docs_url="/api/v1/docs",  # Update Swagger UI path
    redoc_url="/api/v1/redoc",  # Update ReDoc path
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "api/v1/admin/login",
                    "scopes": {}
                }
            }
        },
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    # Add global security
    openapi_schema["security"] = [
        {"OAuth2PasswordBearer": []},
        {"Bearer": []}
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

settings = get_settings()

# Add middleware
app.middleware("http")(log_request_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize monitoring
Instrumentator().instrument(app).expose(app)

# Enhanced metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

# API versioning
api_v1 = APIRouter(prefix="/api/v1")

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(time.time() - start_time)
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }
# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.error(f"Global error: {exc}", exc_info=True)
    # Capture in Sentry
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error"}
    )

# Remove these lines that use the old router
# admin_router = APIRouter(prefix="/admin", tags=["Admin"])
# for route in admin.router.routes:
#     if not route.path.endswith("/login"):
#         admin_router.routes.append(route)
# api_v1.include_router(admin.router, prefix="/admin", tags=["Admin"], include_in_schema=False)
# api_v1.include_router(admin_router)

# Replace with direct inclusion of the new public and protected routers
api_v1.include_router(admin.router_public)  # Include public admin routes (like login)
api_v1.include_router(admin.router_protected)  # Include protected admin routes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Public endpoints
@api_v1.post("/recognize-face", response_model=schemas.FaceRecognitionResponse)
async def recognize_face_endpoint(image_data: schemas.ImageData, db: Session = Depends(get_db)):
    try:
        # Extract face from image
        face_data = face_recognition.face_system.extract_face(image_data.image)
        if not face_data["success"]:
            return schemas.FaceRecognitionResponse(
                success=False,
                message=face_data["message"]
            )

        # Get all employees with face encodings
        employees = db.query(database.Employee).filter(
            database.Employee.face_encoding.isnot(None)
        ).all()

        # Check for matching employee
        for employee in employees:
            confidence = face_recognition.face_system.compare_faces_with_confidence(
                employee.face_encoding, 
                face_data["encoding"]
            )
            
            if confidence > 0.6:  # Confidence threshold
                # Check for recent attendance (within 5 minutes)
                recent_attendance = db.query(database.Attendance).filter(
                    database.Attendance.employee_id == employee.id,
                    database.Attendance.timestamp >= datetime.now() - timedelta(minutes=5)
                ).first()

                if recent_attendance:
                    return schemas.FaceRecognitionResponse(
                        success=True,
                        name=employee.name,
                        message="Attendance already marked",
                        timestamp=recent_attendance.timestamp
                    )

                # Create new attendance record
                attendance = database.Attendance(
                    employee_id=employee.id,
                    timestamp=datetime.now(),
                    confidence=confidence
                )
                db.add(attendance)
                db.commit()

                return schemas.FaceRecognitionResponse(
                    success=True,
                    name=employee.name,
                    department=employee.department,
                    timestamp=attendance.timestamp
                )

        return schemas.FaceRecognitionResponse(
            success=False,
            message="Face not recognized"
        )

    except Exception as e:
        print(f"Error recognizing face: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@api_v1.post("/detect-faces", response_model=schemas.FaceDetectionResponse)
async def detect_faces(image_data: schemas.ImageData):
    """Detect faces in an image and return their locations"""
    try:
        result = face_recognition.face_system.detect_faces(image_data.image)
        return result
    except Exception as e:
        print(f"Error detecting faces: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_v1.get("/recent-activity")
@cache(expire=60)
async def get_recent_activity(db: Session = Depends(get_db)):
    try:
        current_time = datetime.now()
        activities = (
            db.query(database.Attendance)
            .join(database.Employee)
            .filter(
                database.Attendance.timestamp >= current_time - timedelta(hours=24)
            )
            .order_by(database.Attendance.timestamp.desc())
            .limit(10)
            .all()
        )

        return [{
            "id": activity.id,
            "name": activity.employee.name,
            "department": activity.employee.department,
            "lastAttendance": activity.timestamp.strftime("%I:%M %p")
        } for activity in activities]

    except Exception as e:
        print(f"Error fetching recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent activity"
        )

# Protected endpoints
@api_v1.post("/register-employee", response_model=schemas.EmployeeResponse, dependencies=[Depends(JWTBearer())])
async def register_employee(request: Request, data: schemas.RegistrationData, db: Session = Depends(get_db)):
    try:
        print("Starting employee registration process")
        
        # Validate input data
        if not all([data.firstName, data.lastName, data.department, data.position, data.email, data.image]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All fields are required"
            )
            
        # Extract and validate face
        face_data = face_recognition.face_system.extract_face(data.image)
        if not face_data["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=face_data["message"]
            )

        # Check if email already exists
        existing_employee = db.query(database.Employee).filter(
            database.Employee.email == data.email
        ).first()
        
        if existing_employee:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        # Check if face already exists
        existing_face = db.query(database.Employee).filter(
            database.Employee.face_encoding.isnot(None)
        ).all()
        
        for emp in existing_face:
            if face_recognition.face_system.compare_faces(emp.face_encoding, face_data["encoding"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Face already registered"
                )

        # Create employee with face encoding
        try:
            employee = database.Employee(
                name=f"{data.firstName} {data.lastName}",
                department=data.department,
                position=data.position,
                email=data.email,
                company_email=f"{data.firstName.lower()}.{data.lastName.lower()}@company.com",
                face_encoding=face_data["encoding"],
                created_at=datetime.utcnow()
            )
            
            db.add(employee)
            db.commit()
            db.refresh(employee)
            
            return employee

        except Exception as e:
            db.rollback()
            print(f"Database error during registration: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register employee"
            )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Employee registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# Include routers
app.include_router(api_v1)
app.include_router(
    admin.router_public,
    prefix="/api/v1"
)
app.include_router(
    admin.router_protected,
    prefix="/api/v1"
)

# Ensure the root path is defined
@app.get("/")
async def read_root():
    return {"message": "Welcome to the Employee Recognition System API"}

# Ensure the docs path is correctly set
@app.get("/docs")
async def get_docs():
    return {"message": "Swagger UI is available at /api/v1/docs"}

# Ensure the redoc path is correctly set
@app.get("/redoc")
async def get_redoc():
    return {"message": "ReDoc is available at /api/v1/redoc"}
