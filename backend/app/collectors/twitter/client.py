"""Twitter/X collector - Phase 2 stub."""
# This module will be implemented when Twitter API integration is added.
# The hooks are designed but not yet functional.


async def link_twitter_from_github(github_twitter_username: str | None) -> dict | None:
    """Stub: Link a Twitter profile from GitHub's twitter_username field."""
    if not github_twitter_username:
        return None
    return {
        "handle": github_twitter_username,
        "linked_via": "github_field",
        "confidence": 0.9,
    }
