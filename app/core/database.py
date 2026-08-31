"""Engine y sessionmaker de SQLAlchemy, mas la dependencia de FastAPI para inyectar sesiones de DB."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base declarativa de la que heredan todos los modelos SQLAlchemy del proyecto.
class Base(DeclarativeBase):
    pass


# Dependencia inyectable: entrega una sesion de DB por request y la cierra siempre al final.
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
