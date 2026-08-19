"""Plan generation — Mission 004

Revision ID: 004_plan_generation
Create Date: 2026-07-23

Adds all plan-related tables:
  - verification_plans
  - plan_versions
  - planned_stages, planned_checks
  - command_specifications
  - planned_services, planned_dependencies
  - plan_conflicts, decision_requests
  - llm_planning_attempts, grounding_results
  - plan_artifacts
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "004"
down_revision: Union[str, None] = "003_discovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── verification_plans ──────────────────────────────
    op.create_table(
        "verification_plans",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("project_id", sa.String(32), sa.ForeignKey("projects.id"), nullable=True),
        sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("repository_connection_id", sa.String(32), sa.ForeignKey("repository_connections.id"), nullable=True),
        sa.Column("repository_url", sa.Text(), nullable=False, server_default=""),
        sa.Column("locked_commit_sha", sa.String(64), nullable=False, server_default=""),
        sa.Column("manifest_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("manifest_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="deterministic"),
        sa.Column("plan_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("planner_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("planning_rules_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("llm_provider", sa.String(50), nullable=False, server_default=""),
        sa.Column("llm_model", sa.String(100), nullable=False, server_default=""),
        sa.Column("prompt_version", sa.String(20), nullable=False, server_default=""),
        sa.Column("error_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("generation_timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index("ix_plans_job_version", "verification_plans", ["master_job_id", "version"])
    op.create_index("ix_plans_status", "verification_plans", ["status"])
    op.create_index("ix_plans_project", "verification_plans", ["project_id"])

    # ── plan_versions ───────────────────────────────────
    op.create_table(
        "plan_versions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("plan_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("plan_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_plan_versions_plan_version", "plan_versions", ["plan_id", "version"], unique=True)

    # ── planned_stages ──────────────────────────────────
    op.create_table(
        "planned_stages",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("stage_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("applicability", sa.String(50), nullable=False, server_default="required"),
        sa.Column("criticality", sa.String(50), nullable=False, server_default="required"),
        sa.Column("stage_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_planned_stages_plan", "planned_stages", ["plan_id"])

    # ── planned_checks ──────────────────────────────────
    op.create_table(
        "planned_checks",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("stage_id", sa.String(32), sa.ForeignKey("planned_stages.id"), nullable=True),
        sa.Column("stage_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("check_key", sa.String(100), nullable=False, server_default=""),
        sa.Column("check_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("check_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_planned_checks_plan", "planned_checks", ["plan_id"])

    # ── command_specifications ──────────────────────────
    op.create_table(
        "command_specifications",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("stage_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("check_key", sa.String(100), nullable=False, server_default=""),
        sa.Column("ecosystem", sa.String(50), nullable=False, server_default=""),
        sa.Column("purpose", sa.Text(), nullable=False, server_default=""),
        sa.Column("executable", sa.String(100), nullable=False, server_default=""),
        sa.Column("arguments", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("working_directory", sa.String(255), nullable=False, server_default="."),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("source_reference", sa.Text(), nullable=False, server_default=""),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="unknown"),
        sa.Column("inferred_or_explicit", sa.String(20), nullable=False, server_default="inferred"),
        sa.Column("environment_variable_names", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("secret_reference_names", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("allowed_network_destinations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("requires_network", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="300"),
        sa.Column("cpu_limit", sa.String(20), nullable=False, server_default="1"),
        sa.Column("memory_limit", sa.String(20), nullable=False, server_default="512Mi"),
        sa.Column("disk_limit", sa.String(20), nullable=False, server_default="1Gi"),
        sa.Column("expected_exit_codes", postgresql.JSONB(), nullable=False, server_default="[0]"),
        sa.Column("output_capture_policy", sa.String(50), nullable=False, server_default="capture"),
        sa.Column("redaction_policy", sa.String(50), nullable=False, server_default="redact_secrets"),
        sa.Column("lifecycle_script_risk", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("destructive_risk", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("privilege_requirement", sa.String(50), nullable=False, server_default="none"),
        sa.Column("approval_requirement", sa.String(50), nullable=False, server_default="not_yet_known"),
        sa.Column("execution_status", sa.String(50), nullable=False, server_default="not_executed"),
        sa.Column("sequence_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_cmd_specs_plan", "command_specifications", ["plan_id"])

    # ── planned_services ────────────────────────────────
    op.create_table(
        "planned_services",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("service_identifier", sa.String(255), nullable=False, server_default=""),
        sa.Column("service_type", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("service_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_planned_svcs_plan", "planned_services", ["plan_id"])

    # ── planned_dependencies ────────────────────────────
    op.create_table(
        "planned_dependencies",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("ecosystem", sa.String(50), nullable=False, server_default=""),
        sa.Column("manifest", sa.String(255), nullable=False, server_default=""),
        sa.Column("lock_file", sa.String(255), nullable=False, server_default=""),
        sa.Column("package_manager", sa.String(50), nullable=False, server_default=""),
        sa.Column("dependency_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_planned_deps_plan", "planned_dependencies", ["plan_id"])

    # ── plan_conflicts ──────────────────────────────────
    op.create_table(
        "plan_conflicts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("conflict_type", sa.String(50), nullable=False, server_default="other"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("options", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("recommended", sa.Text(), nullable=False, server_default=""),
        sa.Column("severity", sa.String(20), nullable=False, server_default="warning"),
        sa.Column("blocking", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_plan_conflicts_plan", "plan_conflicts", ["plan_id"])

    # ── decision_requests ───────────────────────────────
    op.create_table(
        "decision_requests",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False, server_default=""),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("available_evidence", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("options", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("risk_of_each_option", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("default_option", sa.Text(), nullable=False, server_default=""),
        sa.Column("planning_can_continue", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("answer", sa.Text(), nullable=False, server_default=""),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_decision_reqs_plan", "decision_requests", ["plan_id"])

    # ── llm_planning_attempts ───────────────────────────
    op.create_table(
        "llm_planning_attempts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False, server_default=""),
        sa.Column("model", sa.String(100), nullable=False, server_default=""),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=False, server_default="1.0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("token_usage", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("suggestions_accepted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("suggestions_rejected", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("block_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_llm_attempts_plan", "llm_planning_attempts", ["plan_id"])

    # ── grounding_results ───────────────────────────────
    op.create_table(
        "grounding_results",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("item_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("item_id", sa.String(64), nullable=True),
        sa.Column("decision", sa.String(50), nullable=False, server_default="requires_confirmation"),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("source_reference_exists", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("manifest_digest_match", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("confidence_appropriate", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("prohibited_patterns", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_grounding_plan", "grounding_results", ["plan_id"])

    # ── plan_artifacts ──────────────────────────────────
    op.create_table(
        "plan_artifacts",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=False),
        sa.Column("artifact_type", sa.String(50), nullable=False, server_default=""),
        sa.Column("artifact_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_plan_artifacts_plan", "plan_artifacts", ["plan_id"])


def downgrade() -> None:
    op.drop_table("plan_artifacts")
    op.drop_table("grounding_results")
    op.drop_table("llm_planning_attempts")
    op.drop_table("decision_requests")
    op.drop_table("plan_conflicts")
    op.drop_table("planned_dependencies")
    op.drop_table("planned_services")
    op.drop_table("command_specifications")
    op.drop_table("planned_checks")
    op.drop_table("planned_stages")
    op.drop_table("plan_versions")
    op.drop_table("verification_plans")
