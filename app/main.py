from fastapi import FastAPI
from app.models.base import Base, engine
from app.api.auth import router as auth_router
from app.api.team import router as team_router


app = FastAPI(title="MVP")


app.include_router(auth_router, prefix="/api")
app.include_router(team_router, prefix="/api")


@app.get("/")
def get_message():
    return {"message": "Добро пожаловать!"}


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
