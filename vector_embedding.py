import os
import psycopg2
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain.schema import Document
from schemas.data import SlackData, NotionData, OnedriveData, OutlookData

from dotenv import load_dotenv
load_dotenv()

CONNECTION_STRING = os.getenv("DATABASE_URL")
COLLECTION_NAME = "weekly_report_documents"

# 임베딩 모델 설정
EMBEDDING_MODEL = "jhgan/ko-sbert-nli"
print(f"'{EMBEDDING_MODEL}' 임베딩 모델을 로드합니다...")
embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL, model_kwargs={'device': 'cpu'}, encode_kwargs={'normalize_embeddings': True}
)

# 임베딩을 처리할 테이블 목록
TABLES_TO_PROCESS = ["slack", "notion", "onedrive", "outlook"]

def create_embeddings():
    """
    각 테이블을 순회하며 content를 읽어 embedding 컬럼을 채웁니다.
    """
    conn = None
    try:
        # 데이터베이스 연결
        conn = psycopg2.connect(CONNECTION_STRING)
        cur = conn.cursor()
        print("✅ 데이터베이스에 성공적으로 연결했습니다.")

        for table_name in TABLES_TO_PROCESS:
            print(f"\n--- '{table_name}' 테이블 처리 시작 ---")

            # 아직 임베딩되지 않은 데이터만 선택 (WHERE embedding IS NULL)
            cur.execute(f"SELECT id, content FROM {table_name} WHERE embedding IS NULL;")
            rows_to_update = cur.fetchall()

            if not rows_to_update:
                print(f"'{table_name}' 테이블에 새로 처리할 데이터가 없습니다.")
                continue

            print(f"총 {len(rows_to_update)}개의 데이터를 임베딩합니다...")

            ids = [row[0] for row in rows_to_update]
            contents = [row[1] for row in rows_to_update]

            # content 목록을 한 번에 임베딩하여 효율성 증대
            vectors = embeddings.embed_documents(contents)

            # 각 row에 대해 UPDATE 쿼리 실행
            for i in range(len(ids)):
                # pgvector는 벡터를 문자열 형태로 입력받습니다.
                vector_str = str(vectors[i])
                cur.execute(
                    f"UPDATE {table_name} SET embedding = %s WHERE id = %s;",
                    (vector_str, ids[i])
                )
            
            # 변경사항 커밋
            conn.commit()
            print(f"✅ '{table_name}' 테이블의 {len(ids)}개 데이터 임베딩을 완료했습니다.")

    except Exception as e:
        print(f"오류 발생: {e}")
        if conn:
            conn.rollback() # 오류 발생 시 롤백
    finally:
        if conn:
            conn.close() # 연결 종료
            print("\n데이터베이스 연결을 종료했습니다.")


# --- 3. 실행 ---
if __name__ == "__main__":
    create_embeddings()