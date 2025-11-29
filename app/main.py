from fastapi import FastAPI
from .core.config import settings

app = FastAPI(title="MVP")


@app.get("/")
def get_message():
    return {"message": "Добро пожаловать!"}