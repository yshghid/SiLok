from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import asyncio

router = APIRouter()

# 데이터베이스 연결 설정 (로컬 PostgreSQL)
DATABASE_URL = "postgresql://postgres:6813@localhost:5432/dump"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 요청 모델
class UserTimelineRequest(BaseModel):
    user_id: str
    start_date: datetime
    end_date: datetime


# 응답 모델
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
    summary: Dict[str, int]

# 데이터베이스 세션 의존성
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_slack_data(user_id: str, start_date: datetime, end_date: datetime, session: Session) -> List[TimelineActivity]:
    """사용자별 Slack 메시지 데이터 조회"""
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
            AND s."timestamp" BETWEEN :start_date AND :end_date
        ORDER BY s."timestamp" DESC
    """)

    result = session.execute(
        query,
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
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

def get_user_notion_data(user_id: str, start_date: datetime, end_date: datetime, session: Session) -> List[TimelineActivity]:
    """사용자별 Notion 데이터 조회 (participant 테이블과 조인)"""
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
        AND n."timestamp" BETWEEN :start_date AND :end_date
        ORDER BY n."timestamp" DESC
    """)

    result = session.execute(
        query,
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
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

def get_user_onedrive_data(user_id: str, start_date: datetime, end_date: datetime, session: Session) -> List[TimelineActivity]:
    """사용자별 OneDrive 데이터 조회"""
    query = text("""
        SELECT
            od.id,
            od.content,
            od.writer,
            od.task_id,
            od."timestamp"::text as timestamp
        FROM public.onedrive od
        WHERE od.writer = :user_id
            AND od."timestamp" BETWEEN :start_date AND :end_date
        ORDER BY od."timestamp" DESC
    """)

    result = session.execute(
        query,
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
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

def get_user_outlook_data(user_id: str, start_date: datetime, end_date: datetime, session: Session) -> List[TimelineActivity]:
    """사용자별 Outlook 데이터 조회"""
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
            AND o."timestamp" BETWEEN :start_date AND :end_date
        ORDER BY o."timestamp" DESC
    """)

    result = session.execute(
        query,
        {"user_id": user_id, "start_date": start_date, "end_date": end_date}
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


@router.get("/user-timeline/{user_id}", response_model=UserTimelineResponse)
def get_user_timeline(
    user_id: str,
    start_date: datetime = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    session: Session = Depends(get_db_session)
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
        # 날짜에서 시간 부분 제거하고 하루의 시작과 끝으로 설정
        start_date_only = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date_only = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 4개 데이터 소스를 순차적으로 조회
        slack_data = get_user_slack_data(user_id, start_date_only, end_date_only, session)
        notion_data = get_user_notion_data(user_id, start_date_only, end_date_only, session)
        onedrive_data = get_user_onedrive_data(user_id, start_date_only, end_date_only, session)
        outlook_data = get_user_outlook_data(user_id, start_date_only, end_date_only, session)

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
            start_date=start_date_only.date().isoformat(),
            end_date=end_date_only.date().isoformat(),
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

@router.post("/user-timeline", response_model=UserTimelineResponse)
def get_user_timeline_post(
    request: UserTimelineRequest,
    session: Session = Depends(get_db_session)
):
    """
    POST 요청으로 특정 사용자의 모든 활동 데이터를 시간순으로 통합 조회합니다.
    시간까지 포함된 정확한 날짜/시간으로 조회합니다.

    - **user_id**: 사용자 이름 (예: 서은수, 윤소현, 박현규 등)
    - **start_date**: 조회 시작 날짜/시간 (YYYY-MM-DD HH:MM:SS)
    - **end_date**: 조회 종료 날짜/시간 (YYYY-MM-DD HH:MM:SS)

    Returns:
    - 시간순으로 정렬된 모든 활동 데이터 (Slack, Notion, OneDrive, Outlook)
    """
    try:
        # POST 요청에서는 시간까지 포함된 정확한 날짜/시간 사용
        start_date = request.start_date
        end_date = request.end_date
        
        # 4개 데이터 소스를 순차적으로 조회
        slack_data = get_user_slack_data(request.user_id, start_date, end_date, session)
        notion_data = get_user_notion_data(request.user_id, start_date, end_date, session)
        onedrive_data = get_user_onedrive_data(request.user_id, start_date, end_date, session)
        outlook_data = get_user_outlook_data(request.user_id, start_date, end_date, session)

        # 모든 활동을 하나의 리스트로 통합
        all_activities = []
        all_activities.extend(slack_data)
        all_activities.extend(notion_data)
        all_activities.extend(onedrive_data)
        all_activities.extend(outlook_data)

        # 시간순 정렬 (최신순)
        all_activities.sort(key=lambda x: x.timestamp, reverse=True)

        return UserTimelineResponse(
            user_id=request.user_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
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

@router.get("/user-summary/{user_id}")
def get_user_activity_summary(
    user_id: str,
    start_date: datetime = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
    end_date: datetime = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
    session: Session = Depends(get_db_session)
):
    """사용자별 활동 요약 정보 조회"""

    # 날짜에서 시간 부분 제거하고 하루의 시작과 끝으로 설정
    start_date_only = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date_only = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 각 소스별 건수만 조회하는 가벼운 쿼리
    summary_query = text("""
        SELECT
            (SELECT COUNT(*) FROM public.slack
             WHERE (sender = :user_id OR receiver = :user_id)
             AND "timestamp" BETWEEN :start_date AND :end_date) as slack_count,

            (SELECT COUNT(*) FROM public.notion n
             WHERE EXISTS (
                 SELECT 1 FROM public.participant p
                 WHERE p.notion_id = n.id
                 AND :user_id IN (p.p1, p.p2, p.p3, p.p4, p.p5, p.p6)
             ) AND n."timestamp" BETWEEN :start_date AND :end_date) as notion_count,

            (SELECT COUNT(*) FROM public.onedrive
             WHERE writer = :user_id
             AND "timestamp" BETWEEN :start_date AND :end_date) as onedrive_count,

            (SELECT COUNT(*) FROM public.outlook
             WHERE (sender = :user_id OR receiver = :user_id)
             AND "timestamp" BETWEEN :start_date AND :end_date) as outlook_count
    """)

    result = session.execute(
        summary_query,
        {"user_id": user_id, "start_date": start_date_only, "end_date": end_date_only}
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

@router.get("/users")
def get_available_users(session: Session = Depends(get_db_session)):
    """사용 가능한 사용자 목록 조회"""
    try:
        query = text("""
            SELECT DISTINCT name FROM public.employee ORDER BY name
        """)

        result = session.execute(query)
        users = [row[0] for row in result.fetchall()]

        return {
            "users": users,
            "count": len(users)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 오류: {str(e)}")

@router.get("/health")
def health_check():
    """서버 상태 확인"""
    return {"status": "healthy", "message": "사용자 타임라인 API 서버가 정상 동작 중입니다."}

@router.get("/db-health")
def database_health_check(session: Session = Depends(get_db_session)):
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
                result = session.execute(text(query))
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

# router 반환

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
http://localhost:8000/docs

⚠️ 주의사항:
- 포트 8001 사용 (기존 API와 구분)
- DATABASE_URL을 본인 환경에 맞게 수정
- 한글 사용자명 지원
"""


# ######################################################################################################33
# from fastapi import FastAPI, HTTPException, Depends, Query
# from sqlalchemy import text
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
# from pydantic import BaseModel
# from typing import List, Dict, Any
# from datetime import datetime, date
# import asyncio

# app = FastAPI()

# # 데이터베이스 연결 설정 (로컬 PostgreSQL)
# DATABASE_URL = "postgresql+asyncpg://postgres:6813@localhost:5432/dump"
# engine = create_async_engine(DATABASE_URL)
# async_session = async_sessionmaker(engine, class_=AsyncSession)

# # 응답 모델
# class TimelineActivity(BaseModel):
#     source: str
#     timestamp: str
#     content: str
#     metadata: Dict[str, Any]

# class UserTimelineResponse(BaseModel):
#     user_id: str
#     start_date: str
#     end_date: str
#     activities: List[TimelineActivity]
#     summary: Dict[str, int]

# # 데이터베이스 세션 의존성
# async def get_db_session():
#     async with async_session() as session:
#         yield session

# async def get_user_slack_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
#     """사용자별 Slack 메시지 데이터 조회"""
#     # 문자열을 date 객체로 변환
#     start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
#     end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

#     query = text("""
#         SELECT
#             s.id,
#             s.content,
#             s.receiver,
#             s.sender,
#             s.task_id,
#             s."timestamp"::text as timestamp
#         FROM public.slack s
#         WHERE (s.sender = :user_id OR s.receiver = :user_id)
#             AND DATE(s."timestamp") BETWEEN :start_date AND :end_date
#         ORDER BY s."timestamp" DESC
#     """)

#     result = await session.execute(
#         query,
#         {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
#     )

#     activities = []
#     for row in result.fetchall():
#         row_dict = dict(row._mapping)
#         activities.append(TimelineActivity(
#             source="slack",
#             timestamp=row_dict["timestamp"],
#             content=row_dict["content"],
#             metadata={
#                 "sender": row_dict["sender"],
#                 "receiver": row_dict["receiver"],
#                 "task_id": row_dict["task_id"],
#                 "slack_id": row_dict["id"]
#             }
#         ))

#     return activities

# async def get_user_notion_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
#     """사용자별 Notion 데이터 조회 (participant 테이블과 조인)"""
#     # 문자열을 date 객체로 변환
#     start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
#     end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

#     query = text("""
#         SELECT
#             n.id,
#             n.content,
#             n.participant_id,
#             n.task_id,
#             n."timestamp"::text as timestamp,
#             COALESCE(
#                 ARRAY_TO_STRING(
#                     ARRAY_REMOVE(
#                         ARRAY[p.p1, p.p2, p.p3, p.p4, p.p5, p.p6],
#                         NULL
#                     ), ', '
#                 ), ''
#             ) as participants
#         FROM public.notion n
#         LEFT JOIN public.participant p ON p.notion_id = n.id
#         WHERE EXISTS (
#             SELECT 1 FROM public.participant p2
#             WHERE p2.notion_id = n.id
#             AND :user_id IN (p2.p1, p2.p2, p2.p3, p2.p4, p2.p5, p2.p6)
#         )
#         AND DATE(n."timestamp") BETWEEN :start_date AND :end_date
#         ORDER BY n."timestamp" DESC
#     """)

#     result = await session.execute(
#         query,
#         {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
#     )

#     activities = []
#     for row in result.fetchall():
#         row_dict = dict(row._mapping)
#         activities.append(TimelineActivity(
#             source="notion",
#             timestamp=row_dict["timestamp"],
#             content=row_dict["content"],
#             metadata={
#                 "participant_id": row_dict["participant_id"],
#                 "participants": row_dict["participants"],
#                 "task_id": row_dict["task_id"],
#                 "notion_id": row_dict["id"]
#             }
#         ))

#     return activities

# async def get_user_onedrive_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
#     """사용자별 OneDrive 데이터 조회"""
#     # 문자열을 date 객체로 변환
#     start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
#     end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

#     query = text("""
#         SELECT
#             od.id,
#             od.content,
#             od.writer,
#             od.task_id,
#             od."timestamp"::text as timestamp
#         FROM public.onedrive od
#         WHERE od.writer = :user_id
#             AND DATE(od."timestamp") BETWEEN :start_date AND :end_date
#         ORDER BY od."timestamp" DESC
#     """)

#     result = await session.execute(
#         query,
#         {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
#     )

#     activities = []
#     for row in result.fetchall():
#         row_dict = dict(row._mapping)
#         # content에서 파일명 추출 시도
#         file_name = "Unknown File"
#         content = row_dict["content"] or ""
#         if "문서명:" in content:
#             try:
#                 file_name = content.split("문서명:")[1].split("\n")[0].strip()
#             except:
#                 pass

#         activities.append(TimelineActivity(
#             source="onedrive",
#             timestamp=row_dict["timestamp"],
#             content=row_dict["content"],
#             metadata={
#                 "writer": row_dict["writer"],
#                 "file_name": file_name,
#                 "task_id": row_dict["task_id"],
#                 "onedrive_id": row_dict["id"]
#             }
#         ))

#     return activities

# async def get_user_outlook_data(user_id: str, start_date: str, end_date: str, session: AsyncSession) -> List[TimelineActivity]:
#     """사용자별 Outlook 데이터 조회"""
#     # 문자열을 date 객체로 변환
#     start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
#     end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

#     query = text("""
#         SELECT
#             o.id,
#             o.content,
#             o.sender,
#             o.receiver,
#             o.task_id,
#             o."timestamp"::text as timestamp
#         FROM public.outlook o
#         WHERE (o.sender = :user_id OR o.receiver = :user_id)
#             AND DATE(o."timestamp") BETWEEN :start_date AND :end_date
#         ORDER BY o."timestamp" DESC
#     """)

#     result = await session.execute(
#         query,
#         {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
#     )

#     activities = []
#     for row in result.fetchall():
#         row_dict = dict(row._mapping)
#         # content에서 제목 추출 시도
#         subject = "No Subject"
#         content = row_dict["content"] or ""
#         if "제목:" in content:
#             try:
#                 subject = content.split("제목:")[1].split("\n")[0].strip()
#             except:
#                 pass

#         activities.append(TimelineActivity(
#             source="outlook",
#             timestamp=row_dict["timestamp"],
#             content=row_dict["content"],
#             metadata={
#                 "sender": row_dict["sender"],
#                 "receiver": row_dict["receiver"],
#                 "subject": subject,
#                 "task_id": row_dict["task_id"],
#                 "outlook_id": row_dict["id"]
#             }
#         ))

#     return activities

# @app.get("/api/user-timeline/{user_id}", response_model=UserTimelineResponse)
# async def get_user_timeline(
#     user_id: str,
#     start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
#     end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
#     session: AsyncSession = Depends(get_db_session)
# ):
#     """
#     특정 사용자의 모든 활동 데이터를 시간순으로 통합 조회합니다.

#     - **user_id**: 사용자 이름 (예: 서은수, 윤소현, 박현규 등)
#     - **start_date**: 조회 시작 날짜
#     - **end_date**: 조회 종료 날짜

#     Returns:
#     - 시간순으로 정렬된 모든 활동 데이터 (Slack, Notion, OneDrive, Outlook)
#     """

#     try:
#         # 4개 데이터 소스를 순차적으로 조회 (세션 충돌 방지)
#         slack_data = await get_user_slack_data(user_id, start_date, end_date, session)
#         notion_data = await get_user_notion_data(user_id, start_date, end_date, session)
#         onedrive_data = await get_user_onedrive_data(user_id, start_date, end_date, session)
#         outlook_data = await get_user_outlook_data(user_id, start_date, end_date, session)

#         # 모든 활동을 하나의 리스트로 통합
#         all_activities = []
#         all_activities.extend(slack_data)
#         all_activities.extend(notion_data)
#         all_activities.extend(onedrive_data)
#         all_activities.extend(outlook_data)

#         # 시간순 정렬 (최신순)
#         all_activities.sort(key=lambda x: x.timestamp, reverse=True)

#         return UserTimelineResponse(
#             user_id=user_id,
#             start_date=start_date,
#             end_date=end_date,
#             activities=all_activities,
#             summary={
#                 "total_count": len(all_activities),
#                 "slack_count": len(slack_data),
#                 "notion_count": len(notion_data),
#                 "onedrive_count": len(onedrive_data),
#                 "outlook_count": len(outlook_data)
#             }
#         )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"데이터 조회 중 오류가 발생했습니다: {str(e)}")

# @app.get("/api/user-summary/{user_id}")
# async def get_user_activity_summary(
#     user_id: str,
#     start_date: str = Query(..., description="시작 날짜 (YYYY-MM-DD)"),
#     end_date: str = Query(..., description="종료 날짜 (YYYY-MM-DD)"),
#     session: AsyncSession = Depends(get_db_session)
# ):
#     """사용자별 활동 요약 정보 조회"""
#     # 문자열을 date 객체로 변환
#     start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
#     end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

#     # 각 소스별 건수만 조회하는 가벼운 쿼리
#     summary_query = text("""
#         SELECT
#             (SELECT COUNT(*) FROM public.slack
#              WHERE (sender = :user_id OR receiver = :user_id)
#              AND DATE("timestamp") BETWEEN :start_date AND :end_date) as slack_count,

#             (SELECT COUNT(*) FROM public.notion n
#              WHERE EXISTS (
#                  SELECT 1 FROM public.participant p
#                  WHERE p.notion_id = n.id
#                  AND :user_id IN (p.p1, p.p2, p.p3, p.p4, p.p5, p.p6)
#              ) AND DATE(n."timestamp") BETWEEN :start_date AND :end_date) as notion_count,

#             (SELECT COUNT(*) FROM public.onedrive
#              WHERE writer = :user_id
#              AND DATE("timestamp") BETWEEN :start_date AND :end_date) as onedrive_count,

#             (SELECT COUNT(*) FROM public.outlook
#              WHERE (sender = :user_id OR receiver = :user_id)
#              AND DATE("timestamp") BETWEEN :start_date AND :end_date) as outlook_count
#     """)

#     result = await session.execute(
#         summary_query,
#         {"user_id": user_id, "start_date": start_date_obj, "end_date": end_date_obj}
#     )

#     row = result.fetchone()
#     if row:
#         row_dict = dict(row._mapping)
#         row_dict['total_count'] = sum(row_dict.values())
#         row_dict['user_id'] = user_id
#         return row_dict
#     else:
#         return {
#             "user_id": user_id,
#             "slack_count": 0,
#             "notion_count": 0,
#             "onedrive_count": 0,
#             "outlook_count": 0,
#             "total_count": 0
#         }

# @app.get("/api/users")
# async def get_available_users(session: AsyncSession = Depends(get_db_session)):
#     """사용 가능한 사용자 목록 조회"""
#     try:
#         query = text("""
#             SELECT DISTINCT name FROM public.employee ORDER BY name
#         """)

#         result = await session.execute(query)
#         users = [row[0] for row in result.fetchall()]

#         return {
#             "users": users,
#             "count": len(users)
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"사용자 목록 조회 오류: {str(e)}")

# @app.get("/health")
# async def health_check():
#     """서버 상태 확인"""
#     return {"status": "healthy", "message": "사용자 타임라인 API 서버가 정상 동작 중입니다."}

# @app.get("/api/db-health")
# async def database_health_check(session: AsyncSession = Depends(get_db_session)):
#     """데이터베이스 연결 상태 확인"""
#     try:
#         # 각 테이블 존재 여부 확인
#         tables_check = {}

#         table_queries = {
#             "slack": "SELECT COUNT(*) FROM public.slack LIMIT 1",
#             "notion": "SELECT COUNT(*) FROM public.notion LIMIT 1",
#             "onedrive": "SELECT COUNT(*) FROM public.onedrive LIMIT 1",
#             "outlook": "SELECT COUNT(*) FROM public.outlook LIMIT 1",
#             "participant": "SELECT COUNT(*) FROM public.participant LIMIT 1",
#             "employee": "SELECT COUNT(*) FROM public.employee LIMIT 1"
#         }

#         for table_name, query in table_queries.items():
#             try:
#                 result = await session.execute(text(query))
#                 count = result.scalar()
#                 tables_check[table_name] = {"exists": True, "count": count}
#             except Exception as e:
#                 tables_check[table_name] = {"exists": False, "error": str(e)}

#         return {
#             "database_status": "connected",
#             "tables": tables_check,
#             "message": "데이터베이스 연결이 정상입니다."
#         }

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"데이터베이스 연결 오류: {str(e)}")

