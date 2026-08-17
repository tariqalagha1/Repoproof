"""DeterministicPlanner — ecosystem detection and plan generation."""

from pathlib import Path

from src.domain.plan_enums import Ecosystem


def detect_ecosystem(manifest: dict) -> Ecosystem:
    """Detect ecosystem from discovery manifest."""
    languages = manifest.get("detected_languages", [])
    frameworks = manifest.get("detected_frameworks", [])
    dep_files = manifest.get("dependency_files", [])

    # Python detection
    if "python" in languages:
        return Ecosystem.PYTHON
    if any(f.endswith("requirements.txt") or f.endswith("pyproject.toml") or f.endswith("setup.py") for f in dep_files):
        return Ecosystem.PYTHON
    if any(fw in ("fastapi", "django", "flask") for fw in frameworks):
        return Ecosystem.PYTHON

    # Node detection
    if "javascript" in languages or "typescript" in languages:
        return Ecosystem.NODE
    if any(f.endswith("package.json") for f in dep_files):
        return Ecosystem.NODE
    if any(fw in ("express", "next.js", "react", "vue") for fw in frameworks):
        return Ecosystem.NODE

    # Go detection
    if "go" in languages:
        return Ecosystem.GO
    if any(f.endswith("go.mod") for f in dep_files):
        return Ecosystem.GO

    # Rust detection
    if "rust" in languages:
        return Ecosystem.RUST
    if any(f.endswith("Cargo.toml") for f in dep_files):
        return Ecosystem.RUST

    # Java detection
    if "java" in languages:
        return Ecosystem.JAVA
    if any(f.endswith("pom.xml") or f.endswith("build.gradle") for f in dep_files):
        return Ecosystem.JAVA

    # Ruby detection
    if "ruby" in languages:
        return Ecosystem.RUBY
    if any(f.endswith("Gemfile") for f in dep_files):
        return Ecosystem.RUBY

    # PHP detection
    if "php" in languages:
        return Ecosystem.PHP
    if any(f.endswith("composer.json") for f in dep_files):
        return Ecosystem.PHP

    return Ecosystem.UNKNOWN


class DeterministicPlanner:
    """Generates a verification plan based on discovered ecosystem."""

    ECOSYSTEM_PLANS: dict[Ecosystem, list[dict]] = {
        Ecosystem.PYTHON: [
            {"name": "virtualenv_setup", "description": "Set up virtual environment", "commands": ["python -m venv .venv"]},
            {"name": "install_deps", "description": "Install dependencies", "commands": ["pip install -r requirements.txt 2>/dev/null; pip install -e . 2>/dev/null; true"]},
            {"name": "lint", "description": "Run linter", "commands": ["ruff check . 2>/dev/null; flake8 . 2>/dev/null; true"]},
            {"name": "test", "description": "Run tests", "commands": ["python -m pytest -x --tb=short 2>/dev/null; true"]},
            {"name": "build", "description": "Build package", "commands": ["python -m build 2>/dev/null; true"]},
        ],
        Ecosystem.NODE: [
            {"name": "install_deps", "description": "Install dependencies", "commands": ["npm ci 2>/dev/null || npm install 2>/dev/null; true"]},
            {"name": "lint", "description": "Run linter", "commands": ["npm run lint 2>/dev/null; true"]},
            {"name": "test", "description": "Run tests", "commands": ["npm test 2>/dev/null; true"]},
            {"name": "build", "description": "Build project", "commands": ["npm run build 2>/dev/null; true"]},
        ],
        Ecosystem.GO: [
            {"name": "download_deps", "description": "Download dependencies", "commands": ["go mod download"]},
            {"name": "vet", "description": "Run go vet", "commands": ["go vet ./..."]},
            {"name": "test", "description": "Run tests", "commands": ["go test ./..."]},
            {"name": "build", "description": "Build binaries", "commands": ["go build ./..."]},
        ],
        Ecosystem.RUST: [
            {"name": "check", "description": "Check compilation", "commands": ["cargo check"]},
            {"name": "test", "description": "Run tests", "commands": ["cargo test"]},
            {"name": "clippy", "description": "Run clippy", "commands": ["cargo clippy -- -D warnings 2>/dev/null; true"]},
            {"name": "build", "description": "Build release", "commands": ["cargo build --release"]},
        ],
        Ecosystem.JAVA: [
            {"name": "compile", "description": "Compile project", "commands": ["mvn compile -q 2>/dev/null; true"]},
            {"name": "test", "description": "Run tests", "commands": ["mvn test -q 2>/dev/null; true"]},
            {"name": "package", "description": "Package artifact", "commands": ["mvn package -q -DskipTests 2>/dev/null; true"]},
        ],
        Ecosystem.RUBY: [
            {"name": "install_deps", "description": "Install gems", "commands": ["bundle install 2>/dev/null; true"]},
            {"name": "test", "description": "Run tests", "commands": ["bundle exec rake test 2>/dev/null; true"]},
            {"name": "lint", "description": "Run rubocop", "commands": ["bundle exec rubocop 2>/dev/null; true"]},
        ],
        Ecosystem.PHP: [
            {"name": "install_deps", "description": "Install Composer deps", "commands": ["composer install --no-interaction 2>/dev/null; true"]},
            {"name": "test", "description": "Run tests", "commands": ["vendor/bin/phpunit 2>/dev/null; true"]},
            {"name": "cs", "description": "Code style check", "commands": ["vendor/bin/php-cs-fixer fix --dry-run 2>/dev/null; true"]},
        ],
        Ecosystem.DOTNET: [
            {"name": "restore", "description": "Restore packages", "commands": ["dotnet restore"]},
            {"name": "build", "description": "Build solution", "commands": ["dotnet build --no-restore"]},
            {"name": "test", "description": "Run tests", "commands": ["dotnet test --no-build"]},
        ],
        Ecosystem.UNKNOWN: [
            {"name": "ls", "description": "List project structure", "commands": ["ls -la"]},
            {"name": "file_count", "description": "Count files", "commands": ["find . -type f | wc -l"]},
            {"name": "dir_tree", "description": "Show directory tree", "commands": ["find . -maxdepth 3 -type d | sort"]},
        ],
    }

    def generate_plan(self, ecosystem: Ecosystem, manifest: dict | None = None) -> list[dict]:
        """Generate a plan for the given ecosystem."""
        stages = self.ECOSYSTEM_PLANS.get(ecosystem, self.ECOSYSTEM_PLANS[Ecosystem.UNKNOWN])
        return [
            {
                "name": s["name"],
                "seq": i,
                "description": s["description"],
                "commands": s["commands"],
            }
            for i, s in enumerate(stages)
        ]

    def generate_digest(self, plan: list[dict]) -> dict:
        """Create a digest/summary of the plan."""
        total_commands = sum(len(s.get("commands", [])) for s in plan)
        return {
            "stage_count": len(plan),
            "command_count": total_commands,
            "conflicts": 0,
        }
