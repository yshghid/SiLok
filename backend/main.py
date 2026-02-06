from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import List, Dict, Any
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
import dotenv
import os
from passlib.context import CryptContext
from sentence_transformers import SentenceTransformer
import numpy as np

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

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    start_date: str
    end_date: str
    task_name: str
    admin_request: str

#class ReportResponse(BaseModel):
#    summary: str
class ReportResponse(BaseModel):
    success: bool
    summary: str
    used_reports: List[Dict[str, Any]]  # 선택된 보고서 목록
    similarities: List[Dict[str, Any]]  # 각 보고서별 유사도


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
    try:
        # bcrypt로 검증 시도
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # bcrypt가 아니면 평문 비교
        return plain_password == hashed_password


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

# ====================================
# 보고서 임베딩 서비스
# ====================================
class ReportEmbeddingService:
    """
    보고서 임베딩 전용 서비스 클래스
    jhgan/ko-sbert-nli 모델을 사용하여 768차원 벡터 생성
    """

    def __init__(self):
        """임베딩 모델 초기화"""
        #self.model_name = "jhgan/ko-sbert-nli"
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = None
        self._initialize_model()

    def _initialize_model(self):
        """
        SentenceTransformer 모델 로드
        최초 실행시 모델 다운로드가 필요할 수 있음
        """
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"✅ 임베딩 모델 로드 성공: {self.model_name}")
        except Exception as e:
            print(f"❌ 임베딩 모델 로드 실패: {e}")
            raise

    def create_embedding(self, text: str) -> List[float]:
        """
        텍스트를 768차원 벡터로 변환

        Args:
            text (str): 임베딩할 텍스트 (보고서 내용)

        Returns:
            List[float]: 768차원 임베딩 벡터
        """
        if not text or not text.strip():
            raise ValueError("임베딩할 텍스트가 비어있습니다.")

        if self.model is None:
            raise RuntimeError("임베딩 모델이 초기화되지 않았습니다.")

        try:
            # 텍스트를 임베딩으로 변환 (768차원)
            embedding = self.model.encode(text.strip())

            # numpy array를 Python list로 변환
            embedding_list = embedding.tolist()

            print(f"📊 임베딩 생성 완료: {len(embedding_list)}차원")
            return embedding_list

        except Exception as e:
            print(f"❌ 임베딩 생성 실패: {e}")
            raise

    def create_vector_string(self, embedding: List[float]) -> str:
        """
        임베딩 리스트를 PostgreSQL vector 형식 문자열로 변환

        Args:
            embedding (List[float]): 768차원 임베딩 벡터

        Returns:
            str: PostgreSQL vector 형식 문자열 "[0.1,0.2,0.3,...]"
        """
        if not embedding:
            raise ValueError("임베딩 벡터가 비어있습니다.")

        if len(embedding) != 384: #768:
            raise ValueError(f"임베딩 차원이 올바르지 않습니다. 예상: 384, 실제: {len(embedding)}")

        # PostgreSQL vector 형식으로 변환
        vector_str = "[" + ",".join(map(str, embedding)) + "]"
        return vector_str

# 임베딩 서비스 인스턴스 생성 (전역)
embedding_service = ReportEmbeddingService()

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

async def insert_report(task_id: int, writer: str, email: str, content: str, session: AsyncSession) -> int:
    """
    보고서를 DB에 저장하고 생성된 report_id를 반환

    Returns:
        int: 생성된 report의 id
    """
    now = datetime.utcnow()
    query = text("""
        INSERT INTO public.report (task_id, "timestamp", writer, email, report)
        VALUES (:task_id, :timestamp, :writer, :email, :content)
        RETURNING id
    """)
    result = await session.execute(query, {
        "task_id": task_id,
        "timestamp": now,
        "writer": writer,
        "email": email,
        "content": content
    })
    report_id = result.fetchone()[0]
    await session.commit()
    return report_id

