"""LLM client - Google Gemini Flash free tier for classification and analysis."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)


async def classify_with_gemini(prompt: str) -> dict[str, Any] | None:
    """
    Call Gemini Flash for classification. Returns parsed JSON response.
    Falls back to None if API fails.
    """
    if not settings.gemini_api_key:
        logger.warning("No Gemini API key configured, skipping LLM classification")
        return None

    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "temperature": 0.3,
                "max_output_tokens": 1024,
            },
        )

        text = response.text.strip()
        # Try to parse JSON from response
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)

    except Exception as e:
        logger.warning(f"Gemini classification failed: {e}")
        return None


async def classify_ai_relevance(
    repo_name: str,
    description: str | None,
    topics: list[str],
    primary_language: str | None,
    readme_excerpt: str | None = None,
) -> dict[str, Any] | None:
    """Classify a repository's AI relevance using Gemini."""
    prompt = f"""Analyze this GitHub repository and classify its AI-relevance.

Repository: {repo_name}
Description: {description or 'N/A'}
Topics: {', '.join(topics) if topics else 'N/A'}
Primary Language: {primary_language or 'N/A'}
README excerpt: {(readme_excerpt or 'N/A')[:1500]}

Classify on these dimensions:

1. ai_relevance (0.0-1.0): How related is this to AI/ML/LLM development?
   - 1.0: Core AI/ML library, LLM application, AI agent framework
   - 0.7: Uses AI/ML as a significant component
   - 0.4: Tangentially related (data pipeline, ML-adjacent)
   - 0.1: Not AI-related but modern tech
   - 0.0: Not relevant

2. builder_sophistication (0.0-1.0): How sophisticated is the engineering?

3. categories (list): Which apply? Options: llm_app, ai_agent, ml_model, data_pipeline, mcp_server, developer_tool, infrastructure, web_app, api_service, other

Respond in JSON: {{"ai_relevance": float, "builder_sophistication": float, "categories": [str]}}"""

    return await classify_with_gemini(prompt)


async def classify_builder(
    display_name: str | None,
    location: str | None,
    bio: str | None,
    followers: int,
    public_repos: int,
    primary_languages: list[str],
    recent_repos_summary: str,
    org_memberships: list[str],
    scores: dict[str, float],
    signals_summary: str,
) -> dict[str, Any] | None:
    """Classify a builder's type and founder fit using Gemini."""
    prompt = f"""Classify this builder's profile for a VC fund looking for potential AI-native founders.

Name: {display_name or 'Unknown'}
Location: {location or 'Unknown'}
Bio: {bio or 'N/A'}
GitHub followers: {followers}
Total repos: {public_repos}
Top languages: {', '.join(primary_languages) if primary_languages else 'N/A'}
Recent repos (last 6 months): {recent_repos_summary}
Org memberships: {', '.join(org_memberships) if org_memberships else 'N/A'}
Scores: Technical={scores.get('technical', 0):.2f}, Momentum={scores.get('momentum', 0):.2f}, AI-nativeness={scores.get('ai', 0):.2f}, Leadership={scores.get('leadership', 0):.2f}
Active signals: {signals_summary or 'None'}

CLASSIFY:

1. builder_experience: One of:
   - "seasoned_builder": Substantial open-source work, multiple repos, established presence
   - "seasoned_academia": Research background, academic repos, papers
   - "early_stage": Fewer than 3 years visible, promising but early

2. builder_type: One of:
   - "generalist": Broad skillset, writes docs, visible online, likely to sell/lead
   - "product_leader": Product-oriented repos (dashboards, tools, user-facing)
   - "engineer": Deep technical repos (libraries, frameworks, infra)

3. founder_fit: One of:
   - "good_builder_good_founder": High technical + high leadership + active momentum
   - "good_builder_not_founder": High technical but low leadership signals
   - "okay_builder": Moderate technical, interesting with right co-founder

4. one_line_summary: A single sentence summarizing why this person is interesting.

Respond in JSON: {{"builder_experience": str, "builder_type": str, "founder_fit": str, "one_line_summary": str}}"""

    return await classify_with_gemini(prompt)
