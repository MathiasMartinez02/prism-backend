"""Logica de sincronizacion: trae un repo + sus PRs de GitHub y los persiste de forma idempotente."""
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.analysis import Analysis
from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.services import github_client


# Upsert de un repositorio por github_repo_id.
def _upsert_repository(db: Session, repo_data: dict) -> Repository:
    github_repo_id = repo_data["id"]
    repository = db.scalar(select(Repository).where(Repository.github_repo_id == github_repo_id))
    if repository is None:
        repository = Repository(github_repo_id=github_repo_id, full_name=repo_data["full_name"])
        db.add(repository)
    else:
        repository.full_name = repo_data["full_name"]
    db.flush()  # asegura repository.id antes de usarlo en los PRs
    return repository


# Upsert de un PR por (repository_id, github_pr_number).
def _upsert_pull_request(db: Session, repository: Repository, pr_data: dict) -> PullRequest:
    pull_request = db.scalar(
        select(PullRequest).where(
            PullRequest.repository_id == repository.id,
            PullRequest.github_pr_number == pr_data["number"],
        )
    )
    author = pr_data["user"]["login"] if pr_data.get("user") else None
    if pull_request is None:
        pull_request = PullRequest(
            repository_id=repository.id,
            github_pr_number=pr_data["number"],
            title=pr_data["title"],
            author=author,
            diff_url=pr_data.get("diff_url"),
        )
        db.add(pull_request)
    else:
        pull_request.title = pr_data["title"]
        pull_request.author = author
        pull_request.diff_url = pr_data.get("diff_url")
    return pull_request


# Trae el repo + sus PRs de GitHub y los persiste (idempotente).
async def sync_pull_requests(db: Session, full_name: str) -> list[PullRequest]:
    repo_data = await github_client.get_repository(full_name)
    repository = _upsert_repository(db, repo_data)

    prs_data = await github_client.list_pull_requests(full_name)
    for pr_data in prs_data:
        _upsert_pull_request(db, repository, pr_data)

    db.commit()

    return list(
        db.scalars(
            select(PullRequest)
            .where(PullRequest.repository_id == repository.id)
            .order_by(PullRequest.github_pr_number.desc())
        )
    )


# Trae el ultimo analisis de cada PR, en una sola query (sin N+1).
def get_latest_analyses(db: Session, pull_requests: list[PullRequest]) -> dict[uuid.UUID, Analysis]:
    if not pull_requests:
        return {}

    pull_request_ids = [pr.id for pr in pull_requests]
    all_analyses = db.scalars(
        select(Analysis)
        .options(selectinload(Analysis.findings))
        .where(Analysis.pull_request_id.in_(pull_request_ids))
        .order_by(Analysis.started_at.desc().nullslast())
    )

    latest_by_pr: dict[uuid.UUID, Analysis] = {}
    for analysis in all_analyses:
        # El primero por PR es el mas reciente (ya viene ordenado desc).
        latest_by_pr.setdefault(analysis.pull_request_id, analysis)

    return latest_by_pr


# Repositorio ya sincronizado por full_name, o None.
def get_repository_by_full_name(db: Session, full_name: str) -> Repository | None:
    return db.scalar(select(Repository).where(Repository.full_name == full_name))


# Stats agregadas para las stat cards del dashboard.
def get_repository_stats(db: Session, repository: Repository) -> tuple[int, float | None, int]:
    pull_requests = list(
        db.scalars(select(PullRequest).where(PullRequest.repository_id == repository.id))
    )
    latest_by_pr = get_latest_analyses(db, pull_requests)

    completed = [a for a in latest_by_pr.values() if a.status == "completed"]
    total_analyzed = len(completed)
    average_score = (
        round(sum(a.overall_score or 0 for a in completed) / total_analyzed, 1)
        if total_analyzed > 0
        else None
    )
    critical_findings = sum(
        1 for a in completed for finding in a.findings if finding.severity == "high"
    )

    return total_analyzed, average_score, critical_findings
