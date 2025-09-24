from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from backend import database, models, schemas
from backend.user_timeline_api import router as timeline_router

# DB 초기화 (데이터베이스가 사용 가능할 때만)
try:
    models.Base.metadata.create_all(bind=database.engine)
except Exception as e:
    print(f"데이터베이스 초기화 실패: {e}")
    print("데이터베이스가 없어도 API는 실행됩니다.")

app = FastAPI(title="Weekly Report Generator API")

# Vue 프론트엔드 (Vite 기본 포트) 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# User Timeline API 라우터 포함
app.include_router(timeline_router, prefix="/api", tags=["User Timeline"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/signup", response_model=schemas.EmployeeOut, tags=["Authentication"])
def signup(user: schemas.EmployeeCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Employee).filter(models.Employee.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    new_user = models.Employee(name=user.name, email=user.email, password=user.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login", tags=["Authentication"])
def login(user: schemas.EmployeeLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.Employee).filter(
        models.Employee.email == user.email,
        models.Employee.password == user.password
    ).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return {"success": True, "user": {"id": db_user.id, "name": db_user.name, "email": db_user.email}}
