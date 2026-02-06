# SiLok

AI 기반 주간업무 보고서 자동 생성 시스템

### 0. DB 설정

.env 파일이 있다고 가정
```bash
cd backend
# Docker Compose로 PostgreSQL 실행
docker-compose up -d
# 데이터베이스 확인
docker ps
```
PostgreSQL이 `localhost:5433`에서 실행됩니다.

```bash
psql -h localhost -p 5433 -U myuser -d mydatabase -f backend/sample_data.sql
```

### 1. 백엔드 서버 실행

```bash
cd backend
python main.py
```

또는 uvicorn으로 직접 실행:

```bash
cd backend
uvicorn main:app --port 8001 --reload
```

백엔드 서버가 `http://localhost:8001`에서 실행됩니다.

### 2. 프론트엔드 서버 실행

```bash
cd frontend
npm run dev
```

프론트엔드가 `http://localhost:5173`에서 실행됩니다.
