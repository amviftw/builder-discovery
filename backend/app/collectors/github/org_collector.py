"""Org-based discovery - monitor company GitHub orgs for contributors."""

from __future__ import annotations

import logging

from app.collectors.github.client import GitHubClient

logger = logging.getLogger(__name__)


async def get_org_repos(client: GitHubClient, org_login: str, max_pages: int = 5) -> list[dict]:
    """Get all public repos for an organization."""
    repos = []
    for page in range(1, max_pages + 1):
        data = await client.request(
            "GET", f"/orgs/{org_login}/repos",
            params={"type": "public", "sort": "pushed", "per_page": 100, "page": page},
            cache_ttl=43200,
        )
        if not data or not isinstance(data, list):
            break
        repos.extend(data)
        if len(data) < 100:
            break

    logger.info(f"Found {len(repos)} public repos for org: {org_login}")
    return repos


async def get_org_contributors(
    client: GitHubClient,
    org_login: str,
    max_repos: int = 20,
    max_contributors_per_repo: int = 30,
) -> list[str]:
    """
    Get unique contributors across an org's top repos.
    Returns list of GitHub logins.
    """
    repos = await get_org_repos(client, org_login)
    # Focus on most recently pushed repos
    repos = repos[:max_repos]

    all_contributors: set[str] = set()
    for repo in repos:
        full_name = repo.get("full_name", "")
        if not full_name:
            continue

        contributors = await client.get_repo_contributors(full_name)
        if not contributors:
            continue

        for c in contributors[:max_contributors_per_repo]:
            login = c.get("login", "")
            if login and c.get("type") == "User":
                all_contributors.add(login)

    logger.info(f"Found {len(all_contributors)} unique contributors for org: {org_login}")
    return list(all_contributors)


async def get_org_info(client: GitHubClient, org_login: str) -> dict:
    """Get organization profile info."""
    return await client.request("GET", f"/orgs/{org_login}", cache_ttl=86400)
