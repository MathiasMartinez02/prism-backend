"""Wrapper delgado sobre la REST API de GitHub para listar PRs de un repo."""
import httpx

from app.core.config import settings

GITHUB_API_BASE = "https://api.github.com"


# Se levanta cuando GitHub devuelve un error identificable (repo no existe, token invalido, rate limit).
class GitHubClientError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # GITHUB_TOKEN sale siempre de env var (nunca hardcodeado); sin token igual funciona
    # para repos publicos, con un limite de rate mas bajo.
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


# Trae los metadatos del repo (incluye el github_repo_id que necesitamos para el upsert).
async def get_repository(full_name: str) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{full_name}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=_headers())

    if response.status_code == 404:
        raise GitHubClientError(f"repository '{full_name}' not found on GitHub", status_code=404)
    if response.status_code == 401:
        raise GitHubClientError("invalid GITHUB_TOKEN", status_code=401)
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        raise GitHubClientError("GitHub rate limit exceeded, try again later", status_code=429)
    response.raise_for_status()

    return response.json()


# Trae los PRs abiertos de un repo publico ("owner/repo") usando la REST API de GitHub.
async def list_pull_requests(full_name: str, state: str = "open") -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{full_name}/pulls"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=_headers(), params={"state": state, "per_page": 30})

    if response.status_code == 404:
        raise GitHubClientError(f"repository '{full_name}' not found on GitHub", status_code=404)
    if response.status_code == 401:
        raise GitHubClientError("invalid GITHUB_TOKEN", status_code=401)
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        raise GitHubClientError("GitHub rate limit exceeded, try again later", status_code=429)
    response.raise_for_status()

    return response.json()
