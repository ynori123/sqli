from fastapi import FastAPI, Depends, Form, Request
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy.orm import sessionmaker
import hashlib
from dotenv import load_dotenv

load_dotenv(verbose=True)

dotenv_path = os.join(os.dirname(__file__), '.env')
load_dotenv(dotenv_path)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# disable docs
# app.redoc_url = None
# app.openapi_url = None
# app.docs_url = None

templates = Jinja2Templates(directory='templates')

DATABASE_URI = os.environ["DATABASE_URI"]
engine = create_engine(
    DATABASE_URI,
    connect_args={"check_same_thread": False}, 
    echo=True
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def session():
    db = Session()
    try:
        yield db
    finally:
        db.close()

Base = declarative_base()
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    password = Column(String(50))

@app.on_event("startup")
def startup(db: Session = Depends(session)):
    Base.metadata.create_all(bind=engine)
    plane_password = os.environ["FLAG"]
    target_user = User(username="admin", password=hashlib.sha256(plane_password.encode()).hexdigest())
    with Session() as db:
        existing_user = db.query(User).filter_by(username="admin").first()
        
        if not existing_user:
            db.add(target_user)
            db.commit()

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})

@app.post("/login")
async def login(request: Request, db: Session = Depends(session), username: str = Form(...), password: str = Form(...)):
    print(username, password)
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    query = text(f"SELECT * FROM users WHERE username='{username}' AND password='{hashed_password}'")
    result = db.execute(query).first()

    if result:
        return templates.TemplateResponse("success.html", context={"request": request, "message": "Login successful"})
    else:
        return templates.TemplateResponse("failed.html", status_code=401, context={"request": request, "detail": "Login failed"})
