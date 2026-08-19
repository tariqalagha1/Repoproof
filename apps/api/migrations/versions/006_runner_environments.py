"""Mission 006 — Runner environment tables.

Creates:
- runner_environments (durable provisioning records)
- environment_transitions (lifecycle audit log)
- isolation_test_results (per-test results)

Revision ID: 006
Revises: 005
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Runner environments
    op.create_table(
        "runner_environments",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("organization_id", sa.String(32), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("master_job_id", sa.String(32), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("stage_id", sa.String(32), sa.ForeignKey("verification_stages.id"), nullable=True),
        sa.Column("tenant_id", sa.String(32), nullable=True),
        sa.Column("plan_id", sa.String(32), sa.ForeignKey("verification_plans.id"), nullable=True),

        # Provider
        sa.Column("provider", sa.String(50), nullable=False, server_default="docker"),
        sa.Column("provider_resource_id", sa.String(255), nullable=False, server_default=""),
        sa.Column("environment_name", sa.String(255), nullable=False, server_default=""),

        # Pipeline identity
        sa.Column("target_commit_sha", sa.String(64), nullable=False, server_default=""),
        sa.Column("manifest_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("plan_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("policy_validation_id", sa.String(32), nullable=False, server_default=""),

        # State
        sa.Column("state", sa.String(50), nullable=False, server_default="provision_requested"),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("failure_classification", sa.String(50), nullable=False, server_default="none"),
        sa.Column("error_detail", sa.Text, nullable=False, server_default=""),

        # Security
        sa.Column("security_profile_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("security_profile", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("network_policy", sa.String(50), nullable=False, server_default="default_deny"),
        sa.Column("network_policy_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("resource_limits", sa.JSON, nullable=False, server_default="{}"),

        # Runner image
        sa.Column("runner_image", sa.String(255), nullable=False, server_default="repoproof-runner:latest"),
        sa.Column("runner_image_digest", sa.String(128), nullable=False, server_default=""),

        # Source
        sa.Column("source_attachment", sa.JSON, nullable=False, server_default="{}"),

        # Health
        sa.Column("health_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("non_root_uid", sa.Integer, nullable=False, server_default="0"),
        sa.Column("capabilities_dropped", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("isolation_tests_passed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("isolation_tests_total", sa.Integer, nullable=False, server_default="0"),

        # Timestamps
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("provisioned_at", sa.DateTime, nullable=True),
        sa.Column("ready_at", sa.DateTime, nullable=True),
        sa.Column("paused_at", sa.DateTime, nullable=True),
        sa.Column("stopped_at", sa.DateTime, nullable=True),
        sa.Column("destroyed_at", sa.DateTime, nullable=True),
        sa.Column("expiry_at", sa.DateTime, nullable=True),

        # Durability
        sa.Column("idempotency_key", sa.String(255), nullable=False, server_default=""),
        sa.Column("checkpoint_metadata", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("optimistic_concurrency_version", sa.Integer, nullable=False, server_default="1"),

        # Constraints
        sa.UniqueConstraint("master_job_id", "idempotency_key", name="uq_env_idempotency"),
    )

    # Indexes
    op.create_index("ix_env_master_job", "runner_environments", ["master_job_id"])
    op.create_index("ix_env_tenant", "runner_environments", ["tenant_id"])
    op.create_index("ix_env_state", "runner_environments", ["state"])
    op.create_index("ix_env_provider_resource", "runner_environments", ["provider_resource_id"])
    op.create_index("ix_env_target_sha", "runner_environments", ["target_commit_sha"])
    op.create_index("ix_env_plan_digest", "runner_environments", ["plan_digest"])
    op.create_index("ix_env_idempotency", "runner_environments", ["idempotency_key"])

    # Environment transitions
    op.create_table(
        "environment_transitions",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("environment_id", sa.String(32), sa.ForeignKey("runner_environments.id"), nullable=False),
        sa.Column("from_state", sa.String(50), nullable=False),
        sa.Column("to_state", sa.String(50), nullable=False),
        sa.Column("reason", sa.Text, nullable=False, server_default=""),
        sa.Column("actor_id", sa.String(32), nullable=True),
        sa.Column("checkpoint_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("transitioned_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_env_trans_env", "environment_transitions", ["environment_id"])

    # Isolation test results
    op.create_table(
        "isolation_test_results",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("environment_id", sa.String(32), sa.ForeignKey("runner_environments.id"), nullable=False),
        sa.Column("test_name", sa.String(100), nullable=False),
        sa.Column("passed", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("detail", sa.Text, nullable=False, server_default=""),
        sa.Column("evidence", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_index("ix_iso_env", "isolation_test_results", ["environment_id"])


def downgrade() -> None:
    op.drop_table("isolation_test_results")
    op.drop_table("environment_transitions")
    op.drop_table("runner_environments")
