"""initial storage: repositories, snapshots, analysis runs, jobs, artifacts and evidence

Revision ID: 0001
Revises:
Create Date: 2026-10-22 15:06:13.981962
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

LEASE_ONLY_WHILE_RUNNING = (
    "CASE WHEN status = 'running' THEN lease_token IS NOT NULL"
    " AND heartbeat_at IS NOT NULL AND lease_expires_at IS NOT NULL"
    " ELSE lease_token IS NULL AND heartbeat_at IS NULL AND lease_expires_at IS NULL END"
)


def upgrade() -> None:
    op.create_table(
        "artifact_objects",
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "length(content_hash) = 71 AND substr(content_hash, 1, 7) = 'sha256:'",
            name=op.f("ck_artifact_objects_content_hash_format"),
        ),
        sa.CheckConstraint("size >= 0", name=op.f("ck_artifact_objects_size_non_negative")),
        sa.PrimaryKeyConstraint("content_hash", name=op.f("pk_artifact_objects")),
    )
    op.create_table(
        "repositories",
        sa.Column("repository_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column(
            "source",
            sa.Enum(
                "local_git", name="repository_source", native_enum=False, create_constraint=True
            ),
            nullable=False,
        ),
        sa.Column("allowed_root", sa.String(length=4096), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("repository_id", name=op.f("pk_repositories")),
        sa.UniqueConstraint("allowed_root", name=op.f("uq_repositories_allowed_root")),
    )
    op.create_table(
        "snapshots",
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=64), nullable=False),
        sa.Column("commit_sha", sa.String(length=40), nullable=False),
        sa.Column("tree_sha", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.repository_id"],
            name=op.f("fk_snapshots_repository_id_repositories"),
        ),
        sa.PrimaryKeyConstraint("snapshot_id", name=op.f("pk_snapshots")),
        sa.UniqueConstraint(
            "repository_id", "commit_sha", name=op.f("uq_snapshots_repository_id_commit_sha")
        ),
        sa.UniqueConstraint(
            "snapshot_id", "repository_id", name=op.f("uq_snapshots_snapshot_id_repository_id")
        ),
    )
    op.create_table(
        "analysis_runs",
        sa.Column("analysis_run_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("identity_key", sa.String(length=71), nullable=False),
        sa.Column(
            "language",
            sa.Enum(
                "vue-typescript", name="target_language", native_enum=False, create_constraint=True
            ),
            nullable=False,
        ),
        sa.Column("parser_version", sa.String(length=128), nullable=False),
        sa.Column("rule_set_version", sa.String(length=128), nullable=False),
        sa.Column("config_hash", sa.String(length=71), nullable=False),
        sa.Column("pipeline_version", sa.String(length=128), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=True),
        sa.Column("prompt_version", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "(model_version IS NULL) = (prompt_version IS NULL)",
            name=op.f("ck_analysis_runs_model_prompt_pair"),
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["snapshots.snapshot_id"],
            name=op.f("fk_analysis_runs_snapshot_id_snapshots"),
        ),
        sa.PrimaryKeyConstraint("analysis_run_id", name=op.f("pk_analysis_runs")),
        sa.UniqueConstraint(
            "analysis_run_id",
            "snapshot_id",
            name=op.f("uq_analysis_runs_analysis_run_id_snapshot_id"),
        ),
        sa.UniqueConstraint("identity_key", name=op.f("uq_analysis_runs_identity_key")),
    )
    op.create_table(
        "evidence",
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column(
            "type",
            sa.Enum(
                "code",
                "commit",
                "human_answer",
                name="evidence_type",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("locator", sa.JSON(), nullable=False),
        sa.Column("locator_key", sa.String(length=71), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("captured_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["content_hash"],
            ["artifact_objects.content_hash"],
            name=op.f("fk_evidence_content_hash_artifact_objects"),
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id"],
            ["snapshots.snapshot_id"],
            name=op.f("fk_evidence_snapshot_id_snapshots"),
        ),
        sa.PrimaryKeyConstraint("evidence_id", name=op.f("pk_evidence")),
        sa.UniqueConstraint(
            "snapshot_id",
            "locator_key",
            "content_hash",
            name=op.f("uq_evidence_snapshot_id_locator_key_content_hash"),
        ),
    )
    op.create_table(
        "analysis_artifacts",
        sa.Column("artifact_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=64), nullable=False),
        sa.Column(
            "stage",
            sa.Enum(
                "snapshot",
                "parse",
                "graph",
                "rank",
                "rules",
                "evidence",
                "generate",
                name="job_stage",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("content_hash", sa.String(length=71), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_run_id"],
            ["analysis_runs.analysis_run_id"],
            name=op.f("fk_analysis_artifacts_analysis_run_id_analysis_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["content_hash"],
            ["artifact_objects.content_hash"],
            name=op.f("fk_analysis_artifacts_content_hash_artifact_objects"),
        ),
        sa.PrimaryKeyConstraint("artifact_id", name=op.f("pk_analysis_artifacts")),
        sa.UniqueConstraint(
            "analysis_run_id",
            "stage",
            "name",
            name=op.f("uq_analysis_artifacts_analysis_run_id_stage_name"),
        ),
    )
    op.create_table(
        "jobs",
        sa.Column("job_id", sa.String(length=64), nullable=False),
        sa.Column("repository_id", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("request_hash", sa.String(length=71), nullable=False),
        sa.Column("requested_ref", sa.String(length=255), nullable=False),
        sa.Column("snapshot_id", sa.String(length=64), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "succeeded",
                "partial",
                "failed",
                "cancelled",
                name="job_status",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "stage",
            sa.Enum(
                "snapshot",
                "parse",
                "graph",
                "rank",
                "rules",
                "evidence",
                "generate",
                name="job_stage",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("lease_token", sa.String(length=128), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(), nullable=True),
        sa.Column("progress", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("error", sa.JSON(none_as_null=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            LEASE_ONLY_WHILE_RUNNING,
            name=op.f("ck_jobs_lease_only_while_running"),
        ),
        sa.CheckConstraint(
            "attempt >= 0 AND max_attempts >= 1 AND attempt <= max_attempts",
            name=op.f("ck_jobs_attempt_bounds"),
        ),
        sa.ForeignKeyConstraint(
            ["analysis_run_id", "snapshot_id"],
            ["analysis_runs.analysis_run_id", "analysis_runs.snapshot_id"],
            name=op.f("fk_jobs_analysis_run_id_snapshot_id_analysis_runs"),
        ),
        sa.ForeignKeyConstraint(
            ["snapshot_id", "repository_id"],
            ["snapshots.snapshot_id", "snapshots.repository_id"],
            name=op.f("fk_jobs_snapshot_id_repository_id_snapshots"),
        ),
        sa.PrimaryKeyConstraint("job_id", name=op.f("pk_jobs")),
        sa.UniqueConstraint(
            "repository_id", "idempotency_key", name=op.f("uq_jobs_repository_id_idempotency_key")
        ),
    )


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("analysis_artifacts")
    op.drop_table("evidence")
    op.drop_table("analysis_runs")
    op.drop_table("snapshots")
    op.drop_table("repositories")
    op.drop_table("artifact_objects")
