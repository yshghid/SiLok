# weekly-report-generator
AI 기반 주간업무 보고서 자동 생성 시스템

## 1. fastapi-project
```bash
cd fastapi-project
python run_servers.py
```

FastAPI 서버가 `http://localhost:3306`에서 실행됩니다.
Streamlit이 `http://localhost:8501`에서 실행됩니다.


## 2. langchain-project
#### 1. 백엔드 서버 실행

```bash
cd langchain-project/backend
python main.py
```

또는 uvicorn으로 직접 실행:

```bash
cd langchain-project/backend
uvicorn main:app --port 8001 --reload
```

백엔드 서버가 `http://localhost:8001`에서 실행됩니다.

#### 2. 프론트엔드 서버 실행

```bash
cd langchain-project/frontend
npm run dev
```

프론트엔드가 `http://localhost:5173`에서 실행됩니다.
