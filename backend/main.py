from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import List, Dict, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema import Document
from langchain.schema.output_parser import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import dotenv
import os
from passlib.context import CryptContext

# ====================================
# 환경 변수 로드
# ====================================
dotenv.load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL 환경 변수가 설정되지 않았습니다.")
if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

# ====================================
# FastAPI app
# ====================================
app = FastAPI(title="User Timeline + Weekly Report Service", version="1.0")

# ====================================
# DB 연결
# ====================================
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession)

async def get_db_session():
    async with async_session() as session:
        yield session

# ====================================
# 데이터 모델
# ====================================
class TimelineActivity(BaseModel):
    source: str
    timestamp: str
    content: str
    metadata: Dict[str, Any]

class UserTimelineResponse(BaseModel):
    user_id: str
    start_date: str
    end_date: str
    activities: List[TimelineActivity]
    summary: Dict[str, Any]

class ReportRequest(BaseModel):
    task_id: int
    start_date: str
    end_date: str

class ReportResponse(BaseModel):
    summary: str

class ReportIn(BaseModel):
    platform_ids: Dict[str, List[int]]
    start: str
    end: str
    writer: str
    email: str

# ====================================
# 비밀번호 유틸
# ====================================
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ====================================
# 인증용 스키마
# ====================================
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
        orm_mode = True

# ====================================
# LLM
# ====================================
llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=OPENAI_API_KEY)
output_parser = StrOutputParser()

manager_prompt = PromptTemplate.from_template("""
# 역할
당신은 팀의 성과를 한눈에 파악해야 하는 유능한 팀장입니다.

# 지시
아래에 task별 팀원들의 주간 보고서를 바탕으로, 
**핵심 성과 / 문제점 / 다음 주 공통 목표**를 요약하세요.

# 팀원별 보고 내용
{team_reports}

# 관리자 요약 보고서:
""")
manager_chain = manager_prompt | llm | output_parser

REPORT_TEMPLATE = """
## 1) 주간 요약
Task {task_id} ({task_description}) 관련 진행 상황 요약:
{context}

## 2) 사람별 주요 산출물
{member_list}

## 3) 협업 내역
Slack/Notion/Outlook/OneDrive 기록 기반 협업 내역 정리.

## 4) 리스크/이슈
문제점, 리스크, 해결 필요 사항.

## 5) 차주 계획
후속 작업 및 개선점.

(기간: {start} ~ {end})
"""
report_prompt = PromptTemplate(
    template=REPORT_TEMPLATE,
    input_variables=["context", "task_id", "task_description", "member_list", "start", "end"],
)

# ====================================
# 유틸 함수
# ====================================
async def get_task_description(task_id: int, session: AsyncSession) -> str:
    query = text("SELECT description FROM public.task WHERE id = :task_id")
    result = await session.execute(query, {"task_id": task_id})
    row = result.fetchone()
    return row[0] if row else "(설명 없음)"

async def insert_report(task_id: int, writer: str, email: str, content: str, session: AsyncSession):
    now = datetime.utcnow()
    query = text("""
        INSERT INTO public.report (task_id, "timestamp", writer, email, content)
        VALUES (:task_id, :timestamp, :writer, :email, :content)
    """)
    await session.execute(query, {
        "task_id": task_id,
        "timestamp": now,
        "writer": writer,
        "email": email,
        "content": content
    })
    await session.commit()

async def generate_report_for_task(task_id: int, platform_data: List[Dict[str, Any]], start_ts: str, end_ts: str, session: AsyncSession) -> str:
    docs = [Document(page_content=d.get("content", "")) for d in platform_data]
    actors = {d.get("actor") for d in platform_data if d.get("actor")}
    actor_list = "- " + "\n- ".join(actors) if actors else "- (none)"
    task_description = await get_task_description(task_id, session)
    context = "\n".join([doc.page_content for doc in docs])

    chain = report_prompt | llm | output_parser
    body = await chain.ainvoke({
        "context": context,
        "task_id": task_id,
        "task_description": task_description,
        "member_list": actor_list,
        "start": start_ts,
        "end": end_ts,
    })
    return f"# 업무 {task_id}: {task_description} 주간 보고서\n\n{body}"

# ====================================
# API 엔드포인트
# ====================================

# --- 회원가입 ---
@app.post("/signup", response_model=EmployeeOut, tags=["Authentication"])
async def signup(user: EmployeeCreate, session: AsyncSession = Depends(get_db_session)):
    query = text("SELECT id FROM public.employee WHERE email = :email")
    result = await session.execute(query, {"email": user.email})
    if result.fetchone():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    hashed_pw = hash_password(user.password)
    insert_q = text("""
        INSERT INTO public.employee (name, email, password)
        VALUES (:name, :email, :password)
        RETURNING id, name, email
    """)
    res = await session.execute(insert_q, {"name": user.name, "email": user.email, "password": hashed_pw})
    await session.commit()
    row = res.fetchone()
    return {"id": row[0], "name": row[1], "email": row[2]}

