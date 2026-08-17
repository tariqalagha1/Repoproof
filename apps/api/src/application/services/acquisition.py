"""Repository acquisition — safe git clone with commit locking."""

import tempfile
from pathlib import Path


async def safe_clone(url: str, target_dir: Path | None = None, branch: str = "main") -> tuple[Path, str]:
    """Clone a repository safely, returning (path, commit_hash).

    Uses gitpython if available, otherwise falls back to subprocess git.
    """
    work_dir = Path(target_dir) if target_dir else Path(tempfile.mkdtemp(prefix="repoproof-clone-"))

    try:
        import git
        repo = git.Repo.clone_from(
            url,
            str(work_dir),
            branch=branch,
            depth=1,
            single_branch=True,
        )
        commit_hash = repo.head.commit.hexsha
    except ImportError:
        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", "--single-branch", "--branch", branch, url, str(work_dir)],
                check=True, capture_output=True, text=True, timeout=120,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Git clone failed: {e.stderr}") from e
        commit = subprocess.run(
            ["git", "-C", str(work_dir), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        )
        commit_hash = commit.stdout.strip()

    return work_dir, commit_hash


async def acquire_repository(url: str, target_dir: Path | None = None, branch: str = "main") -> dict:
    """Acquire a repository and return metadata."""
    try:
        work_dir, commit_hash = await safe_clone(url, target_dir, branch)
        return {
            "success": True,
            "path": str(work_dir),
            "commit_hash": commit_hash,
            "branch": branch,
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
