"""Logica de sincronizacion: trae un repo + sus PRs de GitHub y los persiste de forma idempotente."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.pull_request import PullRequest
from app.models.repository import Repository
from app.services import github_client


# Upsert de un repositorio por github_repo_id (nunca duplica si ya existe).
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


# Upsert de un PR por (repository_id, github_pr_number) — la unique constraint de la tabla
# es la que realmente garantiza que nunca se duplique aunque se llame dos veces seguidas.
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


# Trae el repo + sus PRs abiertos de GitHub y los persiste. Llamar dos veces con el mismo
# full_name no duplica filas: actualiza las existentes por su clave natural.
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
