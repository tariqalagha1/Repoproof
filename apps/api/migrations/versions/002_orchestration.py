"""Migration 002: Master verification job orchestration.

Adds master_verification_jobs, verification_stages, stage_prerequisites,
verification_checks, approval_requests. Extends repository_connections,
evidence_items, findings, recommendations. Links verification_runs.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002_orchestration"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Extend repository_connections ──────────────────
    op.add_column("repository_connections", sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("repository_connections", sa.Column("repository_url", sa.Text, nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("normalized_url", sa.Text, nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("visibility", sa.String(20), nullable=False, server_default="unknown"))
    op.add_column("repository_connections", sa.Column("default_branch", sa.String(255), nullable=False, server_default="main"))
    op.add_column("repository_connections", sa.Column("selected_branch", sa.String(255), nullable=False, server_default="main"))
    op.add_column("repository_connections", sa.Column("resolved_commit_sha", sa.String(64), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("connection_status", sa.String(50), nullable=False, server_default="submitted"))
    op.add_column("repository_connections", sa.Column("authorization_status", sa.String(50), nullable=False, server_default="none"))
    op.add_column("repository_connections", sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_repo_connections_org", "repository_connections", ["organization_id"])
    op.create_index("ix_repo_connections_project", "repository_connections", ["project_id"])
    # Migrate existing url→repository_url data
    op.execute("UPDATE repository_connections SET repository_url = url WHERE repository_url = ''")

    # ── master_verification_jobs ─────────────────────────
    op.create_table(
        "master_verification_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("repository_connection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repository_connections.id"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="created"),
        sa.Column("current_stage_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("initial_authorization_scope", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("plan_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("orchestration_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("idempotency_key", sa.String(255), nullable=False, server_default=""),
        sa.Column("failure_summary", sa.Text, nullable=False, server_default=""),
        sa.Column("estimated_duration", sa.String(100), nullable=False, server_default=""),
        sa.Column("actual_duration", sa.String(100), nullable=False, server_default=""),
        sa.Column("estimated_cost", sa.String(100), nullable=False, server_default=""),
        sa.Column("actual_cost", sa.String(100), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paused_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_checkpoint_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("optimistic_concurrency_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("ix_master_jobs_org_status", "master_verification_jobs", ["organization_id", "status"])
    op.create_index("ix_master_jobs_repo_conn", "master_verification_jobs", ["repository_connection_id"])
    op.create_index("ix_master_jobs_idempotency", "master_verification_jobs", ["idempotency_key"])

    # ── verification_stages ──────────────────────────────
    op.create_table(
        "verification_stages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("stage_type", sa.String(50), nullable=False),
        sa.Column("sequence_number", sa.Integer, nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("applicability", sa.String(50), nullable=False, server_default="required"),
        sa.Column("criticality", sa.String(50), nullable=False, server_default="required"),
        sa.Column("execution_policy", sa.String(50), nullable=False, server_default="sequential"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("maximum_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_reason", sa.Text, nullable=False, server_default=""),
        sa.Column("failure_classification", sa.String(50), nullable=True),
        sa.Column("estimated_duration", sa.String(100), nullable=False, server_default=""),
        sa.Column("actual_duration", sa.String(100), nullable=False, server_default=""),
        sa.Column("estimated_cost", sa.String(100), nullable=False, server_default=""),
        sa.Column("actual_cost", sa.String(100), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("optimistic_concurrency_version", sa.Integer, nullable=False, server_default="1"),
    )
    op.create_index("ix_stages_job_seq", "verification_stages", ["master_job_id", "sequence_number"])
    op.create_index("ix_stages_type", "verification_stages", ["stage_type"])

    # ── stage_prerequisites ───────────────────────────────
    op.create_table(
        "stage_prerequisites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verification_stages.id"), nullable=True),
        sa.Column("prerequisite_stage_type", sa.String(50), nullable=False),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_prereq_stage", "stage_prerequisites", ["stage_id"])

    # ── verification_checks ───────────────────────────────
    op.create_table(
        "verification_checks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verification_stages.id"), nullable=True),
        sa.Column("check_key", sa.String(100), nullable=False, server_default=""),
        sa.Column("check_version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("category", sa.String(100), nullable=False, server_default=""),
        sa.Column("name", sa.String(255), nullable=False, server_default=""),
        sa.Column("description", sa.Text, nullable=False, server_default=""),
        sa.Column("sequence_number", sa.Integer, nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("execution_type", sa.String(50), nullable=False, server_default="not_proven"),
        sa.Column("criticality", sa.String(50), nullable=False, server_default="required"),
        sa.Column("expected_result", sa.Text, nullable=False, server_default=""),
        sa.Column("actual_result_summary", sa.Text, nullable=False, server_default=""),
        sa.Column("exit_code", sa.Integer, nullable=True),
        sa.Column("evidence_classification", sa.String(50), nullable=False, server_default="not_proven"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("maximum_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_reason", sa.Text, nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_checks_stage_seq", "verification_checks", ["stage_id", "sequence_number"])

    # ── approval_requests ─────────────────────────────────
    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("stage_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("verification_stages.id"), nullable=True),
        sa.Column("action_type", sa.String(100), nullable=False),
        sa.Column("requested_scope", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("reason", sa.Text, nullable=False, server_default=""),
        sa.Column("risk_level", sa.String(20), nullable=False, server_default="low"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("decided_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decision_reason", sa.Text, nullable=False, server_default=""),
    )
    op.create_index("ix_approval_reqs_job", "approval_requests", ["master_job_id"])

    # ── Extend evidence_items ─────────────────────────────
    op.add_column("evidence_items", sa.Column("master_job_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("evidence_items", sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("evidence_items", sa.Column("check_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("evidence_items", sa.Column("evidence_classification", sa.String(50), nullable=False, server_default="not_proven"))

    # ── Extend findings ───────────────────────────────────
    op.add_column("findings", sa.Column("master_job_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("findings", sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("findings", sa.Column("check_id", postgresql.UUID(as_uuid=True), nullable=True))

    # ── Extend recommendations ────────────────────────────
    op.add_column("recommendations", sa.Column("master_job_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("recommendations", sa.Column("stage_id", postgresql.UUID(as_uuid=True), nullable=True))

    # ── Link verification_runs to master_jobs ─────────────
    op.add_column("verification_runs", sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True))


def downgrade() -> None:
    # Remove extended columns
    op.drop_column("verification_runs", "master_job_id")
    op.drop_column("recommendations", "stage_id")
    op.drop_column("recommendations", "master_job_id")
    op.drop_column("findings", "check_id")
    op.drop_column("findings", "stage_id")
    op.drop_column("findings", "master_job_id")
    op.drop_column("evidence_items", "evidence_classification")
    op.drop_column("evidence_items", "check_id")
    op.drop_column("evidence_items", "stage_id")
    op.drop_column("evidence_items", "master_job_id")

    # Drop new tables
    op.drop_table("approval_requests")
    op.drop_index("ix_checks_stage_seq", table_name="verification_checks")
    op.drop_table("verification_checks")
    op.drop_index("ix_prereq_stage", table_name="stage_prerequisites")
    op.drop_table("stage_prerequisites")
    op.drop_index("ix_stages_type", table_name="verification_stages")
    op.drop_index("ix_stages_job_seq", table_name="verification_stages")
    op.drop_table("verification_stages")
    op.drop_index("ix_master_jobs_idempotency", table_name="master_verification_jobs")
    op.drop_index("ix_master_jobs_repo_conn", table_name="master_verification_jobs")
    op.drop_index("ix_master_jobs_org_status", table_name="master_verification_jobs")
    op.drop_table("master_verification_jobs")

    # Drop extended repository_connection columns
    op.drop_index("ix_repo_connections_project", table_name="repository_connections")
    op.drop_index("ix_repo_connections_org", table_name="repository_connections")
    op.drop_column("repository_connections", "created_by")
    op.drop_column("repository_connections", "authorization_status")
    op.drop_column("repository_connections", "connection_status")
    op.drop_column("repository_connections", "resolved_commit_sha")
    op.drop_column("repository_connections", "selected_branch")
    op.drop_column("repository_connections", "default_branch")
    op.drop_column("repository_connections", "visibility")
    op.drop_column("repository_connections", "normalized_url")
    op.drop_column("repository_connections", "repository_url")
    op.drop_column("repository_connections", "organization_id")
