"""Phase 1 — Safe Downloader: zip-based fetch, extraction, auto-cleanup.

Replaces git clone with static .zip archive download.
No git hooks, no submodule execution, no LFS, no credential exposure.
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import httpx


class SafeDownloadResult:
    def __init__(self, extract_path: Path, commit_sha: str = "", file_count: int = 0):
        self.extract_path = extract_path
        self.commit_sha = commit_sha
        self.file_count = file_count
        self.cleaned_up = False

    def cleanup(self):
        """Remove the extracted directory and all contents."""
        if not self.cleaned_up and self.extract_path.exists():
            shutil.rmtree(self.extract_path, ignore_errors=True)
            self.cleaned_up = True


async def fetch_repo_zip(
    repo_url: str,
    branch: str = "main",
    timeout: int = 60,
) -> SafeDownloadResult:
    """Download a GitHub repository as a .zip archive and extract it.

    Args:
        repo_url: GitHub URL like https://github.com/owner/repo
        branch: Branch name (default 'main')
        timeout: Download timeout in seconds

    Returns:
        SafeDownloadResult with extract path, commit SHA, and file count.

    Uses GitHub's /archive/ endpoint which returns a static zip — no
    git clone, no hooks, no submodules, no LFS, no credential prompts.
    """
    parsed = urlparse(repo_url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) < 2:
        raise ValueError(f"Cannot parse owner/repo from URL: {repo_url}")

    owner, repo = path_parts[0], path_parts[1]
    repo = repo.removesuffix(".git")

    # GitHub archive endpoint (public repos only, no auth)
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"

    # Also fetch the commit SHA from GitHub API (lightweight — no clone)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}"
    commit_sha = ""

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # Try to get commit SHA
        try:
            api_resp = await client.get(api_url)
            if api_resp.status_code == 200:
                commit_sha = api_resp.json().get("object", {}).get("sha", "")
        except Exception:
            pass

        # Download zip
        zip_resp = await client.get(zip_url)
        if zip_resp.status_code != 200:
            raise RuntimeError(
                f"Failed to download {zip_url}: HTTP {zip_resp.status_code}"
            )

        # Extract to temp directory
        extract_dir = Path(tempfile.mkdtemp(prefix="repoproof-zip-"))
        zip_path = extract_dir / "repo.zip"
        zip_path.write_bytes(zip_resp.content)

        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        zip_path.unlink()  # Remove zip after extraction

        # Find the extracted directory (GitHub wraps in repo-branch/)
        subdirs = [d for d in extract_dir.iterdir() if d.is_dir()]
        if subdirs:
            extract_dir = subdirs[0]

        # Count files
        file_count = sum(1 for _ in extract_dir.rglob("*") if _.is_file())

    return SafeDownloadResult(
        extract_path=extract_dir,
        commit_sha=commit_sha,
        file_count=file_count,
    )
