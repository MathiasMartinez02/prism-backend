"""Punto de entrada de la app FastAPI."""
from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from starlette import status

from app.api.deps import DbSession

app = FastAPI(title="PRISM API", version="0.1.0")


# Endpoint raiz minimo, solo para confirmar que el servidor levanta correctamente.
@app.get("/")
def root() -> dict[str, str]:
    return {"service": "prism-backend", "status": "ok"}


# Health check real: ademas de que el proceso responda, confirma que Postgres esta accesible.
@app.get("/health")
def health(db: DbSession) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database unavailable: {exc}",
        ) from exc
    return {"status": "ok", "database": "up"}
