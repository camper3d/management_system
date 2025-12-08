from pydantic import BaseModel
from typing import Optional


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str  

    class Config:
        from_attributes = True