from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# PostgreSQL 연결
DATABASE_URL = "postgresql://postgres:6813@localhost:5432/repotify"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
