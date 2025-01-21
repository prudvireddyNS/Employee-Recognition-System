import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, Float, PickleType, Index, event
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    position = Column(String, nullable=False)  # Added position column
    email = Column(String, unique=True)
    company_email = Column(String, unique=True)  # Added company_email column
    face_encoding = Column(PickleType, nullable=True)  # Add this line to store face encoding
    created_at = Column(DateTime, default=datetime.utcnow)
    attendances = relationship("Attendance", back_populates="employee")

class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)  # To prevent duplicate processing
    confidence = Column(Float)  # Store recognition confidence
    employee = relationship("Employee", back_populates="attendances")

class AdminUser(Base):
    __tablename__ = 'admin_users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

class APIKey(Base):
    __tablename__ = 'api_keys'
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)

# Update indexes (remove API key index)
Index('idx_employee_department', Employee.department)
Index('idx_attendance_timestamp', Attendance.timestamp)
Index('idx_attendance_employee', Attendance.employee_id)
Index('idx_admin_username', AdminUser.username)
Index('idx_api_key', APIKey.key)

# Create engine and session
engine = create_engine('sqlite:///attendance.db')
SessionLocal = sessionmaker(bind=engine)

# Optimize SQLite for better concurrent performance
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()
