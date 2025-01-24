from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class Employee(BaseModel):
    id: str
    first_name: str
    last_name: str
    department: str
    position: str
    email: str
    company_email: str
    face_embedding: List[float]
    created_at: datetime

class Activity(BaseModel):
    id: str
    employee_id: str
    timestamp: datetime

class ActivityResponse(BaseModel):
    id: str
    name: str
    department: str
    lastAttendance: str
