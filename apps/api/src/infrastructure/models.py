"""SQLAlchemy ORM models for all domain entities."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def new_id() -> str:
    return uuid4().hex


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id = Column(String(32), primary_key=True, default=new_id)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    projects = relationship("ProjectModel", back_populates="organization")


class UserModel(Base):
    __tablename__ = "users"

    id = Column(String(32), primary_key=True, default=new_id)
    org_id = Column(String(32), ForeignKey("organizations.id"), nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String(32), primary_key=True, default=new_id)
    org_id = Column(String(32), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    organization = relationship("OrganizationModel", back_populates="projects")


class RepositoryConnectionModel(Base):
    __tablename__ = "repository_connections"

    id = Column(String(32), primary_key=True, default=new_id)
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    url = Column(String(1024), nullable=False)
    status = Column(String(32), default="submitted", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class MasterVerificationJobModel(Base):
    __tablename__ = "master_verification_jobs"

    id = Column(String(32), primary_key=True, default=new_id)
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    repo_url = Column(String(1024), nullable=False)
    branch = Column(String(255), default="main")
    commit_hash = Column(String(64), default="")
    status = Column(String(32), default="created", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class VerificationStageModel(Base):
    __tablename__ = "verification_stages"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    stage_type = Column(String(64), nullable=False)
    status = Column(String(32), default="pending", nullable=False)
    applicability = Column(String(32), default="required")
    criticality = Column(String(32), default="required")
    seq = Column(Integer, default=0)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class StagePrerequisiteModel(Base):
    __tablename__ = "stage_prerequisites"

    id = Column(String(32), primary_key=True, default=new_id)
    stage_id = Column(String(32), ForeignKey("verification_stages.id"), nullable=False)
    prerequisite_stage_type = Column(String(64), nullable=False)


class VerificationCheckModel(Base):
    __tablename__ = "verification_checks"

    id = Column(String(32), primary_key=True, default=new_id)
    stage_id = Column(String(32), ForeignKey("verification_stages.id"), nullable=False)
    name = Column(String(255), nullable=False)
    passed = Column(Boolean, default=False)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    scope = Column(String(64), default="single_run")
    granted = Column(Boolean, default=False)
    granted_by = Column(String(255), nullable=True)
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EvidenceItemModel(Base):
    __tablename__ = "evidence_items"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), nullable=False)
    type = Column(String(64), default="")
    content = Column(Text, default="")
    source = Column(String(255), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FindingModel(Base):
    __tablename__ = "findings"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), nullable=False)
    severity = Column(String(16), default="medium")
    title = Column(String(255), default="")
    description = Column(Text, default="")
    location = Column(String(512), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RecommendationModel(Base):
    __tablename__ = "recommendations"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), nullable=False)
    finding_id = Column(String(32), nullable=False)
    title = Column(String(255), default="")
    description = Column(Text, default="")
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class VerificationRunModel(Base):
    __tablename__ = "verification_runs"

    id = Column(String(32), primary_key=True, default=new_id)
    project_id = Column(String(32), ForeignKey("projects.id"), nullable=False)
    lifecycle = Column(String(32), default="created", nullable=False)
    commit_hash = Column(String(64), default="")
    branch = Column(String(255), default="")
    error_classification = Column(String(64), nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)


class CheckpointModel(Base):
    __tablename__ = "checkpoints"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), ForeignKey("verification_runs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RunTransitionModel(Base):
    __tablename__ = "run_transitions"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), ForeignKey("verification_runs.id"), nullable=False)
    from_state = Column(String(32), nullable=False)
    to_state = Column(String(32), nullable=False)
    actor = Column(String(255), default="system")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AuditEventModel(Base):
    __tablename__ = "audit_events"

    id = Column(String(32), primary_key=True, default=new_id)
    run_id = Column(String(32), nullable=False)
    event_type = Column(String(64), default="")
    detail = Column(Text, default="")
    actor = Column(String(255), default="system")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
