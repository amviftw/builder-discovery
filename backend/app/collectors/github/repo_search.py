"""Repo-based discovery strategy - find repos then extract contributors."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from app.collectors.github.client import GitHubClient

logger = logging.getLogger(__name__)

# Repo search queries targeting AI/ML, MCP, and internal tool patterns
AI_REPO_QUERIES = [
    "topic:mcp stars:>3",
    "mcp server language:python stars:>3",
    "mcp server language:typescript stars:>3",
    "model context protocol stars:>2",
    "topic:llm topic:agent language:python stars:>10 created:>2024-01-01",
    "topic:rag language:python stars:>10 created:>2024-01-01",
    "topic:ai-agent stars:>10 created:>2024-01-01",
    "topic:langchain stars:>10 created:>2024-01-01",
    "topic:generative-ai language:python stars:>10 created:>2024-01-01",
]

INTERNAL_TOOL_QUERIES = [
    '"internal tool" language:python stars:>3',
    '"internal tool" language:typescript stars:>3',
    "zomato OR swiggy OR razorpay tool",
    "flipkart OR phonepe OR cred sdk",
    "zerodha OR groww internal",
]


@dataclass
class RepoSearchResult:
    full_name: str
    github_repo_id: int
    description: str | None = None
    stars: int = 0
    language: str | None = None
    topics: list[str] = field(default_factory=list)
    url: str | None = None
    contributors: list[str] = field(default_factory=list)  # GitHub logins


async def search_ai_repos(
    client: GitHubClient,
    queries: list[str] | None = None,
    max_pages_per_query: int = 3,
) -> list[RepoSearchResult]:
    """Search for AI/ML/MCP repos and extract their details."""
    if queries is None:
        queries = AI_REPO_QUERIES

    seen: set[str] = set()
    results: list[RepoSearchResult] = []

    for query in queries:
        logger.info(f"Searching repos: {query}")
        for page in range(1, max_pages_per_query + 1):
            data = await client.search_repos(query, page=page)
            items = data.get("items", [])
            if not items:
                break

            for repo in items:
                full_name = repo.get("full_name", "")
                if full_name and full_name not in seen:
                    seen.add(full_name)
                    results.append(RepoSearchResult(
                        full_name=full_name,
                        github_repo_id=repo.get("id", 0),
                        description=repo.get("description"),
                        stars=repo.get("stargazers_count", 0),
                        language=repo.get("language"),
                        topics=repo.get("topics", []),
                        url=repo.get("html_url"),
                    ))

            if len(items) < 100:
                break

    logger.info(f"Repo search complete: {len(results)} unique repos found")
    return results


async def extract_contributors_from_repos(
    client: GitHubClient,
    repos: list[RepoSearchResult],
    max_contributors_per_repo: int = 50,
) -> dict[str, list[str]]:
    """
    For each repo, fetch contributors and return a mapping of
    repo_full_name -> list of contributor logins.
    Also updates repo objects with contributor logins.
    """
    all_contributors: set[str] = set()
    repo_contributors: dict[str, list[str]] = {}

    for repo in repos:
        logger.info(f"Fetching contributors for {repo.full_name}")
        contributors = await client.get_repo_contributors(repo.full_name)
        if not contributors:
            continue

        logins = []
        for c in contributors[:max_contributors_per_repo]:
            login = c.get("login", "")
            if login and c.get("type") == "User":
                logins.append(login)
                all_contributors.add(login)

        repo.contributors = logins
        repo_contributors[repo.full_name] = logins

    logger.info(f"Extracted {len(all_contributors)} unique contributors from {len(repos)} repos")
    return repo_contributors


async def search_internal_tool_repos(
    client: GitHubClient,
    queries: list[str] | None = None,
    max_pages_per_query: int = 2,
) -> list[RepoSearchResult]:
    """Search specifically for repos that look like internal company tools."""
    if queries is None:
        queries = INTERNAL_TOOL_QUERIES
    return await search_ai_repos(client, queries, max_pages_per_query)
