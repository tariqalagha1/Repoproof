"""Unit tests — URL validation, repository discovery, secret fingerprinting."""

import tempfile
from pathlib import Path

from src.application.services.url_validation import validate_repository_url
from src.application.services.discovery import discover_repository, secret_fingerprint


# ═══════════════════════════════════════════════════════════
# URL Validation
# ═══════════════════════════════════════════════════════════

class TestURLValidation:
    def test_valid_github_url(self):
        ok, err = validate_repository_url("https://github.com/nousresearch/hermes-agent")
        assert ok
        assert err is None

    def test_empty_url_rejected(self):
        ok, err = validate_repository_url("")
        assert not ok
        assert "required" in err.lower()

    def test_non_https_rejected(self):
        ok, err = validate_repository_url("http://github.com/a/b")
        assert not ok

    def test_non_github_host_rejected(self):
        ok, err = validate_repository_url("https://gitlab.com/a/b")
        assert not ok

    def test_malformed_url_rejected(self):
        ok, err = validate_repository_url("not-a-url")
        assert not ok

    def test_single_segment_path_rejected(self):
        ok, err = validate_repository_url("https://github.com/onlyowner")
        assert not ok


# ═══════════════════════════════════════════════════════════
# Repository Discovery
# ═══════════════════════════════════════════════════════════

class TestDiscovery:
    async def test_python_language_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("print('hi')")
            (Path(tmp) / "README.md").write_text("# hi")
            disc = await discover_repository(Path(tmp))
            assert "python" in disc["detected_languages"]

    async def test_entry_point_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("x = 1")
            disc = await discover_repository(Path(tmp))
            assert "main.py" in disc["entry_points"]

    async def test_framework_detected_from_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requirements.txt").write_text("fastapi\nuvicorn\n")
            disc = await discover_repository(Path(tmp))
            assert "fastapi" in disc["detected_frameworks"]

    async def test_dependency_files_listed(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requirements.txt").write_text("")
            (Path(tmp) / "package.json").write_text("{}")
            disc = await discover_repository(Path(tmp))
            deps = disc["dependency_files"]
            assert any("requirements.txt" in f for f in deps)
            assert any("package.json" in f for f in deps)

    async def test_file_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "a.py").write_text("")
            (Path(tmp) / "b.py").write_text("")
            disc = await discover_repository(Path(tmp))
            assert disc["file_count"] >= 2

    async def test_result_has_required_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "x.py").write_text("")
            disc = await discover_repository(Path(tmp))
            for key in ("project_root", "entry_points", "detected_frameworks",
                        "detected_languages", "dependency_files", "file_count"):
                assert key in disc


# ═══════════════════════════════════════════════════════════
# Secret Fingerprinting
# ═══════════════════════════════════════════════════════════

class TestSecretFingerprint:
    async def test_env_file_detected_by_filename(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".env").write_text("SECRET=x")
            findings = await secret_fingerprint(Path(tmp))
            assert any(f["type"] == "filename_match" for f in findings)

    async def test_openai_key_detected_by_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "config.py").write_text('KEY = "sk-' + "A" * 32 + '"')
            findings = await secret_fingerprint(Path(tmp))
            labels = {f["pattern"] for f in findings}
            assert "OpenAI API key" in labels

    async def test_clean_repo_has_no_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "main.py").write_text("print('hello world')\n")
            findings = await secret_fingerprint(Path(tmp))
            assert len(findings) == 0

    async def test_secret_value_never_in_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret = "sk-" + "B" * 40
            (Path(tmp) / "env.py").write_text(f'KEY = "{secret}"')
            findings = await secret_fingerprint(Path(tmp))
            for f in findings:
                assert secret not in f.get("message", "")

    async def test_private_key_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "key.pem").write_text("-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----\n")
            findings = await secret_fingerprint(Path(tmp))
            assert len(findings) >= 1
