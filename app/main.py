"""Punto de entrada de la app FastAPI."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette import status

from app.api.deps import DbSession
from app.api.routes.pull_requests import router as pull_requests_router
from app.core.config import settings

app = FastAPI(title="PRISM API", version="0.1.0")

# El frontend (Next.js) llama a este backend directo desde el browser, asi que necesita CORS habilitado.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pull_requests_router)


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
