"""Endpoints relacionados a repositorios y sus pull requests."""
import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.analysis import Analysis
from app.models.pull_request import PullRequest
from app.schemas.analysis import AnalysisOut
from app.schemas.pull_request import PullRequestOut
from app.services import repository_service
from app.services.analysis_service import AnalysisError, run_analysis
from app.services.github_client import GitHubClientError

router = APIRouter(tags=["pull-requests"])


# Trae (y persiste) los PRs abiertos de un repo publico de GitHub. Idempotente: llamarlo
# de nuevo con el mismo repo actualiza las filas existentes en vez de duplicarlas.
@router.get("/repositories/{full_name:path}/pull-requests", response_model=list[PullRequestOut])
async def get_repository_pull_requests(full_name: str, db: DbSession) -> list[PullRequestOut]:
    try:
        pull_requests = await repository_service.sync_pull_requests(db, full_name)
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return pull_requests


# Trae un PR puntual ya sincronizado, para la pantalla de detalle/analisis.
@router.get("/pull-requests/{pull_request_id}", response_model=PullRequestOut)
def get_pull_request(pull_request_id: uuid.UUID, db: DbSession) -> PullRequestOut:
    pull_request = db.get(PullRequest, pull_request_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail=f"pull request '{pull_request_id}' not found")
    return pull_request


# Dispara el pipeline de analisis de AI sobre un PR ya sincronizado. Sincronico (el usuario
# espera unos segundos): en produccion esto seria un background job con cola, pero para el
# MVP evitamos la complejidad de una cola solo para poder mostrar el trade-off en el README.
@router.post("/pull-requests/{pull_request_id}/analyze", response_model=AnalysisOut, status_code=201)
async def analyze_pull_request(pull_request_id: uuid.UUID, db: DbSession) -> AnalysisOut:
    pull_request = db.get(PullRequest, pull_request_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail=f"pull request '{pull_request_id}' not found")

    try:
        analysis = await run_analysis(db, pull_request)
    except AnalysisError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    except ValueError as exc:
        # get_ai_provider() tira ValueError si falta configurar el provider (ej. sin API key).
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return analysis


# Historial de analisis corridos sobre un PR, mas recientes primero.
@router.get("/pull-requests/{pull_request_id}/analyses", response_model=list[AnalysisOut])
def list_analyses(pull_request_id: uuid.UUID, db: DbSession) -> list[AnalysisOut]:
    if db.get(PullRequest, pull_request_id) is None:
        raise HTTPException(status_code=404, detail=f"pull request '{pull_request_id}' not found")

    return list(
        db.scalars(
            select(Analysis)
            .where(Analysis.pull_request_id == pull_request_id)
            .order_by(Analysis.started_at.desc())
        )
    )
