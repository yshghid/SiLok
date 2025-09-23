from pydantic import BaseModel

# Pydantic 모델 정의
class SlackData(BaseModel):
    id: int
    content: str
    channel_name: str
    user_name: str
    date: str

class NotionData(BaseModel):
    id: int
    content: str
    title: str
    author: str
    date: str
    url: str

class OnedriveData(BaseModel):
    id: int
    content: str
    file_name: str
    file_path: str
    author: str
    date: str

class OutlookData(BaseModel):
    id: int
    content: str
    subject: str
    sender: str
    date: str