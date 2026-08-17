"""Discovery domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Optional


@dataclass
class ArchitectureManifest:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    project_root: str = ""
    entry_points: list[str] = field(default_factory=list)
    detected_frameworks: list[str] = field(default_factory=list)
    detected_languages: list[str] = field(default_factory=list)
    dependency_files: list[str] = field(default_factory=list)
    file_count: int = 0
    directory_structure: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DiscoveryClaim:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    claim_type: str = ""
    claim_value: str = ""
    confidence: float = 1.0
    source_file: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DiscoveryWarning:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    warning_type: str = ""
    message: str = ""
    severity: str = "info"
    source_file: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
