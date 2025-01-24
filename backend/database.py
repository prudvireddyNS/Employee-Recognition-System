from typing import List, Optional
from .models import Employee, Activity, ActivityResponse
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

class Database:
    def __init__(self):
        self.employees: List[Employee] = []
        self.activities: List[Activity] = []

    def add_employee(self, employee: Employee):
        self.employees.append(employee)

    def get_all_employees(self) -> List[Employee]:
        return self.employees

    def add_activity(self, activity: Activity):
        # Ensure timestamp has timezone info
        if activity.timestamp.tzinfo is None:
            activity.timestamp = IST.localize(activity.timestamp)
        self.activities.append(activity)

    def get_last_activity(self, employee_id: str) -> Optional[Activity]:
        try:
            employee_activities = [
                a for a in self.activities 
                if a.employee_id == employee_id
            ]
            if not employee_activities:
                return None
                
            # Convert all timestamps to IST for comparison
            return max(
                employee_activities,
                key=lambda x: x.timestamp.astimezone(IST)
            )
        except Exception as e:
            print(f"Error in get_last_activity: {e}")
            return None

    def get_recent_activities(self, limit: int = 10) -> List[ActivityResponse]:
        try:
            # Get current time in IST
            now = datetime.now(IST)
            
            # Sort activities by timestamp in descending order
            recent = sorted(
                [a for a in self.activities if a.timestamp], 
                key=lambda x: x.timestamp.astimezone(IST),
                reverse=True
            )[:limit]
            
            responses = []
            for activity in recent:
                employee = next(
                    (e for e in self.employees if e.id == activity.employee_id), 
                    None
                )
                if employee:
                    ist_time = activity.timestamp.astimezone(IST)
                    responses.append(ActivityResponse(
                        id=f"{activity.id}-{ist_time.timestamp()}",  # Unique ID including timestamp
                        name=f"{employee.first_name} {employee.last_name}",
                        department=employee.department,
                        lastAttendance=ist_time.isoformat()
                    ))
            
            return responses
        except Exception as e:
            print(f"Error in get_recent_activities: {e}")
            return []
