from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from backend import database, models, schemas


# DB 초기화
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Vue 프론트엔드 (Vite 기본 포트) 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.EmployeeOut)
def signup(user: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Employee).filter(models.Employee.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    new_user = models.Employee(name=user.name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login")
def login(user: schemas.EmployeeLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.Employee).filter(
        models.Employee.email == user.email,
        models.Employee.password == user.password
    ).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return {"success": True, "user": {"id": db_user.id, "name": db_user.name, "email": db_user.email}}
