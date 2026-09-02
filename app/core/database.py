"""Engine y sessionmaker de SQLAlchemy, mas la dependencia de FastAPI para inyectar sesiones de DB."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base declarativa para los modelos SQLAlchemy.
class Base(DeclarativeBase):
    pass


# Entrega una sesion de DB por request y la cierra al final.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
