"""Composite Founder Propensity Score - combines all dimension scores."""

from __future__ import annotations

import json
import math
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta


SCORE_WEIGHTS = {
    "technical_capability": 0.20,
    "builder_momentum": 0.20,
    "ai_nativeness": 0.20,
    "leadership": 0.15,
    "departure_signal": 0.15,
    "network_quality": 0.10,
}


@dataclass
class CompositeScore:
    founder_propensity_score: float
    technical_score: float
    momentum_score: float
    ai_nativeness_score: float
    leadership_score: float
    departure_signal_score: float
    network_score: float = 0.0


def compute_technical_score(
    repo_quality_scores: list[float],
    total_stars: int = 0,
    language_count: int = 0,
    contribution_volume_52w: int = 0,
    has_popular_repo: bool = False,
) -> float:
    """Technical capability score (0.0-1.0)."""
    if not repo_quality_scores:
        return 0.0

    # Focus on top 10 repos
    top_scores = sorted(repo_quality_scores, reverse=True)[:10]
    avg_quality = statistics.mean(top_scores)

    star_factor = min(1.0, math.log10(total_stars + 1) / 3.5)
    lang_factor = min(1.0, language_count / 6)
    volume_factor = min(1.0, contribution_volume_52w / 1000)  # Caps at ~1000 contributions/year
    popular_bonus = 0.15 if has_popular_repo else 0.0

    score = (
        0.35 * avg_quality
        + 0.20 * star_factor
        + 0.10 * lang_factor
        + 0.20 * volume_factor
        + 0.15 * popular_bonus
    )
    return round(min(1.0, score), 4)


def compute_momentum_score(
    weekly_contributions: list[int],
    repos_created_last_90d: int = 0,
) -> float:
    """Builder momentum score (0.0-1.0)."""
    if not weekly_contributions or len(weekly_contributions) < 12:
        return 0.0

    # Baseline: weeks 0-39, Recent: weeks 40-51
    split = max(1, len(weekly_contributions) - 12)
    baseline = weekly_contributions[:split]
    recent = weekly_contributions[split:]

    baseline_avg = statistics.mean(baseline) if baseline else 0
    recent_avg = statistics.mean(recent) if recent else 0

    if baseline_avg < 1:
        trend_score = min(1.0, recent_avg / 10)
    else:
        ratio = recent_avg / baseline_avg
        trend_score = min(1.0, ratio / 2.0)

    new_repo_score = min(1.0, repos_created_last_90d / 5.0)

    score = 0.70 * trend_score + 0.30 * new_repo_score
    return round(min(1.0, score), 4)


def compute_ai_nativeness_score(
    repo_ai_scores: list[tuple[float, bool]],  # (ai_relevance_score, created_in_last_6m)
    has_mcp_repo: bool = False,
    total_repos: int = 1,
) -> float:
    """AI-nativeness score (0.0-1.0)."""
    if not repo_ai_scores:
        return 0.0

    ai_repos = [(score, recent) for score, recent in repo_ai_scores if score > 0.5]
    ai_ratio = len(ai_repos) / max(1, total_repos)

    if ai_repos:
        weighted_sum = sum(
            s * (2.0 if recent else 1.0) for s, recent in ai_repos
        )
        weighted_avg = weighted_sum / (len(ai_repos) * 1.5)
    else:
        weighted_avg = 0.0

    mcp_bonus = 0.20 if has_mcp_repo else 0.0

    score = (
        0.35 * ai_ratio
        + 0.45 * min(1.0, weighted_avg)
        + 0.20 * mcp_bonus
    )
    return round(min(1.0, score), 4)


def compute_leadership_score(
    owned_repos_count: int = 0,
    avg_doc_quality: float = 0.0,
    follower_ratio: float = 0.0,
    org_count: int = 0,
    has_website: bool = False,
) -> float:
    """Leadership signal score (0.0-1.0)."""
    ownership = min(1.0, owned_repos_count / 15.0)
    doc = avg_doc_quality
    influence = min(1.0, follower_ratio / 5.0)
    org_factor = min(1.0, org_count / 3.0)
    web_bonus = 0.05 if has_website else 0.0

    score = (
        0.30 * ownership
        + 0.25 * doc
        + 0.20 * influence
        + 0.20 * org_factor
        + 0.05 * web_bonus
    )
    return round(min(1.0, score), 4)


def compute_departure_signal_score(
    signal_strengths: list[tuple[str, float]],  # (signal_type, strength)
) -> float:
    """Departure signal score from active signals (0.0-1.0)."""
    type_weights = {
        "activity_dip": 1.0,
        "org_departure": 0.9,
        "resignation_clump_member": 0.85,
        "hireable_flag_on": 0.7,
        "profile_change": 0.5,
    }

    relevant = [
        strength * type_weights.get(stype, 0.3)
        for stype, strength in signal_strengths
        if stype in type_weights
    ]

    if not relevant:
        return 0.0

    max_signal = max(relevant)
    count_bonus = min(0.2, (len(relevant) - 1) * 0.1)
    return round(min(1.0, max_signal + count_bonus), 4)


def compute_composite_score(
    technical: float,
    momentum: float,
    ai_nativeness: float,
    leadership: float,
    departure: float,
    network: float = 0.0,
) -> CompositeScore:
    """Combine all dimension scores into composite Founder Propensity Score."""
    composite = (
        SCORE_WEIGHTS["technical_capability"] * technical
        + SCORE_WEIGHTS["builder_momentum"] * momentum
        + SCORE_WEIGHTS["ai_nativeness"] * ai_nativeness
        + SCORE_WEIGHTS["leadership"] * leadership
        + SCORE_WEIGHTS["departure_signal"] * departure
        + SCORE_WEIGHTS["network_quality"] * network
    )

    return CompositeScore(
        founder_propensity_score=round(composite, 4),
        technical_score=technical,
        momentum_score=momentum,
        ai_nativeness_score=ai_nativeness,
        leadership_score=leadership,
        departure_signal_score=departure,
        network_score=network,
    )
