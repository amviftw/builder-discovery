"""Scoring service - runs all processors on enriched profiles and stores results."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.models.github_profile import GitHubProfile
from app.models.repository import Repository
from app.models.person_repository import PersonRepository
from app.models.contribution_snapshot import ContributionSnapshot
from app.models.signal import Signal
from app.processors.activity_analyzer import analyze_activity
from app.processors.repo_quality_scorer import score_repo_quality
from app.processors.internal_tool_detector import score_internal_tool
from app.processors.score_compositor import (
    compute_technical_score,
    compute_momentum_score,
    compute_ai_nativeness_score,
    compute_leadership_score,
    compute_departure_signal_score,
    compute_composite_score,
)
from app.llm.client import classify_builder, classify_ai_relevance

logger = logging.getLogger(__name__)


async def score_person(db: AsyncSession, person_id: str) -> bool:
    """Run full scoring pipeline for a single person."""

    # Load person + github profile
    person_result = await db.execute(select(Person).where(Person.id == person_id))
    person = person_result.scalar_one_or_none()
    if not person:
        return False

    gh_result = await db.execute(select(GitHubProfile).where(GitHubProfile.person_id == person_id))
    gh = gh_result.scalar_one_or_none()
    if not gh:
        return False

    # Load contribution snapshots (sorted by week)
    snap_result = await db.execute(
        select(ContributionSnapshot)
        .where(ContributionSnapshot.person_id == person_id)
        .order_by(ContributionSnapshot.week_start.asc())
    )
    snapshots = snap_result.scalars().all()
    weekly_contributions = [s.total_contributions or 0 for s in snapshots]

    # Load repos
    repo_links = await db.execute(
        select(PersonRepository).where(PersonRepository.person_id == person_id)
    )
    repo_ids = [r.repository_id for r in repo_links.scalars().all()]

    repos = []
    if repo_ids:
        repos_result = await db.execute(select(Repository).where(Repository.id.in_(repo_ids)))
        repos = repos_result.scalars().all()

    # ─── 1. Activity analysis → signals ──────────────────────────────
    activity_signals = analyze_activity(weekly_contributions)
    for sig in activity_signals:
        # Check if similar signal already exists
        existing = await db.execute(
            select(Signal).where(
                Signal.person_id == person_id,
                Signal.signal_type == sig.signal_type,
                Signal.is_active == True,  # noqa: E712
            )
        )
        if not existing.scalar_one_or_none():
            db_signal = Signal(
                person_id=person_id,
                signal_type=sig.signal_type,
                signal_strength=sig.signal_strength,
                evidence=json.dumps(sig.evidence),
                description=sig.description,
            )
            db.add(db_signal)

    # Check hireable flag
    if gh.hireable:
        existing_hireable = await db.execute(
            select(Signal).where(
                Signal.person_id == person_id,
                Signal.signal_type == "hireable_flag_on",
                Signal.is_active == True,  # noqa: E712
            )
        )
        if not existing_hireable.scalar_one_or_none():
            db.add(Signal(
                person_id=person_id,
                signal_type="hireable_flag_on",
                signal_strength=0.7,
                evidence=json.dumps({"hireable": True}),
                description="GitHub profile marked as hireable",
            ))

    # ─── 2. Repo quality scoring ─────────────────────────────────────
    repo_quality_scores = []
    repo_ai_scores = []
    has_mcp = False
    now = datetime.utcnow()

    for repo in repos:
        if repo.is_fork or repo.is_archived:
            continue

        days_since_push = (now - repo.pushed_at_gh).days if repo.pushed_at_gh else 365
        topics = json.loads(repo.topics) if repo.topics else []
        topics_count = len(topics)

        quality = score_repo_quality(
            stars=repo.stars or 0,
            forks=repo.forks or 0,
            watchers=repo.watchers or 0,
            has_readme=repo.has_readme or False,
            readme_length=repo.readme_length or 0,
            has_license=repo.has_license or False,
            has_ci=repo.has_ci or False,
            topics_count=topics_count,
            days_since_push=days_since_push,
        )
        repo.quality_score = quality
        repo_quality_scores.append(quality)

        # Internal tool detection
        itool_score, itool_evidence = score_internal_tool(
            repo_name=repo.name,
            description=repo.description,
            contributor_count=repo.contributor_count or 1,
            size_kb=repo.size_kb or 0,
            stars=repo.stars or 0,
        )
        if itool_score > 0.3:
            repo.is_internal_tool = True
            repo.internal_tool_confidence = itool_score

            # Create signal for internal tool
            existing_it = await db.execute(
                select(Signal).where(
                    Signal.person_id == person_id,
                    Signal.signal_type == "internal_tool_shipped",
                )
            )
            if not existing_it.scalar_one_or_none():
                db.add(Signal(
                    person_id=person_id,
                    signal_type="internal_tool_shipped",
                    signal_strength=itool_score,
                    evidence=json.dumps({**itool_evidence, "repo": repo.full_name}),
                    description=f"Likely internal tool: {repo.full_name}",
                ))

        # AI relevance (heuristic - LLM classification is expensive, done separately)
        ai_score = _heuristic_ai_score(repo.name, repo.description, topics)
        repo.ai_relevance_score = ai_score

        created_recently = False
        if repo.created_at_gh:
            created_recently = (now - repo.created_at_gh).days < 180

        repo_ai_scores.append((ai_score, created_recently))

        # MCP detection
        name_lower = repo.name.lower()
        if "mcp" in name_lower or "mcp" in topics or "model-context-protocol" in topics:
            has_mcp = True

    # ─── 3. Compute dimension scores ─────────────────────────────────
    primary_languages = json.loads(gh.primary_languages) if gh.primary_languages else []

    technical = compute_technical_score(
        repo_quality_scores=repo_quality_scores,
        total_stars=gh.total_stars_received or 0,
        language_count=len(primary_languages),
        contribution_volume_52w=sum(weekly_contributions),
        has_popular_repo=any(r.stars and r.stars > 50 for r in repos),
    )

    # Count repos created in last 90 days
    repos_last_90d = sum(
        1 for r in repos
        if r.created_at_gh and (now - r.created_at_gh).days < 90 and not r.is_fork
    )

    momentum = compute_momentum_score(
        weekly_contributions=weekly_contributions,
        repos_created_last_90d=repos_last_90d,
    )

    ai_nativeness = compute_ai_nativeness_score(
        repo_ai_scores=repo_ai_scores,
        has_mcp_repo=has_mcp,
        total_repos=len(repos),
    )

    follower_ratio = (gh.followers / max(gh.following, 1)) if gh.followers and gh.following else 0
    avg_doc = (
        sum(r.quality_score or 0 for r in repos if not r.is_fork) / max(1, len([r for r in repos if not r.is_fork]))
    )

    leadership = compute_leadership_score(
        owned_repos_count=gh.public_repos or 0,
        avg_doc_quality=avg_doc,
        follower_ratio=follower_ratio,
        org_count=len(json.loads(gh.org_memberships)) if gh.org_memberships else 0,
        has_website=bool(person.website_url),
    )

    # Gather active signals for departure score
    sig_result = await db.execute(
        select(Signal).where(Signal.person_id == person_id, Signal.is_active == True)  # noqa: E712
    )
    active_signals = sig_result.scalars().all()
    signal_pairs = [(s.signal_type, s.signal_strength or 0) for s in active_signals]

    departure = compute_departure_signal_score(signal_pairs)

    # ─── 4. Composite score ──────────────────────────────────────────
    composite = compute_composite_score(technical, momentum, ai_nativeness, leadership, departure)

    person.technical_score = composite.technical_score
    person.momentum_score = composite.momentum_score
    person.ai_nativeness_score = composite.ai_nativeness_score
    person.leadership_score = composite.leadership_score
    person.departure_signal_score = composite.departure_signal_score
    person.founder_propensity_score = composite.founder_propensity_score
    person.pipeline_stage = "scored"
    person.last_scored_at = datetime.utcnow()

    return True


def _heuristic_ai_score(name: str, description: str | None, topics: list[str]) -> float:
    """Quick heuristic AI relevance scoring without LLM."""
    HIGH_SIGNAL = {
        "llm", "ai-agent", "ai-agents", "langchain", "rag", "mcp",
        "model-context-protocol", "mcp-server", "openai", "anthropic",
        "generative-ai", "gen-ai", "transformer", "diffusion",
        "large-language-model", "gpt", "claude", "gemini",
        "vector-database", "embedding", "fine-tuning", "autonomous-agent",
    }
    MEDIUM_SIGNAL = {
        "machine-learning", "deep-learning", "neural-network",
        "computer-vision", "nlp", "natural-language-processing",
        "tensorflow", "pytorch", "huggingface", "data-science",
    }

    score = 0.0
    text = f"{name} {description or ''}".lower()
    all_terms = set(topics) | set(text.split())

    high_matches = all_terms & HIGH_SIGNAL
    medium_matches = all_terms & MEDIUM_SIGNAL

    if high_matches:
        score += min(0.6, len(high_matches) * 0.2)
    if medium_matches:
        score += min(0.3, len(medium_matches) * 0.1)

    # Keyword patterns in text
    ai_keywords = ["ai", "ml", "llm", "gpt", "agent", "rag", "mcp", "embedding", "neural", "transformer"]
    for kw in ai_keywords:
        if kw in text:
            score += 0.05

    return min(1.0, round(score, 4))


async def classify_person_with_llm(db: AsyncSession, person_id: str) -> bool:
    """Run LLM classification on a scored person."""
    person_result = await db.execute(select(Person).where(Person.id == person_id))
    person = person_result.scalar_one_or_none()
    if not person:
        return False

    gh_result = await db.execute(select(GitHubProfile).where(GitHubProfile.person_id == person_id))
    gh = gh_result.scalar_one_or_none()
    if not gh:
        return False

    # Build repos summary
    repo_links = await db.execute(select(PersonRepository).where(PersonRepository.person_id == person_id))
    repo_ids = [r.repository_id for r in repo_links.scalars().all()]
    repos_summary = "None"
    if repo_ids:
        repos_result = await db.execute(
            select(Repository)
            .where(Repository.id.in_(repo_ids), Repository.is_fork == False)  # noqa: E712
            .order_by(Repository.stars.desc())
            .limit(10)
        )
        repos = repos_result.scalars().all()
        repos_summary = "; ".join(
            f"{r.name} ({r.primary_language}, {r.stars}*)"
            for r in repos
        )

    # Build signals summary
    sig_result = await db.execute(
        select(Signal).where(Signal.person_id == person_id, Signal.is_active == True)  # noqa: E712
    )
    signals = sig_result.scalars().all()
    signals_summary = "; ".join(f"{s.signal_type} (strength={s.signal_strength:.2f})" for s in signals)

    primary_languages = json.loads(gh.primary_languages) if gh.primary_languages else []
    org_memberships = json.loads(gh.org_memberships) if gh.org_memberships else []

    result = await classify_builder(
        display_name=person.display_name,
        location=person.location,
        bio=person.bio,
        followers=gh.followers or 0,
        public_repos=gh.public_repos or 0,
        primary_languages=primary_languages,
        recent_repos_summary=repos_summary,
        org_memberships=org_memberships,
        scores={
            "technical": person.technical_score or 0,
            "momentum": person.momentum_score or 0,
            "ai": person.ai_nativeness_score or 0,
            "leadership": person.leadership_score or 0,
        },
        signals_summary=signals_summary,
    )

    if result:
        person.builder_experience = result.get("builder_experience")
        person.builder_type = result.get("builder_type")
        person.founder_fit = result.get("founder_fit")
        person.one_line_summary = result.get("one_line_summary")
        person.pipeline_stage = "classified"
        return True

    # Fallback: heuristic classification
    person.builder_experience = _heuristic_experience(gh)
    person.builder_type = _heuristic_builder_type(gh, primary_languages)
    person.founder_fit = _heuristic_founder_fit(person)
    person.pipeline_stage = "classified"
    return True


def _heuristic_experience(gh: GitHubProfile) -> str:
    if gh.public_repos and gh.public_repos > 30 and (gh.followers or 0) > 50:
        return "seasoned_builder"
    if gh.public_repos and gh.public_repos > 10:
        return "seasoned_builder"
    return "early_stage"


def _heuristic_builder_type(gh: GitHubProfile, languages: list[str]) -> str:
    systems_langs = {"rust", "go", "c", "c++", "zig"}
    if set(l.lower() for l in languages) & systems_langs:
        return "engineer"
    if (gh.followers or 0) > 100:
        return "generalist"
    return "engineer"


def _heuristic_founder_fit(person: Person) -> str:
    tech = person.technical_score or 0
    leadership = person.leadership_score or 0
    momentum = person.momentum_score or 0
    if tech > 0.5 and leadership > 0.4 and momentum > 0.3:
        return "good_builder_good_founder"
    if tech > 0.4:
        return "good_builder_not_founder"
    return "okay_builder"


async def batch_score(db: AsyncSession, limit: int = 50) -> int:
    """Score the next batch of enriched people."""
    result = await db.execute(
        select(Person).where(Person.pipeline_stage == "enriched").limit(limit)
    )
    people = result.scalars().all()

    scored = 0
    for person in people:
        try:
            success = await score_person(db, person.id)
            if success:
                scored += 1
                if scored % 10 == 0:
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to score {person.id}: {e}")

    await db.commit()
    logger.info(f"Batch scoring: {scored}/{len(people)} scored")
    return scored


async def batch_classify(db: AsyncSession, limit: int = 50) -> int:
    """Classify the next batch of scored people using LLM."""
    result = await db.execute(
        select(Person).where(Person.pipeline_stage == "scored").limit(limit)
    )
    people = result.scalars().all()

    classified = 0
    for person in people:
        try:
            success = await classify_person_with_llm(db, person.id)
            if success:
                classified += 1
                if classified % 5 == 0:
                    await db.commit()
        except Exception as e:
            logger.error(f"Failed to classify {person.id}: {e}")

    await db.commit()
    logger.info(f"Batch classification: {classified}/{len(people)} classified")
    return classified
