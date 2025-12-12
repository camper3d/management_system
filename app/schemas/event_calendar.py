from pydantic import BaseModel
from datetime import datetime
from typing import Literal


class CalendarEvent(BaseModel):
    id: int
    title: str
    type: Literal["task", "meeting"]
    start: datetime
    end: datetime | None = None
    assignee_id: int | None = None
    creator_id: int


class DayEventsResponse(BaseModel):
    date: str
    events: list[CalendarEvent]


class MonthEventsResponse(BaseModel):
    year: int
    month: int
    days: dict[str, list[CalendarEvent]]  