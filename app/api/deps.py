"""Dependencias inyectables compartidas por los endpoints (sesion de DB, auth a futuro)."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

# Alias tipado para inyectar la sesion de DB en cualquier endpoint sin repetir el Depends.
DbSession = Annotated[Session, Depends(get_db)]
