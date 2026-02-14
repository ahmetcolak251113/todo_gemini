from fastapi import Request
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import RedirectResponse

from models import Base, Todo
from database import engine, SessionLocal
from routers.auth import router as auth_router
from routers.todo import router as todo_router
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
@app.get("/")
def read_root(request: Request):
    return RedirectResponse(url="/todo/todo-page",status_code=302)

app.include_router(auth_router)
app.include_router(todo_router)

Base.metadata.create_all(bind=engine) # veri tabanını oluşturur
