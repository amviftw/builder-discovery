"""Discovery service - orchestrates data collection and stores results in DB."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors.github.client import GitHubClient
from app.collectors.github.user_search import search_indian_builders, UserSearchResult
from app.collectors.github.repo_search import (
    search_ai_repos,
    search_internal_tool_repos,
    extract_contributors_from_repos,
)
from app.collectors.github.org_collector import get_org_contributors
from app.collectors.github.profile_enricher import enrich_profile, EnrichedProfile
from app.models.person import Person
from app.models.github_profile import GitHubProfile
from app.models.repository import Repository
from app.models.person_repository import PersonRepository
from app.models.contribution_snapshot import ContributionSnapshot
from app.models.discovery_run import DiscoveryRun

logger = logging.getLogger(__name__)


def _normalize_country(location: str | None) -> str | None:
    """Simple heuristic to detect India from location string."""
    if not location:
        return None
    loc = location.lower()
    india_markers = [
        "india", "bangalore", "bengaluru", "mumbai", "delhi", "hyderabad",
        "pune", "chennai", "gurgaon", "gurugram", "noida", "kolkata",
        "ahmedabad", "jaipur", "kochi", "thiruvananthapuram",
    ]
    for marker in india_markers:
        if marker in loc:
            return "India"
    return None


async def run_user_search_discovery(
    db: AsyncSession,
    client: GitHubClient,
    queries: list[str] | None = None,
    max_pages: int = 3,
) -> DiscoveryRun:
    """Run user search discovery and store results."""
    run = DiscoveryRun(
        run_type="user_search",
        strategy="indian_builders",
        parameters=json.dumps({"max_pages": max_pages}),
        status="running",
    )
    db.add(run)
    await db.flush()

    try:
        results = await search_indian_builders(client, queries=queries, max_pages_per_query=max_pages)
        run.items_found = len(results)

        for user_result in results:
            existing = await db.execute(
                select(GitHubProfile).where(GitHubProfile.login == user_result.login)
            )
            if existing.scalar_one_or_none():
                run.items_skipped += 1
                continue

            # Create person + github profile
            person = Person(
                display_name=user_result.login,
                avatar_url=user_result.avatar_url,
                pipeline_stage="discovered",
            )
            db.add(person)
            await db.flush()

            gh = GitHubProfile(
                person_id=person.id,
                github_id=user_result.github_id,
                login=user_result.login,
                profile_url=user_result.profile_url,
            )
            db.add(gh)
            run.items_new += 1

        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.api_calls_made = client.api_calls_made

    except Exception as e:
        logger.error(f"User search discovery failed: {e}", exc_info=True)
        run.status = "failed"
        run.errors = json.dumps([str(e)])
        run.completed_at = datetime.utcnow()

    return run


async def run_repo_search_discovery(
    db: AsyncSession,
    client: GitHubClient,
    include_internal_tools: bool = True,
) -> DiscoveryRun:
    """Run repo-based discovery: find repos -> extract contributors -> store."""
    run = DiscoveryRun(
        run_type="repo_search",
        strategy="ai_repos_contributors",
        status="running",
    )
    db.add(run)
    await db.flush()

    try:
        # Search AI repos
        repos = await search_ai_repos(client)
        if include_internal_tools:
            internal = await search_internal_tool_repos(client)
            repos.extend(internal)

        # Extract contributors
        repo_contribs = await extract_contributors_from_repos(client, repos)

        # Store repos
        for repo in repos:
            existing = await db.execute(
                select(Repository).where(Repository.github_repo_id == repo.github_repo_id)
            )
            if existing.scalar_one_or_none():
                continue
            db_repo = Repository(
                github_repo_id=repo.github_repo_id,
                owner_login=repo.full_name.split("/")[0],
                name=repo.full_name.split("/")[-1],
                full_name=repo.full_name,
                description=repo.description,
                url=repo.url,
                stars=repo.stars,
                primary_language=repo.language,
                topics=json.dumps(repo.topics),
            )
            db.add(db_repo)

        # Store unique contributors as people
        all_logins: set[str] = set()
        for logins in repo_contribs.values():
            all_logins.update(logins)

        run.items_found = len(all_logins)

        for login in all_logins:
            existing = await db.execute(
                select(GitHubProfile).where(GitHubProfile.login == login)
            )
            if existing.scalar_one_or_none():
                run.items_skipped += 1
                continue

            person = Person(
                display_name=login,
                pipeline_stage="discovered",
            )
            db.add(person)
            await db.flush()

            gh = GitHubProfile(
                person_id=person.id,
                github_id=0,  # Will be populated during enrichment
                login=login,
            )
            db.add(gh)
            run.items_new += 1

        run.status = "completed"
        run.completed_at = datetime.utcnow()
        run.api_calls_made = client.api_calls_made

    except Exception as e:
        logger.error(f"Repo search discovery failed: {e}", exc_info=True)
        run.status = "failed"
        run.errors = json.dumps([str(e)])
        run.completed_at = datetime.utcnow()

    return run


async def enrich_person(
    db: AsyncSession,
    client: GitHubClient,
    person_id: str,
) -> bool:
    """Enrich a single person's profile with full GitHub data."""
    result = await db.execute(select(Person).where(Person.id == person_id))
    person = result.scalar_one_or_none()
    if not person:
        return False

    gh_result = await db.execute(select(GitHubProfile).where(GitHubProfile.person_id == person_id))
    gh = gh_result.scalar_one_or_none()
    if not gh:
        return False

    profile = await enrich_profile(client, gh.login)
    if not profile:
        return False

    # Update person
    person.display_name = profile.name or profile.login
    person.bio = profile.bio
    person.location = profile.location
    person.country = _normalize_country(profile.location)
    person.email = profile.email
    person.avatar_url = profile.avatar_url
    person.website_url = profile.website_url
    person.pipeline_stage = "enriched"
    person.last_enriched_at = datetime.utcnow()

    # Update GitHub profile
    gh.github_id = profile.github_id or gh.github_id
    gh.name = profile.name
    gh.company = profile.company
    gh.bio = profile.bio
    gh.public_repos = profile.public_repos
    gh.followers = profile.followers
    gh.following = profile.following
    gh.hireable = profile.is_hireable
    gh.twitter_username = profile.twitter_username
    gh.total_stars_received = profile.total_stars
    gh.total_forks_received = profile.total_forks
    gh.primary_languages = json.dumps(profile.primary_languages)
    gh.org_memberships = json.dumps(profile.org_memberships)
    gh.created_at_gh = datetime.fromisoformat(profile.created_at_gh.replace("Z", "+00:00")) if profile.created_at_gh else None
    gh.fetched_at = datetime.utcnow()
    gh.profile_url = f"https://github.com/{gh.login}"

    # Store contribution snapshots
    if profile.weekly_contributions:
        from datetime import timedelta

        now = datetime.utcnow()
        for i, count in enumerate(profile.weekly_contributions):
            week_offset = len(profile.weekly_contributions) - 1 - i
            week_start = (now - timedelta(weeks=week_offset)).date()
            # Monday of that week
            week_start = week_start - timedelta(days=week_start.weekday())

            existing_snap = await db.execute(
                select(ContributionSnapshot).where(
                    ContributionSnapshot.person_id == person_id,
                    ContributionSnapshot.week_start == week_start,
                )
            )
            if existing_snap.scalar_one_or_none():
                continue

            snap = ContributionSnapshot(
                person_id=person_id,
                week_start=week_start,
                total_contributions=count,
                commits=None,  # GraphQL calendar doesn't break down by type
            )
            db.add(snap)

    # Store repos
    for repo_data in profile.repos:
        if repo_data.get("is_fork"):
            continue  # Skip forks

        existing_repo = await db.execute(
            select(Repository).where(Repository.github_repo_id == repo_data["github_repo_id"])
        )
        db_repo = existing_repo.scalar_one_or_none()
        if not db_repo:
            db_repo = Repository(
                github_repo_id=repo_data["github_repo_id"],
                owner_login=repo_data["full_name"].split("/")[0],
                name=repo_data["name"],
                full_name=repo_data["full_name"],
            )
            db.add(db_repo)
            await db.flush()

        # Update repo fields
        db_repo.description = repo_data.get("description")
        db_repo.url = repo_data.get("url")
        db_repo.stars = repo_data.get("stars", 0)
        db_repo.forks = repo_data.get("forks", 0)
        db_repo.watchers = repo_data.get("watchers", 0)
        db_repo.primary_language = repo_data.get("primary_language")
        db_repo.languages = json.dumps(repo_data.get("languages", {}))
        db_repo.topics = json.dumps(repo_data.get("topics", []))
        db_repo.size_kb = repo_data.get("size_kb", 0)
        db_repo.is_fork = repo_data.get("is_fork", False)
        db_repo.is_archived = repo_data.get("is_archived", False)
        db_repo.has_readme = repo_data.get("has_readme", False)
        db_repo.readme_length = repo_data.get("readme_length", 0)
        db_repo.has_license = repo_data.get("has_license", False)
        db_repo.has_ci = repo_data.get("has_ci", False)
        db_repo.open_issues = repo_data.get("open_issues", 0)

        if repo_data.get("created_at_gh"):
            try:
                db_repo.created_at_gh = datetime.fromisoformat(repo_data["created_at_gh"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass
        if repo_data.get("pushed_at_gh"):
            try:
                db_repo.pushed_at_gh = datetime.fromisoformat(repo_data["pushed_at_gh"].replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Link person -> repo
        existing_link = await db.execute(
            select(PersonRepository).where(
                PersonRepository.person_id == person_id,
                PersonRepository.repository_id == db_repo.id,
            )
        )
        if not existing_link.scalar_one_or_none():
            link = PersonRepository(
                person_id=person_id,
                repository_id=db_repo.id,
                role="owner",
            )
            db.add(link)

    return True


async def batch_enrich(
    db: AsyncSession,
    client: GitHubClient,
    limit: int = 50,
) -> int:
    """Enrich the next batch of discovered (un-enriched) people."""
    result = await db.execute(
        select(Person)
        .where(Person.pipeline_stage == "discovered")
        .order_by(Person.created_at)
        .limit(limit)
    )
    people = result.scalars().all()

    enriched = 0
    for person in people:
        success = await enrich_person(db, client, person.id)
        if success:
            enriched += 1
            if enriched % 10 == 0:
                await db.commit()
                logger.info(f"Enriched {enriched}/{len(people)} people")

    await db.commit()
    logger.info(f"Batch enrichment complete: {enriched}/{len(people)} enriched")
    return enriched
