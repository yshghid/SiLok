# API 요청/응답 모델 정의
from pydantic import BaseModel
from typing import List, Dict, Any

class ReportRequest(BaseModel):
    task_id: int
    start_date: str # 예: "2025-09-22"
    end_date: str   # 예: "2025-09-26"

class ReportResponse(BaseModel):
    summary: str

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