# # 사용 예시
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8001)

# """
# 🚀 사용자 타임라인 API 사용 예시:

# 📋 주요 기능:
# - user_id 기반으로 모든 테이블 검색
# - 시간순 통합 타임라인 제공
# - 병렬 쿼리로 성능 최적화
# - 메타데이터 구조화

# 🔍 사용 예시:

# 1. 특정 사용자의 모든 활동 조회:
# GET /api/user-timeline/서은수?start_date=2025-09-22T00:00:00&end_date=2025-09-26T23:59:59

# 2. 사용자별 활동 요약:
# GET /api/user-summary/윤소현?start_date=2025-09-22T00:00:00&end_date=2025-09-26T23:59:59

# 3. 사용 가능한 사용자 목록:
# GET /api/users

# 4. 서버 상태 확인:
# GET /health

# 5. 데이터베이스 연결 확인:
# GET /api/db-health

# 📊 응답 예시:
# {
#   "user_id": "서은수",
#   "start_date": "2025-09-22T00:00:00",
#   "end_date": "2025-09-26T23:59:59",
#   "activities": [
#     {
#       "source": "slack",
#       "timestamp": "2025-09-26T17:20:45",
#       "content": "이번 주 마감!...",
#       "metadata": {
#         "sender": "박현규",
#         "receiver": "윤소현"
#       }
#     }
#   ],
#   "summary": {
#     "total_count": 45,
#     "slack_count": 30,
#     "notion_count": 4,
#     "onedrive_count": 4,
#     "outlook_count": 7
#   }
# }

# 🏃‍♂️ 실행 방법:
# python user_timeline_api.py

# 📱 Swagger UI:
# http://localhost:8001/docs

# ⚠️ 주의사항:
# - 포트 8001 사용 (기존 API와 구분)
# - DATABASE_URL을 본인 환경에 맞게 수정
# - 한글 사용자명 지원
# """