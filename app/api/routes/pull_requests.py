"""Endpoints relacionados a repositorios y sus pull requests."""
import uuid
from collections import Counter

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.api.deps import DbSession
from app.core.config import settings
from app.models.analysis import Analysis
from app.models.pull_request import PullRequest
from app.schemas.analysis import AnalysisOut
from app.schemas.pull_request import LatestAnalysisSummary, PullRequestListItemOut, PullRequestOut
from app.schemas.repository import RepositoryStats
from app.services import repository_service
from app.services.analysis_service import AnalysisError, run_analysis
from app.services.github_client import GitHubClientError

router = APIRouter(tags=["pull-requests"])


# Trae y persiste los PRs de un repo, con el resumen de su ultimo analisis embebido.
@router.get("/repositories/{full_name:path}/pull-requests", response_model=list[PullRequestListItemOut])
async def get_repository_pull_requests(full_name: str, db: DbSession) -> list[PullRequestListItemOut]:
    try:
        pull_requests = await repository_service.sync_pull_requests(db, full_name)
    except GitHubClientError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    latest_by_pr = repository_service.get_latest_analyses(db, pull_requests)

    result = []
    for pr in pull_requests:
        analysis = latest_by_pr.get(pr.id)
        latest_analysis = None
        if analysis is not None:
            latest_analysis = LatestAnalysisSummary(
                id=analysis.id,
                status=analysis.status,
                overall_score=analysis.overall_score,
                findings_count=len(analysis.findings),
                high_severity_count=sum(1 for f in analysis.findings if f.severity == "high"),
                category_counts=dict(Counter(f.category for f in analysis.findings)),
            )
        result.append(
            PullRequestListItemOut(
                id=pr.id,
                github_pr_number=pr.github_pr_number,
                title=pr.title,
                author=pr.author,
                diff_url=pr.diff_url,
                created_at=pr.created_at,
                latest_analysis=latest_analysis,
            )
        )

    return result


# Stats agregadas de un repo ya sincronizado (404 si nunca se sincronizo).
@router.get("/repositories/{full_name:path}/stats", response_model=RepositoryStats)
def get_repository_stats(full_name: str, db: DbSession) -> RepositoryStats:
    repository = repository_service.get_repository_by_full_name(db, full_name)
    if repository is None:
        raise HTTPException(
            status_code=404,
            detail=f"repository '{full_name}' not synced yet - sync it via GET .../pull-requests first",
        )

    total_analyzed, average_score, critical_findings = repository_service.get_repository_stats(
        db, repository
    )
    return RepositoryStats(
        total_analyzed=total_analyzed,
        average_score=average_score,
        critical_findings=critical_findings,
        ai_provider=settings.ai_provider,
    )


# Trae un PR puntual ya sincronizado, para la pantalla de detalle/analisis.
@router.get("/pull-requests/{pull_request_id}", response_model=PullRequestOut)
def get_pull_request(pull_request_id: uuid.UUID, db: DbSession) -> PullRequestOut:
    pull_request = db.get(PullRequest, pull_request_id)
    if pull_request is None:
        raise HTTPException(status_code=404, detail=f"pull request '{pull_request_id}' not found")
    return pull_request


# Dispara el pipeline de analisis de AI sobre un PR (sincronico, sin cola todavia).
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