# --- 로그인 ---
@app.post("/login", tags=["Authentication"])
async def login(user: EmployeeLogin, session: AsyncSession = Depends(get_db_session)):
    query = text("SELECT id, name, email, password FROM public.employee WHERE email = :email")
    result = await session.execute(query, {"email": user.email})
    row = result.fetchone()
    if not row or not verify_password(user.password, row[3]):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    return {"success": True, "user": {"id": row[0], "name": row[1], "email": row[2]}}

# --- 타임라인 조회 ---
@app.get("/api/user-timeline/{email}", response_model=UserTimelineResponse)
async def get_user_timeline(email: str, start_date: str, end_date: str, session: AsyncSession = Depends(get_db_session)):
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 1. email → name 변환
    q = text("SELECT name FROM public.employee WHERE email = :email")
    res = await session.execute(q, {"email": email})
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="해당 이메일의 사용자를 찾을 수 없습니다.")
    user_name = row[0]

    # 2. Slack 조회 (sender/receiver가 user_name인 경우)
    query = text("""
        SELECT id, content, sender, receiver, task_id, "timestamp"::text as timestamp
        FROM public.slack
        WHERE (sender = :user_name OR receiver = :user_name)
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
        ORDER BY "timestamp" DESC
    """)
    result = await session.execute(
        query,
        {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    activities = []
    for row in result.fetchall():
        r = dict(row._mapping)
        activities.append(TimelineActivity(
            source="slack",
            timestamp=r["timestamp"],
            content=r["content"],
            metadata={
                "sender": r["sender"],
                "receiver": r["receiver"],
                "task_id": r["task_id"],
                "slack_id": r["id"]
            }
        ))

    return UserTimelineResponse(
        user_id=email,  # 👈 email 기준
        start_date=start_date,
        end_date=end_date,
        activities=activities,
        summary={"total_count": len(activities), "slack_count": len(activities)}
    )


# --- 활동 요약 ---
@app.get("/api/user-summary/{email}")
async def get_user_summary(email: str, start_date: str, end_date: str, session: AsyncSession = Depends(get_db_session)):
    q = text("SELECT name FROM public.employee WHERE email = :email")
    res = await session.execute(q, {"email": email})
    row = res.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="해당 이메일의 사용자를 찾을 수 없습니다.")
    user_name = row[0]

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    query = text("""
        SELECT COUNT(*) 
        FROM public.slack
        WHERE (sender = :user_name OR receiver = :user_name)
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
    """)
    result = await session.execute(query, {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj})
    count = result.scalar()
    return {"email": email, "user_name": user_name, "total_count": count}

# --- 사용자 목록 ---
@app.get("/api/users")
async def get_available_users(session: AsyncSession = Depends(get_db_session)):
    query = text("SELECT DISTINCT name FROM public.employee ORDER BY name")
    result = await session.execute(query)
    users = [row[0] for row in result.fetchall()]
    return {"users": users, "count": len(users)}

# --- DB health ---
@app.get("/api/db-health")
async def db_health(session: AsyncSession = Depends(get_db_session)):
    try:
        result = await session.execute(text("SELECT 1"))
        return {"database_status": "connected", "result": result.scalar()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- 서비스 health ---
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# --- 요약 생성 ---
@app.post("/api/generate-summary", response_model=ReportResponse)
async def generate_summary(request: ReportRequest):
    dummy_reports = f"Task {request.task_id} 보고서 (기간 {request.start_date}~{request.end_date})"
    manager_summary = await manager_chain.ainvoke({"team_reports": dummy_reports})
    return ReportResponse(summary=manager_summary)

# --- 주간 보고서 생성 ---
@app.post("/reports/weekly")
async def make_weekly_report(p: ReportIn, session: AsyncSession = Depends(get_db_session)):
    reports = []
    all_platform_data = []

    for platform, ids in p.platform_ids.items():
        if not ids: continue
        query = None
        if platform == "slack":
            query = text("SELECT id, content, sender AS actor, receiver, task_id, \"timestamp\"::text as ts FROM public.slack WHERE id = ANY(:ids)")
        elif platform == "notion":
            query = text("SELECT id, content, NULL as actor, task_id, \"timestamp\"::text as ts FROM public.notion WHERE id = ANY(:ids)")
        elif platform == "outlook":
            query = text("SELECT id, content, sender AS actor, receiver, task_id, \"timestamp\"::text as ts FROM public.outlook WHERE id = ANY(:ids)")
        elif platform == "onedrive":
            query = text("SELECT id, content, writer AS actor, task_id, \"timestamp\"::text as ts FROM public.onedrive WHERE id = ANY(:ids)")

        if query:
            result = await session.execute(query, {"ids": ids})
            rows = [dict(r._mapping) for r in result.fetchall()]
            all_platform_data.extend(rows)

    grouped = {}
    for d in all_platform_data:
        task_id = d.get("task_id")
        if not task_id: continue
        grouped.setdefault(task_id, []).append(d)

    for task_id, items in grouped.items():
        task_id_int = int(task_id)
        report_md = await generate_report_for_task(task_id_int, items, p.start, p.end, session)
        await insert_report(task_id_int, p.writer, p.email, report_md, session)
        reports.append({"task_id": task_id_int, "report": report_md})

    return {"platform_ids": p.platform_ids, "range": {"start": p.start, "end": p.end}, "reports": reports}

# ====================================
# 실행
# ====================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
