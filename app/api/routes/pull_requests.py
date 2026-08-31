"""Endpoints relacionados a repositorios y sus pull requests."""
from fastapi import APIRouter, HTTPException

from app.api.deps import DbSession
from app.schemas.pull_request import PullRequestOut
from app.services import repository_service
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
