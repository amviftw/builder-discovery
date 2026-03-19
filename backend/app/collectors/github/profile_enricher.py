"""Profile enricher - pulls full GitHub profile + contribution history via GraphQL."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.collectors.github.client import GitHubClient
from app.collectors.github.graphql_queries import (
    CONTRIBUTION_CALENDAR_QUERY,
    USER_PROFILE_QUERY,
    USER_REPOS_QUERY,
)

logger = logging.getLogger(__name__)


@dataclass
class EnrichedProfile:
    """Full enriched data for a single GitHub user."""

    login: str
    github_id: int = 0
    name: str | None = None
    bio: str | None = None
    company: str | None = None
    location: str | None = None
    email: str | None = None
    website_url: str | None = None
    avatar_url: str | None = None
    is_hireable: bool = False
    twitter_username: str | None = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    created_at_gh: str | None = None
    updated_at_gh: str | None = None
    org_memberships: list[str] = field(default_factory=list)
    org_count: int = 0

    # Derived
    total_stars: int = 0
    total_forks: int = 0
    primary_languages: list[str] = field(default_factory=list)

    # Contribution data (52 weeks)
    weekly_contributions: list[int] = field(default_factory=list)
    total_commits_year: int = 0
    total_prs_year: int = 0
    total_issues_year: int = 0
    total_reviews_year: int = 0
    repos_contributed_to: int = 0

    # Repos
    repos: list[dict] = field(default_factory=list)


def _has_scope_errors(data: dict) -> bool:
    """Check if GraphQL response contains INSUFFICIENT_SCOPES errors."""
    errors = data.get("errors", [])
    return any(
        e.get("type") == "INSUFFICIENT_SCOPES" or "scopes" in str(e.get("message", "")).lower()
        for e in errors
    )


async def enrich_profile(client: GitHubClient, login: str) -> EnrichedProfile | None:
    """
    Pull complete profile data for a user via GraphQL.
    Returns EnrichedProfile or None if user genuinely not found.
    """
    profile = EnrichedProfile(login=login)

    # 1. User profile
    data = await client.graphql(USER_PROFILE_QUERY, {"login": login}, cache_ttl=86400)

    # Check for scope errors — log but don't treat as "not found"
    if _has_scope_errors(data):
        logger.debug(f"Scope warnings for {login} (non-fatal, continuing with available data)")

    user = (data.get("data") or {}).get("user")
    if not user:
        # Only treat as not-found if there are NO scope errors
        # (scope errors can cause user to be null even though user exists)
        if _has_scope_errors(data):
            logger.warning(f"User {login}: scope errors prevented data fetch, trying REST fallback")
            # Fallback: use REST API which works with public_repo scope
            rest_user = await client.get_user(login)
            if rest_user:
                profile.github_id = rest_user.get("id", 0)
                profile.name = rest_user.get("name")
                profile.bio = rest_user.get("bio")
                profile.company = rest_user.get("company")
                profile.location = rest_user.get("location")
                profile.email = rest_user.get("email")
                profile.website_url = rest_user.get("blog")
                profile.avatar_url = rest_user.get("avatar_url")
                profile.is_hireable = rest_user.get("hireable", False) or False
                profile.twitter_username = rest_user.get("twitter_username")
                profile.followers = rest_user.get("followers", 0)
                profile.following = rest_user.get("following", 0)
                profile.public_repos = rest_user.get("public_repos", 0)
                profile.created_at_gh = rest_user.get("created_at")
                profile.updated_at_gh = rest_user.get("updated_at")
            else:
                logger.warning(f"User not found: {login}")
                return None
        else:
            logger.warning(f"User not found: {login}")
            return None
    else:
        profile.github_id = user.get("databaseId", 0)
        profile.name = user.get("name")
        profile.bio = user.get("bio")
        profile.company = user.get("company")
        profile.location = user.get("location")
        # email removed from query (needs read:user scope)
        profile.website_url = user.get("websiteUrl")
        profile.avatar_url = user.get("avatarUrl")
        profile.is_hireable = user.get("isHireable", False)
        profile.twitter_username = user.get("twitterUsername")
        profile.followers = (user.get("followers") or {}).get("totalCount", 0)
        profile.following = (user.get("following") or {}).get("totalCount", 0)
        profile.public_repos = (user.get("repositories") or {}).get("totalCount", 0)
        profile.created_at_gh = user.get("createdAt")
        profile.updated_at_gh = user.get("updatedAt")
        # org count (names need read:org scope, so we just get the count)
        profile.org_count = (user.get("organizations") or {}).get("totalCount", 0)

    # 2. Contribution calendar (last 52 weeks)
    now = datetime.utcnow()
    year_ago = now - timedelta(days=364)
    contrib_data = await client.graphql(
        CONTRIBUTION_CALENDAR_QUERY,
        {
            "login": login,
            "from": year_ago.strftime("%Y-%m-%dT00:00:00Z"),
            "to": now.strftime("%Y-%m-%dT23:59:59Z"),
        },
        cache_ttl=43200,
    )
    collection = ((contrib_data.get("data") or {}).get("user") or {}).get("contributionsCollection", {})

    profile.total_commits_year = collection.get("totalCommitContributions", 0)
    profile.total_prs_year = collection.get("totalPullRequestContributions", 0)
    profile.total_issues_year = collection.get("totalIssueContributions", 0)
    profile.total_reviews_year = collection.get("totalPullRequestReviewContributions", 0)
    profile.repos_contributed_to = collection.get("totalRepositoriesWithContributedCommits", 0)

    # Parse weekly contributions
    calendar = collection.get("contributionCalendar", {})
    weeks = calendar.get("weeks", [])
    weekly = []
    for week in weeks:
        days = week.get("contributionDays", [])
        week_total = sum(d.get("contributionCount", 0) for d in days)
        weekly.append(week_total)
    profile.weekly_contributions = weekly

    # 3. Top repos (by stars)
    repos_data = await client.graphql(
        USER_REPOS_QUERY,
        {"login": login, "first": 50, "after": None},
        cache_ttl=43200,
    )
    repos_user = ((repos_data.get("data") or {}).get("user") or {}).get("repositories", {})
    repo_nodes = repos_user.get("nodes", [])

    total_stars = 0
    total_forks = 0
    languages: dict[str, int] = {}
    repos_list = []

    for r in repo_nodes:
        if not r:
            continue
        stars = r.get("stargazerCount", 0)
        forks = r.get("forkCount", 0)
        total_stars += stars
        total_forks += forks

        # Count languages
        lang_edges = (r.get("languages") or {}).get("edges", [])
        for edge in lang_edges:
            lang_name = (edge.get("node") or {}).get("name", "")
            lang_size = edge.get("size", 0)
            if lang_name:
                languages[lang_name] = languages.get(lang_name, 0) + lang_size

        topics = [
            (n.get("topic") or {}).get("name", "")
            for n in (r.get("repositoryTopics") or {}).get("nodes", [])
        ]

        primary_lang = (r.get("primaryLanguage") or {}).get("name")

        readme_obj = r.get("object")
        readme_size = readme_obj.get("byteSize", 0) if readme_obj and isinstance(readme_obj, dict) else 0

        ci_obj = r.get("object2")
        has_ci = bool(ci_obj and isinstance(ci_obj, dict) and ci_obj.get("entries"))

        license_info = r.get("licenseInfo")
        has_license = bool(license_info and license_info.get("spdxId") not in (None, "NOASSERTION"))

        repos_list.append({
            "github_repo_id": r.get("databaseId", 0),
            "name": r.get("name", ""),
            "full_name": r.get("nameWithOwner", ""),
            "description": r.get("description"),
            "url": r.get("url"),
            "stars": stars,
            "forks": forks,
            "watchers": (r.get("watchers") or {}).get("totalCount", 0),
            "primary_language": primary_lang,
            "languages": {
                (e.get("node") or {}).get("name", ""): e.get("size", 0)
                for e in lang_edges
            },
            "topics": [t for t in topics if t],
            "created_at_gh": r.get("createdAt"),
            "pushed_at_gh": r.get("pushedAt"),
            "updated_at_gh": r.get("updatedAt"),
            "is_fork": r.get("isFork", False),
            "is_archived": r.get("isArchived", False),
            "size_kb": r.get("diskUsage", 0),
            "open_issues": (r.get("openIssues") or {}).get("totalCount", 0),
            "has_readme": readme_size > 0,
            "readme_length": readme_size,
            "has_license": has_license,
            "has_ci": has_ci,
        })

    profile.total_stars = total_stars
    profile.total_forks = total_forks
    profile.repos = repos_list

    # Top languages by total code size
    sorted_langs = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    profile.primary_languages = [lang for lang, _ in sorted_langs[:5]]

    return profile
