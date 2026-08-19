"""Policy Validation — Mission 005

Revision ID: 005_policy_validation
Create Date: 2026-07-26
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_spec in [
        ("policy_rules", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("rule_id", sa.String(20), nullable=False, index=True),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("category", sa.String(50), nullable=False),
            sa.Column("policy_area", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("severity", sa.String(20), nullable=False, server_default="high"),
            sa.Column("default_decision", sa.String(50), nullable=False, server_default="deny"),
            sa.Column("evaluation_fn_name", sa.String(100), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            ("ix_policy_rules_rule_version", ["rule_id", "version"]),
        ]),
        ("policy_evaluations", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
            sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),
            sa.Column("rule_id", sa.String(20), nullable=False),
            sa.Column("rule_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("policy_area", sa.String(50), nullable=False),
            sa.Column("plan_item_type", sa.String(50), nullable=False, server_default=""),
            sa.Column("plan_item_id", sa.String(64), nullable=False, server_default=""),
            sa.Column("decision", sa.String(50), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("evidence", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("risk_level", sa.String(20), nullable=False, server_default="informational"),
            sa.Column("required_restrictions", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("required_approval_scope", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ]),
        ("policy_restrictions", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),
            sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
            sa.Column("restriction_type", sa.String(50), nullable=False),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("applies_to_plan_item", sa.String(64), nullable=False, server_default=""),
            sa.Column("applies_to_stage", sa.String(50), nullable=False, server_default=""),
            sa.Column("value", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ]),
        ("policy_approval_requests", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id"), nullable=True),
            sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
            sa.Column("stage_id", sa.String(32), sa.ForeignKey("verification_stages.id"), nullable=True),
            sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),
            sa.Column("action_type", sa.String(100), nullable=False, server_default=""),
            sa.Column("reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("risk_level", sa.String(20), nullable=False, server_default="medium"),
            sa.Column("affected_commands", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("affected_services", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("network_destinations", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("secret_references", sa.JSON(), nullable=False, server_default="[]"),
            sa.Column("resource_limits", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("estimated_duration", sa.String(100), nullable=False, server_default=""),
            sa.Column("estimated_cost", sa.String(100), nullable=False, server_default=""),
            sa.Column("consequence_of_rejection", sa.Text(), nullable=False, server_default=""),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("requested_by", sa.String(100), nullable=False, server_default="policy_engine"),
            sa.Column("decided_by", sa.String(100), nullable=False, server_default=""),
            sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("decision_reason", sa.Text(), nullable=False, server_default=""),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ]),
        ("policy_validation_results", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),
            sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
            sa.Column("plan_digest", sa.String(64), nullable=False, server_default=""),
            sa.Column("manifest_digest", sa.String(64), nullable=False, server_default=""),
            sa.Column("locked_commit_sha", sa.String(64), nullable=False, server_default=""),
            sa.Column("policy_version", sa.String(20), nullable=False, server_default="1.0.0"),
            sa.Column("outcome", sa.String(50), nullable=False, server_default="blocked"),
            sa.Column("total_evaluations", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("allowed", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("allowed_with_restrictions", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("require_approval", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("denied", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("blocked", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("not_applicable", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("critical_risks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("high_risks", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_summary", sa.Text(), nullable=False, server_default=""),
            sa.Column("validated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ]),
        ("policy_audit_events", [
            sa.Column("id", sa.String(32), primary_key=True),
            sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id"), nullable=True),
            sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
            sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),
            sa.Column("action", sa.String(100), nullable=False, server_default=""),
            sa.Column("actor", sa.String(100), nullable=False, server_default="policy_engine"),
            sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        ]),
    ]:
        table_name = table_spec[0]
        columns = [c for c in table_spec[1] if isinstance(c, sa.Column)]
        op.create_table(table_name, *columns)
        for spec in table_spec[1]:
            if isinstance(spec, tuple) and len(spec) == 2:
                idx_name, idx_cols = spec
                op.create_index(idx_name, table_name, idx_cols)
        for spec in table_spec[1]:
            if isinstance(spec, tuple) and len(spec) == 2:
                pass  # already handled


def downgrade() -> None:
    for table in ["policy_audit_events", "policy_validation_results", "policy_approval_requests",
                   "policy_restrictions", "policy_evaluations", "policy_rules"]:
        op.drop_table(table)
