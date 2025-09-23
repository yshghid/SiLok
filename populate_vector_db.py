import os

from typing import List
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

def embed_and_store_data(
    slack_items: List[SlackData] = [],
    notion_items: List[NotionData] = [],
    onedrive_items: List[OnedriveData] = [],
    outlook_items: List[OutlookData] = []
) -> PGVector:
    """
    다양한 소스의 데이터를 LangChain Document로 변환하고
    임베딩하여 PGVector에 저장합니다.
    """
    
    all_docs = []

    # 각 데이터 소스를 공통 LangChain Document 형식으로 변환
    for item in slack_items:
        all_docs.append(Document(
            page_content=item.content,
            metadata={"source": "slack", "user": item.user_name, "channel": item.channel_name, "date": item.date}
        ))
    
    for item in notion_items:
        all_docs.append(Document(
            page_content=item.content,
            metadata={"source": "notion", "title": item.title, "author": item.author, "url": item.url, "date": item.date}
        ))
        
    for item in onedrive_items:
        all_docs.append(Document(
            page_content=item.content,
            metadata={"source": "onedrive", "file_name": item.file_name, "path": item.file_path, "date": item.date}
        ))

    for item in outlook_items:
        all_docs.append(Document(
            page_content=item.content,
            metadata={"source": "outlook", "subject": item.subject, "sender": item.sender, "date": item.date}
        ))

    if not all_docs:
        print("저장할 데이터가 없습니다.")
        return None

    print(f"총 {len(all_docs)}개의 문서를 임베딩하여 DB에 저장합니다...")

    # 문서 임베딩과 DB 저장
    db = PGVector.from_documents(
        embedding=embeddings,
        documents=all_docs,
        collection_name=COLLECTION_NAME,
        connection_string=CONNECTION_STRING
    )
    
    print(f"✅ 데이터 저장을 완료했습니다.")
    return db

if __name__ == "__main__":
    # 샘플 데이터
    sample_slack = [SlackData(id=1, content="오후 3시에 회의 시작하겠습니다.", channel_name="general", user_name="김민준", date="2025-09-23")]
    sample_notion = [NotionData(id=1, content="이번 회의의 주요 안건은 3분기 실적 리뷰입니다.", title="3분기 회의록", author="박서연", date="2025-09-23", url="http://notion.so/123")]
    sample_onedrive = [OnedriveData(id=1, content="실적 발표 자료 최종본입니다.", file_name="실적발표.pptx", file_path="/reports", author="김민준", date="2025-09-22")]
    sample_outlook = [OutlookData(id=1, content="안녕하세요, 3분기 실적 자료 전달드립니다.", subject="[전달] 3분기 실적 자료", sender="박서연@company.com", date="2025-09-22")]

    vector_store = embed_and_store_data(
        slack_items=sample_slack,
        notion_items=sample_notion,
        onedrive_items=sample_onedrive,
        outlook_items=sample_outlook
    )

    # test
    if vector_store:
        query = "3분기 실적"
        results = vector_store.similarity_search(query, k=2)
        print(f"\n--- '{query}' 검색 결과 ---")
        for doc in results:
            print(f"출처: {doc.metadata['source']}, 내용: {doc.page_content[:50]}...")