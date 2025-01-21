from fastapi import APIRouter, Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import pandas as pd
import io
from .database import SessionLocal, Employee, Attendance, AdminUser, APIKey
from . import schemas
from .auth import get_current_user, verify_password, get_password_hash, create_access_token, authenticate_admin_user

# Split routes into public and protected with correct security
router_public = APIRouter(tags=["default"])
router_protected = APIRouter(
    tags=["admin"],
    dependencies=[Depends(get_current_user)]  # Simplified dependency
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_admin_user(db: Session, username: str, password: str):
    """Command to create admin user"""
    existing_admin = db.query(AdminUser).filter(
        AdminUser.username == username
    ).first()
    if (existing_admin):
        return False, "Admin user already exists"
    
    admin_user = AdminUser(
        username=username,
        password_hash=get_password_hash(password)
    )
    db.add(admin_user)
    db.commit()
    return True, "Admin user created successfully"

def update_api_key_status(db: Session, key: str, active: bool = True, expires_at: Optional[datetime] = None):
    """Command to update API key status"""
    try:
        api_key = db.query(APIKey).filter(APIKey.key == key).first()
        if not api_key:
            return False, "API key not found"
        
        api_key.is_active = active
        api_key.expires_at = expires_at
        db.commit()
        return True, "API key updated successfully"
    except Exception as e:
        db.rollback()
        return False, f"Error updating API key: {str(e)}"

# Public routes (no authentication required)
@router_public.post("/admin/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login endpoint for admin users"""
    try:
        user = authenticate_admin_user(db, form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
            
        # Include admin scope in token
        access_token = create_access_token(
            data={"sub": user.username},
            scopes=["admin"]
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "username": user.username
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# Protected routes (require authentication)
@router_protected.post("/admin/create", response_model=schemas.AdminUserResponse)
async def create_admin(
    admin_data: schemas.AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Create a new admin user (requires admin privileges)"""
    try:
        # Check if username already exists
        if db.query(AdminUser).filter(AdminUser.username == admin_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists"
            )

        # Create new admin user
        new_admin = AdminUser(
            username=admin_data.username,
            password_hash=get_password_hash(admin_data.password),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        
        return new_admin
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating admin user: {str(e)}"
        )

@router_protected.get("/admin/employees", response_model=List[schemas.EmployeeResponse])
async def get_all_employees(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    department: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get all employees with optional department filter"""
    query = db.query(Employee)
    if department:
        query = query.filter(Employee.department == department)
    employees = query.offset(skip).limit(limit).all()
    return employees

@router_protected.get("/admin/attendance/daily")
async def get_daily_attendance(
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user),
    date: Optional[str] = None,
    department: Optional[str] = None
):
    """Get daily attendance report"""
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()

        start_date = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        query = (
            db.query(Attendance)
            .join(Employee)
            .filter(Attendance.timestamp.between(start_date, end_date))
        )

        if department:
            query = query.filter(Employee.department == department)

        attendance_records = query.all()

        return [{
            "employee_name": record.employee.name,
            "department": record.employee.department,
            "check_in_time": record.timestamp.strftime("%I:%M %p"),
            "confidence": record.confidence
        } for record in attendance_records]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating report: {str(e)}"
        )

@router_protected.get("/admin/attendance/export")
async def export_attendance(
    start_date: str,
    end_date: str,
    department: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: AdminUser = Depends(get_current_user)
):
    """Export attendance records to CSV"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

        query = (
            db.query(
                Employee.name,
                Employee.department,
                Attendance.timestamp,
                Attendance.confidence
            )
            .join(Attendance)
            .filter(Attendance.timestamp.between(start, end))
        )

        if department:
            query = query.filter(Employee.department == department)

        records = query.all()

        # Convert to DataFrame
        df = pd.DataFrame(records, columns=['Name', 'Department', 'Timestamp', 'Confidence'])
        df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%d %I:%M %p')

        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False)
        
        return {
            "content": output.getvalue(),
            "filename": f"attendance_{start_date}_to_{end_date}.csv"
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error exporting data: {str(e)}"
        )

@router_protected.delete("/admin/employees/{employee_id}")
async def delete_employee(employee_id: int, db: Session = Depends(get_db), current_user: AdminUser = Depends(get_current_user)):
    """Delete an employee and their attendance records"""
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Employee not found"
            )

        # Delete attendance records first
        db.query(Attendance).filter(
            Attendance.employee_id == employee_id
        ).delete()

        # Delete employee
        db.delete(employee)
        db.commit()

        return {"message": "Employee deleted successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting employee: {str(e)}"
        )

@router_protected.get("/admin/statistics")
async def get_statistics(db: Session = Depends(get_db), current_user: AdminUser = Depends(get_current_user)):
    """Get system statistics"""
    try:
        total_employees = db.query(func.count(Employee.id)).scalar()
        total_attendance = db.query(func.count(Attendance.id)).scalar()
        
        department_stats = (
            db.query(
                Employee.department,
                func.count(Employee.id).label('count')
            )
            .group_by(Employee.department)
            .all()
        )

        today = datetime.now().date()
        today_attendance = (
            db.query(func.count(Attendance.id))
            .filter(func.date(Attendance.timestamp) == today)
            .scalar()
        )

        return {
            "total_employees": total_employees,
            "total_attendance": total_attendance,
            "today_attendance": today_attendance,
            "department_distribution": [
                {"department": dept, "count": count}
                for dept, count in department_stats
            ]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting statistics: {str(e)}"
        )