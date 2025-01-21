from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List

class ImageData(BaseModel):
    image: str

class RegistrationData(BaseModel):
    image: str
    firstName: str
    lastName: str
    department: str
    position: str
    email: EmailStr

class FaceDetectionResponse(BaseModel):
    success: bool
    faces: Optional[List[dict]] = None
    message: Optional[str] = None

class FaceRecognitionResponse(BaseModel):
    success: bool
    name: Optional[str] = None
    department: Optional[str] = None
    timestamp: Optional[datetime] = None
    message: Optional[str] = None

class EmployeeResponse(BaseModel):
    id: int
    name: str
    department: str
    position: str
    email: str
    company_email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AttendanceResponse(BaseModel):
    id: int
    employee_name: str
    department: str
    timestamp: datetime
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class AdminUserCreate(BaseModel):
    username: str
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "username": "newadmin",
                "password": "strongpassword123"
            }
        }

class AdminUserLogin(BaseModel):
    username: str
    password: str

class AdminUserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: int
    key: str
    name: str
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
