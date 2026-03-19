"""User search discovery strategy - find builders via GitHub user search API."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.collectors.github.client import GitHubClient

logger = logging.getLogger(__name__)

# Narrow queries to work around GitHub's 1000 result cap per query
INDIAN_BUILDER_QUERIES = [
    # Python builders by city
    "location:india language:python followers:>50 repos:>10",
    "location:india language:python followers:>20 repos:>20",
    "location:bangalore language:python followers:>30",
    "location:bengaluru language:python followers:>30",
    "location:mumbai language:python followers:>30",
    "location:delhi language:python followers:>30",
    "location:hyderabad language:python followers:>30",
    "location:pune language:python followers:>20",
    "location:chennai language:python followers:>20",
    "location:gurgaon language:python followers:>20",
    "location:gurugram language:python followers:>20",
    "location:noida language:python followers:>20",
    # TypeScript/JS builders
    "location:india language:typescript followers:>50 repos:>10",
    "location:india language:javascript followers:>100 repos:>15",
    "location:bangalore language:typescript followers:>30",
    # Rust/Go builders (systems-minded)
    "location:india language:rust followers:>20",
    "location:india language:go followers:>30 repos:>10",
]


@dataclass
class UserSearchResult:
    login: str
    github_id: int
    avatar_url: str | None = None
    profile_url: str | None = None
    score: float = 0.0  # GitHub's search relevance score


async def search_indian_builders(
    client: GitHubClient,
    queries: list[str] | None = None,
    max_pages_per_query: int = 5,
) -> list[UserSearchResult]:
    """
    Execute multiple narrow user search queries to discover Indian builders.
    Returns deduplicated list of discovered users.
    """
    if queries is None:
        queries = INDIAN_BUILDER_QUERIES

    seen_logins: set[str] = set()
    results: list[UserSearchResult] = []

    for query in queries:
        logger.info(f"Searching users: {query}")
        for page in range(1, max_pages_per_query + 1):
            data = await client.search_users(query, page=page)
            items = data.get("items", [])

            if not items:
                break

            for user in items:
                login = user.get("login", "")
                if login and login not in seen_logins:
                    seen_logins.add(login)
                    results.append(UserSearchResult(
                        login=login,
                        github_id=user.get("id", 0),
                        avatar_url=user.get("avatar_url"),
                        profile_url=user.get("html_url"),
                        score=user.get("score", 0.0),
                    ))

            # If fewer results than requested, no more pages
            if len(items) < 100:
                break

        logger.info(f"  Found {len(results)} unique users so far")

    logger.info(f"User search complete: {len(results)} unique builders found across {len(queries)} queries")
    return results


async def search_users_by_query(
    client: GitHubClient,
    query: str,
    max_pages: int = 10,
) -> list[UserSearchResult]:
    """Search users with a single custom query."""
    seen: set[str] = set()
    results: list[UserSearchResult] = []

    for page in range(1, max_pages + 1):
        data = await client.search_users(query, page=page)
        items = data.get("items", [])
        if not items:
            break
        for user in items:
            login = user.get("login", "")
            if login and login not in seen:
                seen.add(login)
                results.append(UserSearchResult(
                    login=login,
                    github_id=user.get("id", 0),
                    avatar_url=user.get("avatar_url"),
                    profile_url=user.get("html_url"),
                    score=user.get("score", 0.0),
                ))
        if len(items) < 100:
            break

    return results