async def generate_report_with_fallback(task_id: int, platform_data: List[Dict[str, Any]], start_ts: str, end_ts: str, session: AsyncSession) -> str:
    """
    API 키 상태에 따라 실제 보고서 또는 더미 보고서를 생성하는 wrapper 함수

    Args:
        task_id: 작업 ID
        platform_data: 플랫폼 데이터 리스트
        start_ts: 시작 날짜
        end_ts: 종료 날짜
        session: DB 세션

    Returns:
        str: 생성된 보고서 내용
    """
    # OpenAI API 키가 있고 유효한지 확인
    if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("OPENAI_A") and len(OPENAI_API_KEY) >= 20:
        # 실제 OpenAI API를 사용한 보고서 생성
        return await generate_report_for_task(task_id, platform_data, start_ts, end_ts, session)
    else:
        # 더미 보고서 생성 (실제 보고서 형식 유지)
        print(f"🔄 OpenAI API 키가 없어서 더미 보고서를 생성합니다 - Task {task_id}")

        task_description = await get_task_description(task_id, session)
        actors = {d.get("actor") for d in platform_data if d.get("actor")}
        actor_list = "- " + "\n- ".join(actors) if actors else "- (참여자 없음)"

        # 실제 보고서와 동일한 구조로 더미 보고서 생성
        dummy_report = f"""# 업무 {task_id}: {task_description} 주간 보고서

## 1) 주간 요약
Task {task_id} ({task_description}) 관련 진행 상황:
- 프로젝트가 순조롭게 진행되고 있습니다.
- 주요 기능 개발이 완료되었습니다.
- 팀원들과의 협업이 효과적으로 이루어지고 있습니다.

## 2) 사람별 주요 산출물
{actor_list}

## 3) 협업 내역
팀원들 간의 Slack, Notion, Outlook, OneDrive를 통한 효과적인 협업이 이루어졌습니다.
주요 의사결정과 진행 상황 공유가 원활히 진행되었습니다.

## 4) 리스크/이슈
특별한 이슈 없이 계획대로 진행되었습니다.
향후 발생할 수 있는 리스크에 대한 모니터링을 지속하고 있습니다.

## 5) 차주 계획
다음 주에는 추가 개선 사항을 반영할 예정입니다.
팀원들과의 정기 회의를 통해 진행 상황을 점검할 계획입니다.

(기간: {start_ts} ~ {end_ts})"""

        return dummy_report

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

async def store_report_embedding_only(
    report_content: str,
    report_id: int,
    session: AsyncSession
) -> Dict[str, Any]:
    """
    이미 저장된 보고서에 임베딩만 추가하는 함수

    Args:
        report_content (str): 보고서 내용
        report_id (int): 저장된 보고서 ID
        session (AsyncSession): DB 세션

    Returns:
        Dict[str, Any]: 임베딩 저장 결과 정보
    """
    try:
        print(f"📊 임베딩 저장 시작 - Report ID {report_id}")

        # 1. 보고서 임베딩 생성
        embedding_vector = embedding_service.create_embedding(report_content)
        vector_string = embedding_service.create_vector_string(embedding_vector)

        # 2. 기존 보고서에 임베딩 업데이트
        query = text("""
            UPDATE public.report
            SET report_embedded = CAST(:report_embedded AS vector)
            WHERE id = :report_id
        """)

        await session.execute(query, {
            "report_embedded": vector_string,
            "report_id": report_id
        })
        await session.commit()

        print(f"✅ 임베딩 저장 완료 - Report ID {report_id}, 임베딩 차원: {len(embedding_vector)}")

        return {
            "success": True,
            "report_id": report_id,
            "embedding_dimension": len(embedding_vector),
            "report_length": len(report_content)
        }

    except Exception as e:
        print(f"❌ 임베딩 저장 실패 - Report ID {report_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"임베딩 저장 중 오류 발생: {str(e)}"
        )

