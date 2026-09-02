"""Wrapper delgado sobre la REST API de GitHub para listar PRs de un repo."""
import httpx

from app.core.config import settings

GITHUB_API_BASE = "https://api.github.com"


# Error de GitHub identificado (repo inexistente, token invalido, rate limit).
class GitHubClientError(Exception):
    def __init__(self, message: str, status_code: int):
        super().__init__(message)
        self.status_code = status_code


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    # GITHUB_TOKEN sale de env var; sin token funciona igual con menos rate limit.
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


# Trae los metadatos del repo (incluye github_repo_id).
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


# Trae el diff crudo de un PR desde su diff_url.
async def get_diff(diff_url: str) -> str:
    # GitHub redirige *.diff (302), hay que seguir el redirect.
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        response = await client.get(diff_url, headers=_headers())

    if response.status_code == 404:
        raise GitHubClientError(f"diff not found at '{diff_url}'", status_code=404)
    if response.status_code == 401:
        raise GitHubClientError("invalid GITHUB_TOKEN", status_code=401)
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        raise GitHubClientError("GitHub rate limit exceeded, try again later", status_code=429)
    response.raise_for_status()

    return response.text


# Trae los PRs abiertos de un repo publico.
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
