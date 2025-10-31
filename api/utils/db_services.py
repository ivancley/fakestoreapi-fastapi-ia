from decouple import config
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = config("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,            
    max_overflow=40,
    pool_timeout=360,
    pool_recycle=3600,
    pool_pre_ping=True,
    connect_args={"options": "-c timezone=America/Sao_Paulo"}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
