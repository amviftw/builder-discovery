"""Activity pattern analyzer - detects dips and spikes in contribution data."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class ActivitySignal:
    signal_type: str  # activity_dip, activity_spike, new_repo_burst
    signal_strength: float  # 0.0 to 1.0
    evidence: dict
    description: str


def detect_activity_dip(weekly_contributions: list[int], window_size: int = 4) -> ActivitySignal | None:
    """
    Detect significant activity dips that may indicate departure/burnout/transition.

    Algorithm:
    1. Compute rolling average with window_size (default 4 weeks).
    2. Compute the overall mean and std_dev from baseline (weeks 1-40).
    3. If recent 12 weeks have 3+ consecutive windows below (mean - 1.5*std),
       flag as activity_dip.
    """
    if len(weekly_contributions) < 16:
        return None

    # Rolling averages
    rolling = []
    for i in range(len(weekly_contributions) - window_size + 1):
        avg = sum(weekly_contributions[i : i + window_size]) / window_size
        rolling.append(avg)

    if len(rolling) < 12:
        return None

    # Baseline: everything except the most recent 12 windows
    baseline = rolling[: -12] if len(rolling) > 12 else rolling[: len(rolling) // 2]
    if not baseline:
        return None

    mean_baseline = statistics.mean(baseline)
    if mean_baseline < 2:
        return None  # Skip nearly inactive users

    std_baseline = statistics.stdev(baseline) if len(baseline) > 1 else 0
    threshold = mean_baseline - 1.5 * std_baseline

    # Check recent 12 windows
    recent = rolling[-12:]
    consecutive_below = 0
    max_consecutive = 0
    for val in recent:
        if val < threshold:
            consecutive_below += 1
            max_consecutive = max(max_consecutive, consecutive_below)
        else:
            consecutive_below = 0

    if max_consecutive >= 3:
        recent_avg = statistics.mean(recent[-4:]) if len(recent) >= 4 else statistics.mean(recent)
        decline_ratio = 1 - (recent_avg / mean_baseline) if mean_baseline > 0 else 0
        strength = min(1.0, max(0.0, decline_ratio))

        return ActivitySignal(
            signal_type="activity_dip",
            signal_strength=strength,
            evidence={
                "baseline_weekly_avg": round(mean_baseline, 1),
                "recent_weekly_avg": round(recent_avg, 1),
                "decline_percentage": round(decline_ratio * 100, 1),
                "consecutive_low_weeks": max_consecutive,
            },
            description=f"Activity dropped {decline_ratio * 100:.0f}% below baseline ({max_consecutive} consecutive low weeks)",
        )
    return None


def detect_activity_spike(weekly_contributions: list[int], window_size: int = 4) -> ActivitySignal | None:
    """Detect sudden increase in activity (builder momentum indicator)."""
    if len(weekly_contributions) < 16:
        return None

    rolling = []
    for i in range(len(weekly_contributions) - window_size + 1):
        rolling.append(sum(weekly_contributions[i : i + window_size]) / window_size)

    if len(rolling) < 12:
        return None

    baseline = rolling[: -12] if len(rolling) > 12 else rolling[: len(rolling) // 2]
    if not baseline:
        return None

    mean_baseline = statistics.mean(baseline)
    if mean_baseline < 1:
        # New-to-active: check if recent activity is significant
        recent_avg = statistics.mean(rolling[-4:])
        if recent_avg >= 5:
            return ActivitySignal(
                signal_type="activity_spike",
                signal_strength=min(1.0, recent_avg / 20),
                evidence={
                    "baseline_weekly_avg": round(mean_baseline, 1),
                    "recent_weekly_avg": round(recent_avg, 1),
                    "growth_type": "new_to_active",
                },
                description=f"Newly active builder: {recent_avg:.0f} contributions/week (was {mean_baseline:.0f})",
            )
        return None

    std_baseline = statistics.stdev(baseline) if len(baseline) > 1 else 0
    threshold = mean_baseline + 1.5 * std_baseline

    recent = rolling[-8:]
    above_count = sum(1 for v in recent if v > threshold)

    if above_count >= 4:
        recent_avg = statistics.mean(recent[-4:])
        growth_ratio = (recent_avg / mean_baseline) - 1 if mean_baseline > 0 else 0
        strength = min(1.0, growth_ratio / 2.0)

        return ActivitySignal(
            signal_type="activity_spike",
            signal_strength=strength,
            evidence={
                "baseline_weekly_avg": round(mean_baseline, 1),
                "recent_weekly_avg": round(recent_avg, 1),
                "growth_percentage": round(growth_ratio * 100, 1),
            },
            description=f"Activity surged {growth_ratio * 100:.0f}% above baseline",
        )
    return None


def analyze_activity(weekly_contributions: list[int]) -> list[ActivitySignal]:
    """Run all activity analyses and return detected signals."""
    signals = []
    dip = detect_activity_dip(weekly_contributions)
    if dip:
        signals.append(dip)
    spike = detect_activity_spike(weekly_contributions)
    if spike:
        signals.append(spike)
    return signals
