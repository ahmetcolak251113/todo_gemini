from fastapi import APIRouter, Depends, Path, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse
from models import Base, Todo
from database import engine, SessionLocal
from typing import Annotated
from routers.auth import get_current_user
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import os
import requests  # Standart istek kütüphanesi
import markdown
from bs4 import BeautifulSoup
from pathlib import Path as FilePath

router = APIRouter(
    prefix="/todo",
    tags=["Todo"],
)

templates = Jinja2Templates(directory="templates")


class TodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=1000)
    priority: int = Field(gt=0, lt=6)
    complete: bool


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie("access_token")
    return redirect_response


@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todo).filter(Todo.owner_id == user.get('id')).all()
        return templates.TemplateResponse("todo.html", {"request": request, "todos": todos, "user": user})
    except:
        return redirect_to_login()


@router.get("/add-todo-page")
async def render_add_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse("add-todo.html", {"request": request, "user": user})
    except:
        return redirect_to_login()


@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todo = db.query(Todo).filter(Todo.id == todo_id).first()
        return templates.TemplateResponse("edit-todo.html", {"request": request, "todo": todo, "user": user})
    except:
        return redirect_to_login()


@router.get("/")
async def read_all(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(Todo).filter(Todo.owner_id == user.get('id')).all()


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_by_id(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is not None:
        return todo
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    todo = Todo(**todo_request.dict(), owner_id=user.get('id'))
    todo.description = create_todo_with_gemini(todo.description)
    db.add(todo)
    db.commit()


@router.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(user: user_dependency, db: db_dependency, todo_request: TodoRequest, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    todo.title = todo_request.title
    todo.description = todo_request.description
    todo.priority = todo_request.priority
    todo.complete = todo_request.complete
    db.add(todo)
    db.commit()


@router.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    todo = db.query(Todo).filter(Todo.id == todo_id).filter(Todo.owner_id == user.get('id')).first()
    if todo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
    db.delete(todo)
    db.commit()


def markdown_to_text(markdown_string):
    try:
        html = markdown.markdown(markdown_string)
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text()
        return text
    except Exception:
        return markdown_string


# --- AKILLI MODEL BULUCU ---
def get_working_model(api_key):
    """API Anahtarının yetkili olduğu modelleri sorgular ve ilk çalışanı döndürür."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        data = response.json()

        if 'models' in data:
            for model in data['models']:
                # 'generateContent' özelliğini destekleyen bir model arıyoruz
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    # Model adını temizle (örn: models/gemini-pro -> gemini-pro)
                    model_name = model['name'].replace("models/", "")
                    print(f"✅ Bulunan Çalışan Model: {model_name}")
                    return model_name
    except Exception as e:
        print(f"Model bulma hatası: {e}")

    # Hiçbir şey bulunamazsa varsayılanı dene
    return "gemini-1.5-flash"


def markdown_to_text(markdown_text:str):
    html = markdown.markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text()
    return text

def create_todo_with_gemini(todo_string: str):
    # .env dosyasını bul
    try:
        env_path = FilePath(__file__).parent.parent / ".env"
        load_dotenv(dotenv_path=env_path)
    except Exception:
        load_dotenv()

    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("HATA: Google API Key bulunamadı!")
        return todo_string

        # 1. Adım: Çalışan bir model bul
    model_name = get_working_model(api_key)

    # 2. Adım: O modele istek at
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    headers = {"Content-Type": "application/json"}
    prompt = f"Create a comprehensive description for this todo item: {todo_string}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            print(f"API Hatası ({response.status_code}): {response.text}")
            return todo_string

        result = response.json()
        if 'candidates' in result and result['candidates']:
            generated_text = result['candidates'][0]['content']['parts'][0]['text']
            return markdown_to_text(generated_text)
        else:
            return markdown_to_text(todo_string)

    except Exception as e:
        print(f"Bağlantı Hatası: {str(e)}")
        return todo_string

# if __name__ == "__main__":
#     print(create_todo_with_gemini("Buy Milk"))