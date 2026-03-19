"""GitHub API client with rate limiting, token rotation, and disk-based caching."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import httpx
from diskcache import Cache

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RateLimitState:
    remaining: int = 5000
    limit: int = 5000
    reset_at: float = 0.0


@dataclass
class GitHubClient:
    tokens: list[str] = field(default_factory=list)
    _current_token_idx: int = 0
    _rate_limits: dict[int, RateLimitState] = field(default_factory=dict)
    _http: httpx.AsyncClient | None = None
    _cache: Cache | None = None
    _api_calls: int = 0

    def __post_init__(self):
        if not self.tokens:
            self.tokens = settings.github_tokens
        for i in range(len(self.tokens)):
            self._rate_limits[i] = RateLimitState()

    @property
    def api_calls_made(self) -> int:
        return self._api_calls

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(
                base_url="https://api.github.com",
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_connections=10),
            )
        return self._http

    def _get_cache(self) -> Cache:
        if self._cache is None:
            self._cache = Cache(settings.cache_dir, size_limit=500 * 1024 * 1024)  # 500MB
        return self._cache

    def _current_token(self) -> str:
        if not self.tokens:
            return ""
        return self.tokens[self._current_token_idx % len(self.tokens)]

    def _rotate_token(self) -> None:
        if len(self.tokens) > 1:
            self._current_token_idx = (self._current_token_idx + 1) % len(self.tokens)
            logger.info(f"Rotated to token index {self._current_token_idx}")

    def _headers(self) -> dict[str, str]:
        token = self._current_token()
        h = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if token:
            h["Authorization"] = f"Bearer {token}"
        return h

    async def _check_rate_limit(self) -> None:
        state = self._rate_limits.get(self._current_token_idx, RateLimitState())
        if state.remaining < 50 and state.reset_at > time.time():
            # Try rotating to another token
            if len(self.tokens) > 1:
                for i in range(len(self.tokens)):
                    other = self._rate_limits.get(i, RateLimitState())
                    if other.remaining >= 50 or other.reset_at <= time.time():
                        self._current_token_idx = i
                        return
            # All tokens exhausted, wait
            wait_time = state.reset_at - time.time() + 1
            if wait_time > 0:
                logger.warning(f"Rate limited. Waiting {wait_time:.0f}s until reset...")
                import asyncio
                await asyncio.sleep(min(wait_time, 60))

    def _update_rate_limit(self, headers: httpx.Headers) -> None:
        try:
            remaining = int(headers.get("x-ratelimit-remaining", 5000))
            limit = int(headers.get("x-ratelimit-limit", 5000))
            reset_at = float(headers.get("x-ratelimit-reset", 0))
            self._rate_limits[self._current_token_idx] = RateLimitState(
                remaining=remaining, limit=limit, reset_at=reset_at
            )
            if remaining < 100:
                logger.warning(f"GitHub API rate limit low: {remaining}/{limit} remaining")
        except (ValueError, TypeError):
            pass

    def _cache_key(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> str:
        key_data = f"{method}:{path}:{json.dumps(params or {}, sort_keys=True)}:{json.dumps(body or {}, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json_body: dict | None = None,
        cache_ttl: int = 3600,
    ) -> dict[str, Any]:
        """Make a GitHub API request with caching, rate limiting, and retry."""
        cache = self._get_cache()
        cache_k = self._cache_key(method, path, params, json_body)

        # Check cache
        if method.upper() == "GET" and cache_ttl > 0:
            cached = cache.get(cache_k)
            if cached is not None:
                return cached

        await self._check_rate_limit()
        http = await self._get_http()

        last_error = None
        for attempt in range(3):
            try:
                response = await http.request(
                    method,
                    path,
                    params=params,
                    json=json_body,
                    headers=self._headers(),
                )
                self._api_calls += 1
                self._update_rate_limit(response.headers)

                if response.status_code == 403 and "rate limit" in response.text.lower():
                    self._rotate_token()
                    await self._check_rate_limit()
                    continue

                if response.status_code in (502, 503):
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
                    continue

                response.raise_for_status()
                data = response.json()

                # Cache successful GET responses
                if method.upper() == "GET" and cache_ttl > 0:
                    cache.set(cache_k, data, expire=cache_ttl)

                return data

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 404:
                    return {}  # Not found is not an error for us
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)
            except httpx.RequestError as e:
                last_error = e
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        logger.error(f"GitHub API request failed after 3 attempts: {method} {path} - {last_error}")
        return {}

    async def graphql(self, query: str, variables: dict | None = None, *, cache_ttl: int = 3600) -> dict[str, Any]:
        """Execute a GraphQL query against GitHub API v4."""
        body = {"query": query}
        if variables:
            body["variables"] = variables

        cache = self._get_cache()
        cache_k = self._cache_key("GRAPHQL", "/graphql", body=body)

        if cache_ttl > 0:
            cached = cache.get(cache_k)
            if cached is not None:
                return cached

        await self._check_rate_limit()
        http = await self._get_http()

        for attempt in range(3):
            try:
                response = await http.post("/graphql", json=body, headers=self._headers())
                self._api_calls += 1
                self._update_rate_limit(response.headers)

                if response.status_code == 403:
                    self._rotate_token()
                    await self._check_rate_limit()
                    continue

                response.raise_for_status()
                data = response.json()

                if "errors" in data:
                    logger.warning(f"GraphQL errors: {data['errors']}")
                    if any("rate limit" in str(e).lower() for e in data["errors"]):
                        self._rotate_token()
                        await self._check_rate_limit()
                        continue

                if cache_ttl > 0:
                    cache.set(cache_k, data, expire=cache_ttl)

                return data

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                if attempt < 2:
                    import asyncio
                    await asyncio.sleep(2 ** attempt)

        return {}

    # ─── High-level convenience methods ──────────────────────────────

    async def search_users(self, query: str, page: int = 1, per_page: int = 100) -> dict:
        """Search GitHub users."""
        return await self.request(
            "GET", "/search/users",
            params={"q": query, "page": page, "per_page": per_page},
            cache_ttl=1800,
        )

    async def search_repos(self, query: str, page: int = 1, per_page: int = 100) -> dict:
        """Search GitHub repositories."""
        return await self.request(
            "GET", "/search/repositories",
            params={"q": query, "sort": "stars", "order": "desc", "page": page, "per_page": per_page},
            cache_ttl=1800,
        )

    async def get_user(self, login: str) -> dict:
        """Get a user's profile."""
        return await self.request("GET", f"/users/{login}", cache_ttl=86400)

    async def get_user_repos(self, login: str, page: int = 1, per_page: int = 100) -> list:
        """Get a user's public repos."""
        result = await self.request(
            "GET", f"/users/{login}/repos",
            params={"sort": "pushed", "direction": "desc", "page": page, "per_page": per_page},
            cache_ttl=43200,
        )
        return result if isinstance(result, list) else []

    async def get_repo_contributors(self, full_name: str, page: int = 1, per_page: int = 100) -> list:
        """Get contributors for a repo."""
        result = await self.request(
            "GET", f"/repos/{full_name}/contributors",
            params={"page": page, "per_page": per_page},
            cache_ttl=43200,
        )
        return result if isinstance(result, list) else []

    async def get_repo(self, full_name: str) -> dict:
        """Get repo details."""
        return await self.request("GET", f"/repos/{full_name}", cache_ttl=43200)

    async def close(self) -> None:
        if self._http and not self._http.is_closed:
            await self._http.aclose()
        if self._cache:
            self._cache.close()
