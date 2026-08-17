"""Repository discovery — passive file-tree analysis, dependency parsing."""

import json
import re
from pathlib import Path


# ── Content-based secret patterns (pre-compiled) ──────────
_SECRET_CONTENT_PATTERNS: list[tuple[re.Pattern, str, str]] = [
    # AWS Access Key ID
    (re.compile(r'(?:A3T[A-Z0-9]|AKIA|ASIA)[A-Z0-9]{16}'), "AWS Access Key ID", "critical"),
    # GitHub Personal Access Token
    (re.compile(r'gh[pousr]_[A-Za-z0-9_]{36,}'), "GitHub Personal Access Token", "critical"),
    # Generic API key patterns
    (re.compile(r'(?:api[_-]?key|apikey|api_secret|secret[_-]?key)\s*=\s*["\'][A-Za-z0-9_\-+/=]{20,}["\']', re.IGNORECASE), "Hardcoded API key/secret", "critical"),
    # Private SSH key
    (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'), "Private key in source", "critical"),
    # JWT token
    (re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), "Hardcoded JWT token", "high"),
    # Database connection strings
    (re.compile(r'(?:mysql|postgres(?:ql)?|mongodb|redis|sqlite)://[^"\'\s]{10,}', re.IGNORECASE), "Database connection string", "high"),
    # Generic password assignment (not in test files)
    (re.compile(r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{6,}["\']', re.IGNORECASE), "Hardcoded password", "critical"),
    # Stripe keys
    (re.compile(r'sk_live_[0-9a-zA-Z]{24,}'), "Stripe secret key", "critical"),
    # Generic token assignment
    (re.compile(r'(?:auth[_-]?token|access[_-]?token|bearer)\s*=\s*["\'][A-Za-z0-9_\-.]{16,}["\']', re.IGNORECASE), "Hardcoded auth token", "critical"),
    # PEM-encoded certificates
    (re.compile(r'-----BEGIN CERTIFICATE-----'), "Embedded certificate", "medium"),
    # Slack webhook / token
    (re.compile(r'https://hooks\.slack\.com/services/[A-Za-z0-9/]+'), "Slack webhook URL", "high"),
    # OpenAI API key
    (re.compile(r'sk-[A-Za-z0-9]{32,}'), "OpenAI API key", "critical"),
    # Google API key
    (re.compile(r'AIza[0-9A-Za-z\-_]{35}'), "Google API key", "critical"),
]

# ── File-size cap for content scanning ────────────────────
_MAX_SCAN_BYTES = 500_000  # skip files larger than 500KB
_SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', '.next', 'dist', 'build', '.hermes'}


async def discover_repository(project_root: Path) -> dict:
    """Run passive discovery on a repository checkout."""
    root = Path(project_root)

    entry_points = _find_entry_points(root)
    frameworks = _detect_frameworks(root)
    languages = _detect_languages(root)
    dep_files = _find_dependency_files(root)
    file_count = _count_files(root)

    return {
        "project_root": str(root),
        "entry_points": entry_points,
        "detected_frameworks": frameworks,
        "detected_languages": languages,
        "dependency_files": dep_files,
        "file_count": file_count,
    }


def _find_entry_points(root: Path) -> list[str]:
    entry_candidates = [
        "main.py", "app.py", "index.js", "server.js", "main.go",
        "src/main.py", "src/app.py", "src/index.js",
        "manage.py", "run.py", "app/main.py",
    ]
    found = []
    for candidate in entry_candidates:
        if (root / candidate).exists():
            found.append(candidate)
    return found


def _detect_frameworks(root: Path) -> list[str]:
    framework_signatures = {
        "fastapi": ["fastapi"],
        "django": ["django"],
        "flask": ["flask"],
        "next.js": ["next"],
        "express": ["express"],
        "react": ["react"],
        "vue": ["vue"],
        "svelte": ["svelte"],
        "gin": ["github.com/gin-gonic/gin"],
        "spring": ["org.springframework"],
        "laravel": ["laravel"],
    }
    found = []
    # Check package.json
    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            import json
            data = json.loads(pkg_json.read_text())
            all_deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for fw, keys in framework_signatures.items():
                for key in keys:
                    if key in all_deps or any(key in k for k in all_deps):
                        found.append(fw)
                        break
        except Exception:
            pass

    # Check requirements.txt / pyproject.toml
    for req_file in [root / "requirements.txt", root / "pyproject.toml"]:
        if req_file.exists():
            content = req_file.read_text(errors="ignore").lower()
            if "fastapi" in content:
                found.append("fastapi")
            if "django" in content:
                found.append("django")
            if "flask" in content:
                found.append("flask")

    # Check go.mod
    go_mod = root / "go.mod"
    if go_mod.exists():
        content = go_mod.read_text(errors="ignore").lower()
        if "gin-gonic/gin" in content:
            found.append("gin")

    return list(set(found))


def _detect_languages(root: Path) -> list[str]:
    language_extensions = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".rb": "ruby",
        ".php": "php",
        ".cs": "csharp",
        ".kt": "kotlin",
    }
    found = set()
    for ext, lang in language_extensions.items():
        # Simple check — look for at least one file with the extension
        for f in root.rglob(f"*{ext}"):
            if f.is_file() and not any(p.startswith('.') for p in f.parts if p != root.name):
                found.add(lang)
                break
    return sorted(found)


def _find_dependency_files(root: Path) -> list[str]:
    dep_patterns = [
        "requirements.txt", "Pipfile", "Pipfile.lock", "pyproject.toml", "poetry.lock",
        "package.json", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        "go.mod", "go.sum", "Cargo.toml", "Cargo.lock",
        "pom.xml", "build.gradle", "build.gradle.kts",
        "Gemfile", "Gemfile.lock", "composer.json", "composer.lock",
    ]
    found = []
    for pattern in dep_patterns:
        matches = list(root.rglob(pattern))
        for m in matches:
            found.append(str(m.relative_to(root)))
    return found


def _count_files(root: Path) -> int:
    count = 0
    for f in root.rglob("*"):
        if f.is_file() and not any(p.startswith('.') for p in f.parts if p != root.name):
            count += 1
    return count


async def secret_fingerprint(project_root: Path) -> list[dict]:
    """Detect secrets via filename patterns AND content-based regex scanning.

    Phase 1 — Filename scan: flags sensitive filenames (.env, id_rsa, etc.)
    Phase 2 — Content scan: regex-matches file contents for API keys,
    passwords, tokens, private keys, connection strings, and webhooks.

    Skips binary files, files >500KB, and standard dev directories.
    """
    root = Path(project_root)
    findings: list[dict] = []

    # ── Phase 1: Filename-based scan ────────────────────
    sensitive_patterns = [
        (".env", "Environment file found — may contain secrets", "medium"),
        ("credentials.json", "Credentials file found", "high"),
        ("id_rsa", "Private SSH key file found", "critical"),
        (".pem", "PEM certificate/key file found", "high"),
    ]

    for pattern, message, severity in sensitive_patterns:
        for f in root.rglob(f"*{pattern}*"):
            if f.is_file():
                skip = any(p in _SKIP_DIRS for p in f.parts)
                if not skip:
                    findings.append({
                        "type": "filename_match",
                        "pattern": pattern,
                        "message": message,
                        "severity": severity,
                        "file": str(f.relative_to(root)),
                        "line": 0,
                    })

    # ── Phase 2: Content-based scan ─────────────────────
    text_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.json', '.yaml', '.yml',
        '.toml', '.cfg', '.ini', '.env', '.sh', '.bash', '.txt', '.md',
        '.html', '.css', '.xml', '.java', '.go', '.rs', '.rb', '.php',
        '.cs', '.kt', '.swift', '.c', '.cpp', '.h', '.hpp',
    }

    files_scanned = 0
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in text_extensions:
            continue
        if f.stat().st_size > _MAX_SCAN_BYTES:
            continue
        if any(p in _SKIP_DIRS for p in f.parts):
            continue

        try:
            content = f.read_text(errors="replace")
        except Exception:
            continue

        files_scanned += 1
        lines = content.split("\n")

        for regex, label, severity in _SECRET_CONTENT_PATTERNS:
            for match in regex.finditer(content):
                line_no = content[:match.start()].count("\n") + 1
                # Redact the match value — never include the secret itself
                snippet = match.group()[:4] + "***" + match.group()[-4:] if len(match.group()) > 8 else "***"
                findings.append({
                    "type": "content_match",
                    "pattern": label,
                    "message": f"{label}: {snippet}",
                    "severity": severity,
                    "file": str(f.relative_to(root)),
                    "line": line_no,
                })

    return findings
