"""SQLAlchemy ORM for plan tables."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .models import Base


def new_id() -> str:
    return uuid4().hex


class VerificationPlanModel(Base):
    __tablename__ = "verification_plans"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    ecosystem = Column(String(32), default="unknown")
    status = Column(String(32), default="draft")
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PlanStageModel(Base):
    __tablename__ = "plan_stages"

    id = Column(String(32), primary_key=True, default=new_id)
    plan_id = Column(String(32), ForeignKey("verification_plans.id"), nullable=False)
    name = Column(String(255), default="")
    seq = Column(Integer, default=0)
    description = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CommandSpecificationModel(Base):
    __tablename__ = "command_specifications"

    id = Column(String(32), primary_key=True, default=new_id)
    plan_stage_id = Column(String(32), ForeignKey("plan_stages.id"), nullable=False)
    command = Column(Text, default="")
    source = Column(String(32), default="deterministic")
    confidence = Column(String(32), default="medium")
    execution_status = Column(String(32), default="pending")
    timeout_seconds = Column(Integer, default=300)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PlanConflictModel(Base):
    __tablename__ = "plan_conflicts"

    id = Column(String(32), primary_key=True, default=new_id)
    plan_id = Column(String(32), ForeignKey("verification_plans.id"), nullable=False)
    description = Column(Text, default="")
    resolution = Column(Text, nullable=True)
    resolved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
