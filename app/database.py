# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings
from app.models import Base

engine = create_engine(settings.DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """Provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

