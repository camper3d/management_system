from fastapi import FastAPI
from backend.models.base import Base, engine
from backend.api import auth, team, task, evaluation, meeting, event_calendar
from backend.core.config import settings


app = FastAPI(title="MVP")


app.include_router(auth.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(task.router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(meeting.router, prefix="/api")
app.include_router(event_calendar.router, prefix="/api")


import backend.admin


@app.get("/")
def get_message():
    return {"message": "Добро пожаловать!"}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
