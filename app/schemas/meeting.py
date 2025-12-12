from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.schemas.user import UserOut


class MeetingCreate(BaseModel):
    title: str
    start_time: datetime
    end_time: datetime
    participant_ids: List[int]


class MeetingOut(BaseModel):
    id: int
    title: str
    start_time: datetime
    end_time: datetime
    creator: UserOut
    participants: List[UserOut]

    class Config:
        from_attributes = True