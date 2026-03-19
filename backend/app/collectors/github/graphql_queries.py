"""Reusable GraphQL query fragments for GitHub API v4."""

USER_PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    id
    databaseId
    login
    name
    bio
    company
    location
    websiteUrl
    avatarUrl
    isHireable
    twitterUsername
    followers { totalCount }
    following { totalCount }
    repositories(first: 0, ownerAffiliations: OWNER) { totalCount }
    organizations(first: 0) { totalCount }
    createdAt
    updatedAt
  }
}
"""

CONTRIBUTION_CALENDAR_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

USER_REPOS_QUERY = """
query($login: String!, $first: Int!, $after: String) {
  user(login: $login) {
    repositories(
      first: $first
      after: $after
      ownerAffiliations: OWNER
      orderBy: {field: STARGAZERS, direction: DESC}
    ) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        databaseId
        name
        nameWithOwner
        description
        url
        stargazerCount
        forkCount
        watchers { totalCount }
        primaryLanguage { name }
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name }
          }
        }
        repositoryTopics(first: 20) {
          nodes { topic { name } }
        }
        createdAt
        pushedAt
        updatedAt
        isFork
        isArchived
        diskUsage
        licenseInfo { spdxId }
        hasIssuesEnabled
        openIssues: issues(states: OPEN) { totalCount }
        defaultBranchRef {
          name
          target {
            ... on Commit {
              history(first: 0) { totalCount }
            }
          }
        }
        object(expression: "HEAD:README.md") {
          ... on Blob { byteSize }
        }
        object2: object(expression: "HEAD:.github/workflows") {
          ... on Tree { entries { name } }
        }
      }
    }
  }
}
"""

BATCH_USER_PROFILES_QUERY_TEMPLATE = """
query {{
  {user_fragments}
}}
"""

BATCH_USER_FRAGMENT = """
  user_{idx}: user(login: "{login}") {{
    databaseId
    login
    name
    bio
    company
    location
    avatarUrl
    isHireable
    twitterUsername
    followers {{ totalCount }}
    following {{ totalCount }}
    repositories(first: 0, ownerAffiliations: OWNER) {{ totalCount }}
    createdAt
  }}
"""


def build_batch_users_query(logins: list[str]) -> str:
    """Build a GraphQL query that fetches multiple users in one call."""
    fragments = []
    for idx, login in enumerate(logins):
        fragments.append(BATCH_USER_FRAGMENT.format(idx=idx, login=login))
    return BATCH_USER_PROFILES_QUERY_TEMPLATE.format(user_fragments="\n".join(fragments))
