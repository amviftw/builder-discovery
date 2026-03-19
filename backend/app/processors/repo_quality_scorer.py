"""Repo quality scoring - heuristic-based quality assessment per repository."""

from __future__ import annotations

import math
from datetime import datetime


def score_repo_quality(
    stars: int = 0,
    forks: int = 0,
    watchers: int = 0,
    has_readme: bool = False,
    readme_length: int = 0,
    has_license: bool = False,
    has_ci: bool = False,
    topics_count: int = 0,
    days_since_push: int = 365,
    open_issues: int = 0,
    is_fork: bool = False,
    is_archived: bool = False,
) -> float:
    """
    Compute a quality score for a repository (0.0 to 1.0).

    Dimensions:
    - Popularity (stars, log-scaled)
    - Community engagement (forks + watchers ratio)
    - Documentation quality (readme, license, CI)
    - Freshness (recency of last push)
    - Topic richness
    """
    if is_fork or is_archived:
        return 0.0

    # Popularity: log-scale stars (0-1, caps around 1000 stars)
    popularity = min(1.0, math.log10(stars + 1) / 3.0)

    # Community: fork/watch ratio relative to stars
    community = min(1.0, (forks + watchers) / max(stars + 1, 1)) if stars > 0 else 0.0

    # Documentation quality
    documentation = (
        0.4 * (1.0 if has_readme else 0.0)
        + 0.2 * min(1.0, readme_length / 3000)
        + 0.2 * (1.0 if has_license else 0.0)
        + 0.2 * (1.0 if has_ci else 0.0)
    )

    # Freshness: linear decay over a year
    freshness = max(0.0, 1.0 - days_since_push / 365)

    # Topic richness bonus
    topic_bonus = min(0.1, topics_count * 0.02)

    quality = (
        0.30 * popularity
        + 0.15 * community
        + 0.25 * documentation
        + 0.20 * freshness
        + 0.10 * topic_bonus
    )

    return round(min(1.0, quality), 4)
