from pydantic import BaseModel
from typing import List
from app.schemas.user import UserOut


class TeamCreate(BaseModel):
    name: str


class TeamMemberUpdate(BaseModel):
    user_id: int
    role: str  


class TeamOut(BaseModel):
    id: int
    name: str
    admin_id: int
    members: List[UserOut]

    class Config:
        from_attributes = True