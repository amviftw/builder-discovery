"""Internal tool detection - identifies repos likely built as internal company tools."""

from __future__ import annotations

import json
from pathlib import Path


def load_company_keywords() -> list[str]:
    """Load known Indian company names for matching."""
    seed_file = Path(__file__).parent.parent.parent.parent / "database" / "seeds" / "indian_tech_companies.json"
    try:
        with open(seed_file) as f:
            companies = json.load(f)
        keywords = []
        for c in companies:
            keywords.append(c.get("name", "").lower())
            keywords.append(c.get("github_org_login", "").lower())
        return [k for k in keywords if k]
    except (FileNotFoundError, json.JSONDecodeError):
        return [
            "zomato", "swiggy", "razorpay", "zerodha", "flipkart",
            "phonepe", "cred", "groww", "postman", "freshworks",
            "meesho", "dream11", "browserstack", "hasura", "composio",
        ]


TOOL_PATTERNS = [
    "sdk", "client", "internal", "tool", "util", "helper",
    "mcp", "server", "api-client", "dashboard", "admin",
    "portal", "service", "platform",
]

INTERNAL_README_INDICATORS = [
    "internal", "company", "staging", "production",
    ".internal.", "vpn", "okta", "private",
]


def score_internal_tool(
    repo_name: str = "",
    description: str | None = None,
    readme_text: str | None = None,
    contributor_count: int = 0,
    size_kb: int = 0,
    stars: int = 0,
    is_fork: bool = False,
    is_archived: bool = False,
) -> tuple[float, dict]:
    """
    Score how likely a repo is an internal company tool (0.0-1.0).

    Returns (score, evidence_dict).
    """
    if is_fork or is_archived:
        return 0.0, {}

    score = 0.0
    evidence = {}
    text = f"{repo_name} {description or ''}".lower()

    # 1. Few contributors but mature codebase
    if 1 <= contributor_count <= 5 and size_kb > 500:
        score += 0.20
        evidence["few_contributors_mature_code"] = True

    # 2. Company name references
    company_keywords = load_company_keywords()
    matched = [c for c in company_keywords if c in text or (readme_text and c in readme_text.lower())]
    if matched:
        score += 0.25
        evidence["company_references"] = matched[:5]

    # 3. Tool naming patterns
    name_lower = repo_name.lower()
    matching_patterns = [p for p in TOOL_PATTERNS if p in name_lower]
    if matching_patterns:
        score += 0.15
        evidence["tool_name_patterns"] = matching_patterns

    # 4. Internal indicators in description/readme
    if readme_text:
        indicators = [ind for ind in INTERNAL_README_INDICATORS if ind in readme_text.lower()]
        if indicators:
            score += 0.10
            evidence["internal_readme_indicators"] = indicators

    # 5. Low stars relative to code size (not meant for public consumption)
    if size_kb > 1000 and stars < 10:
        score += 0.10
        evidence["low_stars_high_code"] = True

    # 6. Active and not archived
    if not is_fork and not is_archived:
        score += 0.05

    return min(1.0, score), evidence
