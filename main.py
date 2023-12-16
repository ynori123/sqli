from fastapi import FastAPI, Depends
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
import os
from sqlalchemy.orm import sessionmaker
import hashlib

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)
# disable docs
app.redoc_url = None
app.openapi_url = None
app.docs_url = None

templates = Jinja2Templates(directory='templates')

DATABASE_URI = "sqlite:///./sqli.db"
engine = create_engine(
    DATABASE_URI,
    connect_args={"check_same_thread": False}, 
    echo=False
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
    username = Column(String(50), unique=True)
    password = Column(String(50))

@app.on_event("startup")
def startup(db: Session = Depends(session)):
    Base.metadata.create_all(bind=engine)
    plane_password = os.environ["FLAG"]
    target_user = User(username="admin", password=hashlib.sha256(plane_password.encode()).hexdigest())
    db.add(target_user)
    db.commit()

@app.post("/login")
async def login(username: str, password: str, db: Session = Depends(session)):
    if db.query(User).filter(User.username == username, User.password == hashlib.sha256(password.encode()).hexdigest()).first():
        return templates.TemplateResponse(
            name="success.html",
            status_code=200
        )
    else: 
        return templates.TemplateResponse(
            name="failed.html",
            status_code=400
        )
