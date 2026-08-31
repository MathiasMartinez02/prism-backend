"""Tests del wrapper de GitHub, con httpx mockeado via respx (sin llamar a la API real)."""
import httpx
import pytest
import respx

from app.services.github_client import GitHubClientError, list_pull_requests


@pytest.mark.asyncio
@respx.mock
async def test_list_pull_requests_returns_prs_on_success():
    respx.get("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
        return_value=httpx.Response(200, json=[{"number": 1, "title": "Test PR"}])
    )

    prs = await list_pull_requests("octocat/Hello-World")

    assert len(prs) == 1
    assert prs[0]["number"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_list_pull_requests_raises_404_for_missing_repo():
    respx.get("https://api.github.com/repos/octocat/does-not-exist/pulls").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )

    with pytest.raises(GitHubClientError) as exc_info:
        await list_pull_requests("octocat/does-not-exist")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
@respx.mock
async def test_list_pull_requests_raises_401_for_invalid_token():
    respx.get("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
        return_value=httpx.Response(401, json={"message": "Bad credentials"})
    )

    with pytest.raises(GitHubClientError) as exc_info:
        await list_pull_requests("octocat/Hello-World")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
@respx.mock
async def test_list_pull_requests_raises_429_on_rate_limit():
    respx.get("https://api.github.com/repos/octocat/Hello-World/pulls").mock(
        return_value=httpx.Response(
            403, json={"message": "rate limit"}, headers={"X-RateLimit-Remaining": "0"}
        )
    )

    with pytest.raises(GitHubClientError) as exc_info:
        await list_pull_requests("octocat/Hello-World")

    assert exc_info.value.status_code == 429
