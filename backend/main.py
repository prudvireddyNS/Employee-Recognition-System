from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from facenet_pytorch import MTCNN, InceptionResnetV1
import torch
import numpy as np
from typing import List, Optional
import base64
import io
from PIL import Image
from datetime import datetime, timedelta, timezone
import pytz
import uuid
from .models import Employee, Activity
from .database import Database

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize face detection and recognition models
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
mtcnn = MTCNN(
    image_size=160, margin=0,
    min_face_size=20,
    thresholds=[0.6, 0.7, 0.7],
    factor=0.709,
    post_process=True,
    device=device
)
resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

# Initialize database
db = Database()

# Add IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Adjust threshold for face recognition
FACE_RECOGNITION_THRESHOLD = 0.6  # Decrease this value for stricter matching

def get_current_time():
    return datetime.now(IST)

class RegisterEmployee(BaseModel):
    image: str
    firstName: str
    lastName: str
    department: str
    position: str
    email: str

class FaceDetectionRequest(BaseModel):
    image: str

def decode_base64_image(base64_string: str):
    try:
        # Remove header if present
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
        
        # Decode base64 string to bytes
        image_bytes = base64.b64decode(base64_string)
        
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return np.array(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")

def detect_faces_mtcnn(image):
    # Convert numpy array to PIL Image if needed
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
    # Detect faces
    boxes, _ = mtcnn.detect(image)
    
    if boxes is None:
        return []
    
    # Convert boxes to expected format
    faces = []
    for box in boxes:
        left, top, right, bottom = [int(coord) for coord in box]
        faces.append({
            "top": top,
            "right": right,
            "bottom": bottom,
            "left": left
        })
    
    return faces

def get_face_embedding(image):
    # Convert numpy array to PIL Image if needed
    if isinstance(image, np.ndarray):
        image = Image.fromarray(image)
    
    # Get face embedding
    try:
        # Detect and align face
        face = mtcnn(image)
        if face is None:
            return None
        
        # Convert face to batch form
        face = face.unsqueeze(0).to(device)
        
        # Get embedding
        embedding = resnet(face)
        
        return embedding.detach().cpu().numpy()[0]
    except Exception as e:
        print(f"Error getting face embedding: {e}")
        return None

@app.post("/detect-faces")
async def detect_faces(request: FaceDetectionRequest):
    try:
        # Decode the base64 image
        image = decode_base64_image(request.image)
        
        # Detect faces using MTCNN
        faces = detect_faces_mtcnn(image)
        
        return {"success": True, "faces": faces}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/register-employee")
async def register_employee(employee_data: RegisterEmployee):
    try:
        # Decode and process the image
        image = decode_base64_image(employee_data.image)
        
        # Get face embedding
        face_embedding = get_face_embedding(image)
        if face_embedding is None:
            raise HTTPException(status_code=400, detail="No face detected in the image")
        
        # Generate company email
        company_email = f"{employee_data.firstName.lower()}.{employee_data.lastName.lower()}@company.com"
        
        # Create employee record
        employee = Employee(
            id=str(uuid.uuid4()),
            first_name=employee_data.firstName,
            last_name=employee_data.lastName,
            department=employee_data.department,
            position=employee_data.position,
            email=employee_data.email,
            company_email=company_email,
            face_embedding=face_embedding.tolist(),
            created_at=datetime.utcnow()
        )
        
        # Save to database
        db.add_employee(employee)
        
        return {
            "success": True,
            "company_email": company_email
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/recognize-face")
async def recognize_face(request: FaceDetectionRequest):
    try:
        # Decode the image
        image = decode_base64_image(request.image)
        
        # Get face embedding
        face_embedding = get_face_embedding(image)
        if face_embedding is None:
            return JSONResponse(
                status_code=400,
                content={"success": False, "message": "No face detected"}
            )
        
        # Get all employees
        employees = db.get_all_employees()
        
        # Improved face matching logic
        min_distance = float('inf')
        matched_employee = None
        face_embedding = face_embedding / np.linalg.norm(face_embedding)  # Normalize embedding
        
        for employee in employees:
            stored_embedding = np.array(employee.face_embedding)
            stored_embedding = stored_embedding / np.linalg.norm(stored_embedding)  # Normalize stored embedding
            distance = np.linalg.norm(face_embedding - stored_embedding)
            
            if distance < min_distance and distance < FACE_RECOGNITION_THRESHOLD:
                min_distance = distance
                matched_employee = employee
        
        if matched_employee:
            current_time = get_current_time()
            last_activity = db.get_last_activity(matched_employee.id)
            
            if last_activity:
                last_time = last_activity.timestamp.astimezone(IST)
                time_diff = current_time - last_time
                if time_diff < timedelta(minutes=10):
                    minutes_remaining = 10 - int(time_diff.total_seconds() / 60)
                    return JSONResponse(
                        status_code=200,
                        content={
                            "success": False,
                            "message": f"Already logged at {last_time.strftime('%I:%M %p')}. Try after {minutes_remaining} minutes.",
                            "cooldown": True
                        }
                    )

            # Record new activity with IST timezone
            activity = Activity(
                id=str(uuid.uuid4()),
                employee_id=matched_employee.id,
                timestamp=current_time
            )
            db.add_activity(activity)
            
            return {
                "success": True,
                "id": matched_employee.id,
                "name": f"{matched_employee.first_name} {matched_employee.last_name}",
                "department": matched_employee.department,
                "message": f"Attendance recorded at {current_time.strftime('%I:%M %p')}"
            }
        
        return JSONResponse(
            status_code=404,
            content={"success": False, "message": "Face not recognized"}
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/v1/recent-activity")
async def get_recent_activity():
    try:
        activities = db.get_recent_activities(limit=10)
        # Activities are already in IST format from the database
        return activities
    except Exception as e:
        print(f"Error in get_recent_activity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
