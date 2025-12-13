from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from backend.schemas.user import UserOut


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    assignee_id: int


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class CommentCreate(BaseModel):
    content: str


class CommentOut(BaseModel):
    id: int
    content: str
    author: UserOut
    created_at: datetime

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    status: str
    creator: UserOut
    assignee: UserOut
    comments: List[CommentOut] = []

    class Config:
        from_attributes = True