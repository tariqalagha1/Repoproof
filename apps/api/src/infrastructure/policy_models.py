"""SQLAlchemy ORM for policy tables."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text

from .models import Base


def new_id() -> str:
    return uuid4().hex


class PolicyEvaluationModel(Base):
    __tablename__ = "policy_evaluations"

    id = Column(String(32), primary_key=True, default=new_id)
    master_job_id = Column(String(32), ForeignKey("master_verification_jobs.id"), nullable=False)
    overall_decision = Column(String(32), default="allow")
    risk_level = Column(String(32), default="none")
    requires_approval = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PolicyValidationResultModel(Base):
    __tablename__ = "policy_validation_results"

    id = Column(String(32), primary_key=True, default=new_id)
    evaluation_id = Column(String(32), ForeignKey("policy_evaluations.id"), nullable=False)
    master_job_id = Column(String(32), default="")
    rule_id = Column(String(32), default="")
    rule_name = Column(String(255), default="")
    area = Column(String(64), default="security")
    outcome = Column(String(32), default="pass")
    decision = Column(String(32), default="allow")
    message = Column(Text, default="")
    policy_version = Column(String(32), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PolicyRuleModel(Base):
    __tablename__ = "policy_rules"

    id = Column(String(32), primary_key=True, default=new_id)
    name = Column(String(255), default="")
    area = Column(String(64), default="security")
    description = Column(Text, default="")
    risk_level = Column(String(32), default="medium")
    enabled = Column(Integer, default=1)
    config = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class PolicyRestrictionModel(Base):
    __tablename__ = "policy_restrictions"

    id = Column(String(32), primary_key=True, default=new_id)
    result_id = Column(String(32), ForeignKey("policy_validation_results.id"), nullable=False)
    restriction_type = Column(String(32), default="network")
    description = Column(Text, default="")
    value = Column(String(512), default="")
    scope = Column(String(32), default="single_run")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
