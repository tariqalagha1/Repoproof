"""URL validation for repository connections."""

import re

GITHUB_URL_RE = re.compile(
    r"^https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+(?:/.*)?$"
)


def validate_repository_url(url: str) -> tuple[bool, str | None]:
    """Validate a repository URL. Returns (is_valid, error_message)."""
    if not url:
        return False, "URL is required"
    if not url.startswith("https://"):
        return False, "Only HTTPS URLs are supported"
    if not GITHUB_URL_RE.match(url):
        return False, "URL must be a valid GitHub repository URL (https://github.com/owner/repo)"
    return True, None
