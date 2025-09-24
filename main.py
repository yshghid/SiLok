import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import dotenv
from langchain.schema.output_parser import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import psycopg2
from typing import Optional

# .env 파일에서 환경변수 로드
dotenv.load_dotenv()

app = FastAPI(
    title="AI 주간업무 보고서 요약 API",
    description="팀원들의 주간 보고서를 취합하여 관리자용 요약 보고서를 생성합니다."
)

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

# DB 연결 정보
CONNECTION_STRING = os.getenv("DATABASE_URL")

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

# task_id 값, 시간을 기준으로 모든 사람의 보고서 내용(report 테이블의 content 컬럼)을 가져옴
def fetch_reports(task_id: int, start_date: str, end_date: str) -> str:
    """
    데이터베이스에 접속하여 특정 조건에 맞는 보고서 내용을 가져와 합칩니다.
    """
    all_contents = []
    conn = None # conn 변수 초기화
    try:
        conn = psycopg2.connect(CONNECTION_STRING)
        cur = conn.cursor()
        
        cur.execute(
            """
            SELECT writer, content FROM report 
            WHERE %s = task_id AND timestamp::date BETWEEN %s AND %s;
            """,
            (task_id, start_date, end_date)
        )
        rows = cur.fetchall()
        print(f"DB 조회 결과: {len(rows)}건")
        
        for row in rows:
            writer, content = row
            all_contents.append(f"## 작성자: {writer}\n{content}\n")
        
    except Exception as e:
        print(f"DB 접속 중 오류 발생: {e}")
        # 오류 발생 시 빈 리스트를 반환하도록 예외 처리
        return ""
    finally:
        if conn:
            cur.close()
            conn.close()
            
    return "---\n".join(all_contents)

# API 요청/응답 모델 정의

class ReportRequest(BaseModel):
    task_id: int
    start_date: str # 예: "2025-09-22"
    end_date: str   # 예: "2025-09-26"

class ReportResponse(BaseModel):
    summary: str

# API 엔드포인트 생성

@app.post("/generate-summary", response_model=ReportResponse)
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