async def store_report_with_embedding(
    task_id: int,
    report_content: str,
    start_date: str,
    end_date: str,
    writer: str = "system",
    email: str = "system@example.com",
    session: AsyncSession = None
) -> Dict[str, Any]:
    """
    보고서를 임베딩과 함께 DB에 저장하는 함수

    Args:
        task_id (int): 작업 ID
        report_content (str): 보고서 내용
        start_date (str): 시작 날짜
        end_date (str): 종료 날짜
        writer (str): 작성자 이름
        email (str): 작성자 이메일
        session (AsyncSession): DB 세션

    Returns:
        Dict[str, Any]: 저장 결과 정보
    """
    try:
        print(f"📝 보고서 저장 시작 - Task {task_id}")

        # 1. 보고서 임베딩 생성
        embedding_vector = embedding_service.create_embedding(report_content)
        vector_string = embedding_service.create_vector_string(embedding_vector)

        # 2. DB에 보고서와 임베딩 저장
        now = datetime.utcnow()
        query = text("""
            INSERT INTO public.report
            (task_id, "timestamp", writer, email, report, report_embedded)
            VALUES
            (:task_id, :timestamp, :writer, :email, :report, CAST(:report_embedded AS vector))
        """)

        await session.execute(query, {
            "task_id": task_id,
            "timestamp": now,
            "writer": writer,
            "email": email,
            "report": report_content,
            "report_embedded": vector_string
        })
        await session.commit()

        print(f"✅ 보고서 저장 완료 - Task {task_id}, 임베딩 차원: {len(embedding_vector)}")

        return {
            "success": True,
            "task_id": task_id,
            "report_length": len(report_content),
            "embedding_dimension": len(embedding_vector),
            "timestamp": now.isoformat(),
            "period": f"{start_date} ~ {end_date}"
        }

    except Exception as e:
        print(f"❌ 보고서 저장 실패 - Task {task_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"보고서 저장 중 오류 발생: {str(e)}"
        )

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

    activities = []
    counts = {"slack": 0, "notion": 0, "onedrive": 0, "outlook": 0}

    # 2. Slack 조회 (sender/receiver가 user_name인 경우)
    slack_query = text("""
        SELECT id, content, sender, receiver, task_id, "timestamp"::text as timestamp
        FROM public.slack
        WHERE (sender = :user_name OR receiver = :user_name)
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
        ORDER BY "timestamp" DESC
    """)
    slack_result = await session.execute(
        slack_query,
        {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj}
    )
    for row in slack_result.fetchall():
        r = dict(row._mapping)
        activities.append(TimelineActivity(
            source="slack",
            timestamp=r["timestamp"],
            content=r["content"],
            metadata={
                "sender": r["sender"],
                "receiver": r["receiver"],
                "task_id": r["task_id"],
                "slack_id": r["id"],
                "id": r["id"]
            }
        ))
        counts["slack"] += 1

    # 3. Notion 조회 (participant_id가 user_name인 경우)
    notion_query = text("""
        SELECT id, content, participant_id, task_id, "timestamp"::text as timestamp
        FROM public.notion
        WHERE participant_id = :user_name
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
        ORDER BY "timestamp" DESC
    """)
    notion_result = await session.execute(
        notion_query,
        {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj}
    )
    for row in notion_result.fetchall():
        r = dict(row._mapping)
        activities.append(TimelineActivity(
            source="notion",
            timestamp=r["timestamp"],
            content=r["content"],
            metadata={
                "sender": r["participant_id"],  # 작성자로 표시
                "receiver": "-",  # Notion은 수신자 없음
                "task_id": r["task_id"],
                "notion_id": r["id"],
                "id": r["id"]
            }
        ))
        counts["notion"] += 1

    # 4. OneDrive 조회 (writer가 user_name인 경우)
    onedrive_query = text("""
        SELECT id, content, writer, task_id, "timestamp"::text as timestamp
        FROM public.onedrive
        WHERE writer = :user_name
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
        ORDER BY "timestamp" DESC
    """)
    onedrive_result = await session.execute(
        onedrive_query,
        {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj}
    )
    for row in onedrive_result.fetchall():
        r = dict(row._mapping)
        activities.append(TimelineActivity(
            source="onedrive",
            timestamp=r["timestamp"],
            content=r["content"],
            metadata={
                "sender": r["writer"],  # 작성자로 표시
                "receiver": "-",  # OneDrive는 수신자 없음
                "task_id": r["task_id"],
                "onedrive_id": r["id"],
                "id": r["id"]
            }
        ))
        counts["onedrive"] += 1

    # 5. Outlook 조회 (sender/receiver가 user_name인 경우)
    outlook_query = text("""
        SELECT id, content, sender, receiver, task_id, "timestamp"::text as timestamp
        FROM public.outlook
        WHERE (sender = :user_name OR receiver = :user_name)
          AND DATE("timestamp") BETWEEN :start_date AND :end_date
        ORDER BY "timestamp" DESC
    """)
    outlook_result = await session.execute(
        outlook_query,
        {"user_name": user_name, "start_date": start_date_obj, "end_date": end_date_obj}
    )
    for row in outlook_result.fetchall():
        r = dict(row._mapping)
        activities.append(TimelineActivity(
            source="outlook",
            timestamp=r["timestamp"],
            content=r["content"],
            metadata={
                "sender": r["sender"],
                "receiver": r["receiver"],
                "task_id": r["task_id"],
                "outlook_id": r["id"],
                "id": r["id"]
            }
        ))
        counts["outlook"] += 1

    # 시간순 정렬
    activities.sort(key=lambda x: x.timestamp, reverse=True)

    return UserTimelineResponse(
        user_id=email,
        start_date=start_date,
        end_date=end_date,
        activities=activities,
        summary={"total_count": len(activities), **counts}
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
#@app.post("/api/generate-summary", response_model=ReportResponse)
#async def generate_summary(request: ReportRequest):
#    """기존 관리자 요약API (기존 기능 유지)"""
#    dummy_reports = f"Task {request.task_id} 보고서 (기간 {request.start_date}~{request.end_date})"
#    manager_summary = await manager_chain.ainvoke({"team_reports": dummy_reports})
#    return ReportResponse(summary=manager_summary)

from sqlalchemy import text
import numpy as np

# --- 요약 생성 - 소현 0927 ---
@app.post("/api/generate-summary", response_model=ReportResponse)
async def generate_summary(request: ReportRequest, session: AsyncSession = Depends(get_db_session)):
    """관리자 요약 API (임베딩 + 코사인 유사도 기반 + 디버깅 정보 포함)"""

    task_mapping = {
        "프로젝트 1: 온라인 쇼핑몰 시스템 구축": 1,
        "프로젝트 2: 병원 예약·진료 시스템 통합": 2,
    }
    task_id = task_mapping.get(request.task_name)
    if not task_id:
        raise HTTPException(status_code=400, detail="task_name이 올바르지 않습니다.")

    # 1. admin_request 임베딩 생성
    request_embedded = embedding_service.create_embedding(request.admin_request)
    request_embedded = np.array(request_embedded, dtype=np.float32)

    # 2. 해당 task_id 보고서 조회
    query = text("""
        SELECT id, report, report_embedded
        FROM public.report
        WHERE task_id = :task_id
    """)
    result = await session.execute(query, {"task_id": task_id})
    rows = result.fetchall()

    if not rows:
        return ReportResponse(
            success=False,
            summary="❌ 해당 task_id에 저장된 보고서가 없습니다.",
            used_reports=[],
            similarities=[]
        )

    reports_for_summary = []
    similarities = []

    for row in rows:
        rep_id = row[0]
        rep_content = row[1]
        rep_emb_str = row[2]

        if not rep_emb_str:
            continue

        # PostgreSQL vector → numpy array
        rep_emb = np.array(
            list(map(float, rep_emb_str.strip("[]").split(","))),
            dtype=np.float32
        )

        # cosine similarity 계산
        cosine_sim = float(
            np.dot(request_embedded, rep_emb) /
            (np.linalg.norm(request_embedded) * np.linalg.norm(rep_emb))
        )

        similarities.append({
            "report_id": rep_id,
            "similarity": cosine_sim
        })

        if cosine_sim >= 0.3:
            reports_for_summary.append({
                "report_id": rep_id,
                "content": rep_content,
                "similarity": cosine_sim
            })

    # context_summary 생성
    if reports_for_summary:
        context_summary = "\n".join([r["content"] for r in reports_for_summary])
    else:
        context_summary = "⚠️ 유사도가 0.3 이상인 보고서가 없습니다."

    # LLM 요약 실행
    manager_summary = await manager_chain.ainvoke({"team_reports": context_summary})

    return ReportResponse(
        success=True,
        summary=manager_summary,
        used_reports=reports_for_summary,
        similarities=similarities
    )

# --- 주간 보고서 생성 + 임베딩 저장 ---
@app.post("/reports/weekly")
async def make_weekly_report(p: ReportIn, session: AsyncSession = Depends(get_db_session)):
    """
    주간 보고서 생성 및 임베딩 저장 API

    흐름:
    1. 플랫폼별 데이터 수집 (Slack, Notion, Outlook, OneDrive)
    2. task_id별로 데이터 그룹핑
    3. 보고서 생성 (generate_report_with_fallback 사용)
       - OpenAI API 키 있음: 실제 LLM 보고서 생성
       - OpenAI API 키 없음: 더미 보고서 생성 (임시, 프로덕션에서 제거 필요)
    4. 보고서 DB 저장 (insert_report)
    5. 임베딩 생성 및 저장 (store_report_embedding_only)
       - jhgan/ko-sbert-nli 모델 사용 (768차원)
       - PostgreSQL vector 타입으로 저장

    Args:
        p (ReportIn): 플랫폼별 ID 목록, 기간, 작성자 정보

    Returns:
        dict: 생성된 보고서 목록 및 메타데이터

    Note:
        - 더미 보고서는 개발/테스트용이며 프로덕션에서는 제거 예정
    """
    reports = []

    # 1. 모든 플랫폼 데이터 수집
    all_platform_data = []
    for platform, ids in p.platform_ids.items():
        if not ids:
            continue

        query = None
        if platform == "slack":
            query = text("SELECT id, content, sender AS actor, receiver, task_id, \"timestamp\"::text as ts FROM public.slack WHERE id = ANY(:ids)")
        elif platform == "notion":
            query = text("SELECT id, content, NULL as actor, task_id, \"timestamp\"::text as ts FROM public.notion WHERE id = ANY(:ids)")
        elif platform == "outlook":
            query = text("SELECT id, content, sender AS actor, receiver, task_id, \"timestamp\"::text as ts FROM public.outlook WHERE id = ANY(:ids)")
        elif platform == "onedrive":
            query = text("SELECT id, content, writer AS actor, task_id, \"timestamp\"::text as ts FROM public.onedrive WHERE id = ANY(:ids)")

        # ✅ 여기 수정됨
        if query is not None:
            result = await session.execute(query, {"ids": ids})
            rows = [dict(r._mapping) for r in result.fetchall()]
            all_platform_data.extend(rows)

    # 2. task_id별 그룹핑
    grouped = {}
    for d in all_platform_data:
        task_id = d.get("task_id")
        if not task_id:
            continue
        grouped.setdefault(task_id, []).append(d)

    # 3. 보고서 생성
    for task_id, items in grouped.items():
        task_id_int = int(task_id)

        # 보고서 생성 (API 키 상태에 따라 자동 분기)
        report_md = await generate_report_with_fallback(task_id_int, items, p.start, p.end, session)

        # 보고서 저장 (report_id 반환)
        report_id = await insert_report(task_id_int, p.writer, p.email, report_md, session)

        # 임베딩 생성 및 저장
        await store_report_embedding_only(report_md, report_id, session)

        reports.append({"task_id": task_id_int, "report": report_md})

    return {
        "platform_ids": p.platform_ids,
        "range": {"start": p.start, "end": p.end},
        "reports": reports
    }


# ====================================
# 실행
# ====================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)
