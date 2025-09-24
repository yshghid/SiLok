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
# DB 연결 정보
CONNECTION_STRING = os.getenv("DATABASE_URL")

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
