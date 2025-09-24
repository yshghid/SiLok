from pydantic import BaseModel

class EmployeeCreate(BaseModel):
    name: str
    email: str
    password: str

class EmployeeLogin(BaseModel):
    email: str
    password: str

class EmployeeOut(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        from_attributes = True
