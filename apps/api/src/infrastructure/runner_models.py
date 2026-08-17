"""SQLAlchemy ORM for runner environment tables."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text

from .models import Base


def new_id() -> str:
    return uuid4().hex


class RunnerEnvironmentModel(Base):
    __tablename__ = "runner_environments"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    stage_id = Column(String(32), default="")
    state = Column(String(32), default="created")
    container_id = Column(String(128), nullable=True)
    provider = Column(String(32), default="")
    provider_resource_id = Column(String(128), nullable=True)
    image = Column(String(512), default="")
    target_commit_sha = Column(String(64), default="")
    security_profile = Column(JSON, nullable=True)
    resource_limits = Column(JSON, nullable=True)
    source_attachment = Column(JSON, nullable=True)
    network_policy = Column(String(32), default="isolated")
    health_status = Column(String(32), default="")
    isolation_tests_passed = Column(Integer, default=0)
    isolation_tests_total = Column(Integer, default=0)
    idempotency_key = Column(String(64), default="")
    failure_reason = Column(String(64), nullable=True)
    failure_detail = Column(Text, nullable=True)
    provisioned_at = Column(DateTime, nullable=True)
    destroyed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class EnvironmentTransitionModel(Base):
    __tablename__ = "environment_transitions"

    id = Column(String(32), primary_key=True, default=new_id)
    environment_id = Column(String(32), ForeignKey("runner_environments.id"), nullable=False)
    from_state = Column(String(32), default="")
    to_state = Column(String(32), default="")
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class IsolationTestResultModel(Base):
    __tablename__ = "isolation_test_results"

    id = Column(String(32), primary_key=True, default=new_id)
    environment_id = Column(String(32), ForeignKey("runner_environments.id"), nullable=False)
    test_name = Column(String(255), default="")
    passed = Column(Integer, default=0)
    detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
