"""SQLAlchemy ORM for discovery tables."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text

from .models import Base


def new_id() -> str:
    return uuid4().hex


class ArchitectureManifestModel(Base):
    __tablename__ = "architecture_manifests"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    project_root = Column(String(512), default="")
    entry_points = Column(Text, default="[]")
    detected_frameworks = Column(Text, default="[]")
    detected_languages = Column(Text, default="[]")
    dependency_files = Column(Text, default="[]")
    file_count = Column(Integer, default=0)
    directory_structure = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DiscoveryClaimModel(Base):
    __tablename__ = "discovery_claims"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    claim_type = Column(String(64), default="")
    claim_value = Column(String(512), default="")
    confidence = Column(Float, default=1.0)
    source_file = Column(String(512), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DiscoveryWarningModel(Base):
    __tablename__ = "discovery_warnings"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    warning_type = Column(String(64), default="")
    message = Column(Text, default="")
    severity = Column(String(16), default="info")
    source_file = Column(String(512), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
