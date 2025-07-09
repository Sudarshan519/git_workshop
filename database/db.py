from sqlalchemy.orm import sessionmaker 
from sqlalchemy import  create_engine
# === Database Setup ===
DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()