"""Migration 003: Repository discovery — manifests, claims, warnings, limits.

Adds tables: repository_manifests, discovery_claims, discovery_warnings, resource_limit_events.
Extends: repository_connections with additional columns.
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "003_discovery"
down_revision: Union[str, None] = "002_orchestration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── repository_manifests ─────────────────────────────
    op.create_table(
        "repository_manifests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("repository_connection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repository_connections.id"), nullable=True),
        sa.Column("manifest_version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("commit_sha", sa.String(64), nullable=False, server_default=""),
        sa.Column("owner", sa.String(255), nullable=False, server_default=""),
        sa.Column("repo", sa.String(255), nullable=False, server_default=""),
        sa.Column("branch", sa.String(255), nullable=False, server_default=""),
        sa.Column("manifest_data", sa.JSON, nullable=False, server_default="{}"),
        sa.Column("manifest_digest", sa.String(64), nullable=False, server_default=""),
        sa.Column("discovery_completeness", sa.String(20), nullable=False, server_default="PARTIAL"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_manifests_job", "repository_manifests", ["master_job_id"])
    op.create_index("ix_manifests_sha", "repository_manifests", ["commit_sha"])

    # ── discovery_claims ──────────────────────────────────
    op.create_table(
        "discovery_claims",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("manifest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repository_manifests.id"), nullable=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("claim_type", sa.String(50), nullable=False),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("source_file", sa.Text, nullable=False, server_default=""),
        sa.Column("detection_rule", sa.String(100), nullable=False, server_default=""),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="MODERATE"),
        sa.Column("execution_status", sa.String(30), nullable=False, server_default="STATIC_ONLY"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_claims_manifest_type", "discovery_claims", ["manifest_id", "claim_type"])
    op.create_index("ix_claims_job", "discovery_claims", ["master_job_id"])

    # ── discovery_warnings ───────────────────────────────
    op.create_table(
        "discovery_warnings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("manifest_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("repository_manifests.id"), nullable=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("warning_type", sa.String(50), nullable=False),
        sa.Column("finding_type", sa.String(100), nullable=False, server_default=""),
        sa.Column("file_path", sa.Text, nullable=False),
        sa.Column("line_reference", sa.String(100), nullable=False, server_default=""),
        sa.Column("fingerprint", sa.String(64), nullable=False, server_default=""),
        sa.Column("confidence", sa.String(20), nullable=False, server_default="LOW"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="WARNING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_warnings_manifest", "discovery_warnings", ["manifest_id"])
    op.create_index("ix_warnings_job", "discovery_warnings", ["master_job_id"])

    # ── resource_limit_events ────────────────────────────
    op.create_table(
        "resource_limit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("master_verification_jobs.id"), nullable=True),
        sa.Column("limit_name", sa.String(100), nullable=False),
        sa.Column("measured_value", sa.String(100), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_limits_job", "resource_limit_events", ["master_job_id"])

    # ── Extend repository_connections ────────────────────
    op.add_column("repository_connections", sa.Column("owner", sa.String(255), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("repo_name", sa.String(255), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("commit_sha", sa.String(64), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("commit_timestamp", sa.String(50), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("acquisition_timestamp", sa.String(50), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("discovery_timestamp", sa.String(50), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("repo_size_bytes", sa.Integer, nullable=False, server_default="0"))
    op.add_column("repository_connections", sa.Column("workspace_ref", sa.Text, nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("failure_classification", sa.String(50), nullable=False, server_default=""))
    op.add_column("repository_connections", sa.Column("failure_summary", sa.Text, nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("repository_connections", "failure_summary")
    op.drop_column("repository_connections", "failure_classification")
    op.drop_column("repository_connections", "workspace_ref")
    op.drop_column("repository_connections", "repo_size_bytes")
    op.drop_column("repository_connections", "discovery_timestamp")
    op.drop_column("repository_connections", "acquisition_timestamp")
    op.drop_column("repository_connections", "commit_timestamp")
    op.drop_column("repository_connections", "commit_sha")
    op.drop_column("repository_connections", "repo_name")
    op.drop_column("repository_connections", "owner")
    op.drop_index("ix_limits_job", table_name="resource_limit_events")
    op.drop_table("resource_limit_events")
    op.drop_index("ix_warnings_job", table_name="discovery_warnings")
    op.drop_index("ix_warnings_manifest", table_name="discovery_warnings")
    op.drop_table("discovery_warnings")
    op.drop_index("ix_claims_job", table_name="discovery_claims")
    op.drop_index("ix_claims_manifest_type", table_name="discovery_claims")
    op.drop_table("discovery_claims")
    op.drop_index("ix_manifests_sha", table_name="repository_manifests")
    op.drop_index("ix_manifests_job", table_name="repository_manifests")
    op.drop_table("repository_manifests")
