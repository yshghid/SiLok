from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import List
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from langchain.schema.output_parser import StrOutputParser
from langchain_core.prompts import PromptTemplate
import fetch_reports
from langchain_openai import ChatOpenAI
from model.data import ReportRequest, ReportResponse, TimelineActivity, UserTimelineResponse
from pydantic import BaseModel
import dotenv   

dotenv.load_dotenv()

app = FastAPI()

# 데이터베이스 연결 설정 (로컬 PostgreSQL)
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/weekly_report_db"
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession)

# 데이터베이스 세션 의존성
async def get_db_session():
    async with async_session() as session:
        yield session

async def get_user_slack_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
    """사용자별 Slack 메시지 데이터 조회"""
    # 문자열을 date 객체로 변환
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    query = text("""
        SELECT
            s.id,
            s.content,
            s.receiver,
            s.sender,
            s.task_id,
            s."timestamp"::text as timestamp
        FROM public.slack s
        WHERE (s.sender = :user_id OR s.receiver = :user_id)
            AND DATE(s."timestamp") BETWEEN :start_date AND :end_date
        ORDER BY s."timestamp" DESC
    """)

    result = await session.execute(
        query,
        {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    activities = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        activities.append(TimelineActivity(
            source="slack",
            timestamp=row_dict["timestamp"],
            content=row_dict["content"],
            metadata={
                "sender": row_dict["sender"],
                "receiver": row_dict["receiver"],
                "task_id": row_dict["task_id"],
                "slack_id": row_dict["id"]
            }
        ))

    return activities

async def get_user_notion_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
    """사용자별 Notion 데이터 조회 (participant 테이블과 조인)"""
    # 문자열을 date 객체로 변환
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    query = text("""
        SELECT
            n.id,
            n.content,
            n.participant_id,
            n.task_id,
            n."timestamp"::text as timestamp,
            COALESCE(
                ARRAY_TO_STRING(
                    ARRAY_REMOVE(
                        ARRAY[p.p1, p.p2, p.p3, p.p4, p.p5, p.p6],
                        NULL
                    ), ', '
                ), ''
            ) as participants
        FROM public.notion n
        LEFT JOIN public.participant p ON p.notion_id = n.id
        WHERE EXISTS (
            SELECT 1 FROM public.participant p2
            WHERE p2.notion_id = n.id
            AND :user_id IN (p2.p1, p2.p2, p2.p3, p2.p4, p2.p5, p2.p6)
        )
        AND DATE(n."timestamp") BETWEEN :start_date AND :end_date
        ORDER BY n."timestamp" DESC
    """)

    result = await session.execute(
        query,
        {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    activities = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        activities.append(TimelineActivity(
            source="notion",
            timestamp=row_dict["timestamp"],
            content=row_dict["content"],
            metadata={
                "participant_id": row_dict["participant_id"],
                "participants": row_dict["participants"],
                "task_id": row_dict["task_id"],
                "notion_id": row_dict["id"]
            }
        ))

    return activities

async def get_user_onedrive_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
    """사용자별 OneDrive 데이터 조회"""
    # 문자열을 date 객체로 변환
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    query = text("""
        SELECT
            od.id,
            od.content,
            od.writer,
            od.task_id,
            od."timestamp"::text as timestamp
        FROM public.onedrive od
        WHERE od.writer = :user_id
            AND DATE(od."timestamp") BETWEEN :start_date AND :end_date
        ORDER BY od."timestamp" DESC
    """)

    result = await session.execute(
        query,
        {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    activities = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        # content에서 파일명 추출 시도
        file_name = "Unknown File"
        content = row_dict["content"] or ""
        if "문서명:" in content:
            try:
                file_name = content.split("문서명:")[1].split("\n")[0].strip()
            except:
                pass

        activities.append(TimelineActivity(
            source="onedrive",
            timestamp=row_dict["timestamp"],
            content=row_dict["content"],
            metadata={
                "writer": row_dict["writer"],
                "file_name": file_name,
                "task_id": row_dict["task_id"],
                "onedrive_id": row_dict["id"]
            }
        ))

    return activities

async def get_user_outlook_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
    """사용자별 Outlook 데이터 조회"""
    # 문자열을 date 객체로 변환
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    query = text("""
        SELECT
            o.id,
            o.content,
            o.sender,
            o.receiver,
            o.task_id,
            o."timestamp"::text as timestamp
        FROM public.outlook o
        WHERE (o.sender = :user_id OR o.receiver = :user_id)
            AND DATE(o."timestamp") BETWEEN :start_date AND :end_date
        ORDER BY o."timestamp" DESC
    """)

    result = await session.execute(
        query,
        {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    activities = []
    for row in result.fetchall():
        row_dict = dict(row._mapping)
        # content에서 제목 추출 시도
        subject = "No Subject"
        content = row_dict["content"] or ""
        if "제목:" in content:
            try:
                subject = content.split("제목:")[1].split("\n")[0].strip()
            except:
                pass

        activities.append(TimelineActivity(
            source="outlook",
            timestamp=row_dict["timestamp"],
            content=row_dict["content"],
            metadata={
                "sender": row_dict["sender"],
                "receiver": row_dict["receiver"],
                "subject": subject,
                "task_id": row_dict["task_id"],
                "outlook_id": row_dict["id"]
            }
        ))

    return activities

@app.get("/api/user-timeline/{user_id}", response_model=UserTimelineResponse)
async def get_user_timeline(
    user_id: str,
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    특정 사용자의 모든 활동 데이터를 시간순으로 통합 조회합니다.

    - **user_id**: 사용자 이름 (예: 서은수, 윤소현, 박현규 등)
    - **start_date**: 조회 시작 날짜
    - **end_date**: 조회 종료 날짜

    Returns:
    - 시간순으로 정렬된 모든 활동 데이터 (Slack, Notion, OneDrive, Outlook)
    """

    try:
        # 4개 데이터 소스를 순차적으로 조회 (세션 충돌 방지)
        slack_data = await get_user_slack_data(user_id, start_date, end_date, session)
        notion_data = await get_user_notion_data(user_id, start_date, end_date, session)
        onedrive_data = await get_user_onedrive_data(user_id, start_date, end_date, session)
        outlook_data = await get_user_outlook_data(user_id, start_date, end_date, session)

        # 모든 활동을 하나의 리스트로 통합
        all_activities = []
        all_activities.extend(slack_data)
        all_activities.extend(notion_data)
        all_activities.extend(onedrive_data)
        all_activities.extend(outlook_data)

        # 시간순 정렬 (최신순)
        all_activities.sort(key=lambda x: x.timestamp, reverse=True)

        return UserTimelineResponse(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            activities=all_activities,
            summary={
                "total_count": len(all_activities),
                "slack_count": len(slack_data),
                "notion_count": len(notion_data),
                "onedrive_count": len(onedrive_data),
                "outlook_count": len(outlook_data)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}")

@app.get("/api/user-summary/{user_id}")
async def get_user_activity_summary(
    user_id: str,
    start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    session: AsyncSession = Depends(get_db_session)
):
    """사용자별 활동 요약 정보 조회"""
    # 문자열을 date 객체로 변환
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

    # 각 소스별 건수만 조회하는 가벼운 쿼리
    summary_query = text("""
        SELECT
            (SELECT COUNT(*) FROM public.slack
             WHERE (sender = :user_id OR receiver = :user_id)
             AND DATE("timestamp") BETWEEN :start_date AND :end_date) as slack_count,

            (SELECT COUNT(*) FROM public.notion n
             WHERE EXISTS (
                 SELECT 1 FROM public.participant p
                 WHERE p.notion_id = n.id
                 AND :user_id IN (p.p1, p.p2, p.p3, p.p4, p.p5, p.p6)
             ) AND DATE(n."timestamp") BETWEEN :start_date AND :end_date) as notion_count,

            (SELECT COUNT(*) FROM public.onedrive
             WHERE writer = :user_id
             AND DATE("timestamp") BETWEEN :start_date AND :end_date) as onedrive_count,

            (SELECT COUNT(*) FROM public.outlook
             WHERE (sender = :user_id OR receiver = :user_id)
             AND DATE("timestamp") BETWEEN :start_date AND :end_date) as outlook_count
    """)

    result = await session.execute(
        summary_query,
        {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
    )

    row = result.fetchone()
    if row:
        row_dict = dict(row._mapping)
        row_dict['total_count'] = sum(row_dict.values())
        row_dict['user_id'] = user_id
        return row_dict
    else:
        return {
            "user_id": user_id,
            "slack_count": 0,
            "notion_count": 0,
            "onedrive_count": 0,
            "outlook_count": 0,
            "total_count": 0
        }

@app.get("/api/users")
async def get_available_users(session: AsyncSession = Depends(get_db_session)):
    """사용 가능한 사용자 목록 조회"""
    try:
        query = text("""
            SELECT DISTINCT name FROM public.employee ORDER BY name
        """)

        result = await session.execute(query)
        users = [row[0] for row in result.fetchall()]

        return {
            "users": users,
            "count": len(users)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 오류: {str(e)}")

@app.get("/health")
async def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "message": "사용자 타임라인 API 서버가 정상 동작 중입니다."}

@app.get("/api/db-health")
async def database_health_check(session: AsyncSession = Depends(get_db_session)):
    """데이터베이스 연결 상태 확인"""
    try:
        # 각 테이블 존재 여부 확인
        tables_check = {}

        table_queries = {
            "slack": "SELECT COUNT(*) FROM public.slack LIMIT 1",
            "notion": "SELECT COUNT(*) FROM public.notion LIMIT 1",
            "onedrive": "SELECT COUNT(*) FROM public.onedrive LIMIT 1",
            "outlook": "SELECT COUNT(*) FROM public.outlook LIMIT 1",
            "participant": "SELECT COUNT(*) FROM public.participant LIMIT 1",
            "employee": "SELECT COUNT(*) FROM public.employee LIMIT 1"
        }

        for table_name, query in table_queries.items():
            try:
                result = await session.execute(text(query))
                count = result.scalar()
                tables_check[table_name] = {"exists": True, "count": count}
            except Exception as e:
                tables_check[table_name] = {"exists": False, "error": str(e)}

        return {
            "database_status": "connected",
            "tables": tables_check,
            "message": "데이터베이스 연결이 정상입니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"데이터베이스 연결 오류: {str(e)}")
    

# CORS 설정: 프론트엔드(Vue)
origins = [
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# LLM 로드 (OpenAI GPT-4o 사용)
llm = ChatOpenAI(model="gpt-4o", temperature=0.3)


# LangChain 프롬프트 템플릿
template = """
# 역할
당신은 팀의 성과를 한눈에 파악해야 하는 유능한 팀장입니다.

# 지시
아래에 제공되는 task별 팀원들의 주간 보고서 내용을 바탕으로, 팀 전체의 관점에서 **핵심 성과, 발견된 문제점, 그리고 다음 주 공통 목표**를 요약하여 관리자용 보고서를 작성해 주세요.

# 팀원별 보고 내용
{team_reports}

# 관리자용 요약 보고서:
"""

prompt = PromptTemplate.from_template(template)
output_parser = StrOutputParser()

# LangChain 체인 구성
chain = prompt | llm | output_parser

@app.post("/api/generate-summary", response_model=ReportResponse)
async def generate_summary(request: ReportRequest):
    """
    요청받은 task_id와 기간에 해당하는 팀원들의 보고서를 취합하여
    관리자용 요약 보고서를 생성합니다.
    """
    print(f"API 요청 수신: task_id={request.task_id}, 기간={request.start_date}~{request.end_date}")
    
    # 1. DB에서 데이터 가져오기
    team_reports_text = fetch_reports(
        task_id=request.task_id,
        start_date=request.start_date,
        end_date=request.end_date
    )

    if not team_reports_text:
        raise HTTPException(status_code=404, detail="해당 기간/태스크에 대한 보고서가 없습니다.")

    # 2. LangChain으로 관리자 보고서 생성
    try:
        print("🔄 관리자용 요약 보고서를 생성합니다...")
        manager_summary = await chain.invoke({"team_reports": team_reports_text})
        print("✅ 보고서 생성 완료")
        return ReportResponse(summary=manager_summary)
    except Exception as e:
        print(f"LLM 호출 중 오류 발생: {e}")
        raise HTTPException(status_code=500, detail="보고서 생성 중 오류가 발생했습니다.")

# 사용 예시
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

"""
🚀 사용자 타임라인 API 사용 예시:

📋 주요 기능:
- user_id 기반으로 모든 테이블 검색
- 시간순 통합 타임라인 제공
- 병렬 쿼리로 성능 최적화
- 메타데이터 구조화

🔍 사용 예시:

1. 특정 사용자의 모든 활동 조회:
GET /api/user-timeline/서은수?start_date=2025-09-22T00:00:00&end_date=2025-09-26T23:59:59

2. 사용자별 활동 요약:
GET /api/user-summary/윤소현?start_date=2025-09-22T00:00:00&end_date=2025-09-26T23:59:59

3. 사용 가능한 사용자 목록:
GET /api/users

4. 서버 상태 확인:
GET /health

5. 데이터베이스 연결 확인:
GET /api/db-health

📊 응답 예시:
{
  "user_id": "서은수",
  "start_date": "2025-09-22T00:00:00",
  "end_date": "2025-09-26T23:59:59",
  "activities": [
    {
      "source": "slack",
      "timestamp": "2025-09-26T17:20:45",
      "content": "이번 주 마감!...",
      "metadata": {
        "sender": "박현규",
        "receiver": "윤소현"
      }
    }
  ],
  "summary": {
    "total_count": 45,
    "slack_count": 30,
    "notion_count": 4,
    "onedrive_count": 4,
    "outlook_count": 7
  }
}

🏃‍♂️ 실행 방법:
python user_timeline_api.py

📱 Swagger UI:
http://localhost:8001/docs

⚠️ 주의사항:
- 포트 8001 사용 (기존 API와 구분)
- DATABASE_URL을 본인 환경에 맞게 수정
- 한글 사용자명 지원
"""