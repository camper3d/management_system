from fastapi import FastAPI, Request
from backend.models.base import Base, engine
from backend.api import auth, team, task, evaluation, meeting, event_calendar
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import os
from backend.middleware.auth_middleware import AuthMiddleware
from backend.api.html_views import html_router
from backend.api.auth import auth_api_router, auth_html_router


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


app = FastAPI(title="MVP")

app.state.templates = templates

static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


app.add_middleware(AuthMiddleware)
app.include_router(auth_html_router)
app.include_router(html_router)

# app.include_router(auth.router, prefix="/api")
app.include_router(auth_api_router, prefix="/api")
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
    """
    Создание таблиц при запуске приложения, если база не создана.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
