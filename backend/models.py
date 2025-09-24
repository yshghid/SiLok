# backend/models.py
from backend.database import Base
from sqlalchemy import Column, Integer, String

class Employee(Base):
    __tablename__ = "employee"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
