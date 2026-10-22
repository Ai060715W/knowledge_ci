"""Tables for repositories, snapshots, analysis runs, jobs, artifacts and evidence.

Columns mirror the T02 contracts field by field, so stores convert rows with
``Contract.model_validate(row, from_attributes=True)``. The database repeats the identity,
reference and lease rules that a direct SQL write could otherwise break.
"""

import secrets
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    Dialect,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    MetaData,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from knowledge_ci.contracts.common import ContractModel
from knowledge_ci.contracts.evidence import EvidenceType
from knowledge_ci.contracts.jobs import JobStage, JobStatus
from knowledge_ci.contracts.repository import RepositorySource, TargetLanguage

# Upper bounds of the contract string types; SQLite ignores them, PostgreSQL enforces them.
ID_LENGTH = 64
HASH_LENGTH = 71  # "sha256:" + 64 hex
SHA_LENGTH = 40
VERSION_LENGTH = 128
LABEL_LENGTH = 500
REF_LENGTH = 255
KEY_LENGTH = 128
LOCAL_ROOT_LENGTH = 4096
ARTIFACT_NAME_LENGTH = 128

# Stable constraint names keep later batch migrations (table rebuilds on SQLite) predictable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class UtcDateTime(TypeDecorator[datetime]):
    """Aware datetimes only: stored as naive UTC, returned with tzinfo=UTC."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        if value is None:
            return None
        if value.utcoffset() is None:
            raise ValueError("naive datetimes are not stored; pass a UTC-aware value")
        return value.astimezone(UTC).replace(tzinfo=None)

    def process_result_value(self, value: datetime | None, dialect: Dialect) -> datetime | None:
        return None if value is None else value.replace(tzinfo=UTC)


def _enum(enum: type[StrEnum], name: str) -> Enum:
    """Contract value in a string column with a CHECK constraint; adding a member needs a
    migration."""
    return Enum(
        enum,
        name=name,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [member.value for member in members],
    )


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
    type_annotation_map: ClassVar[dict[Any, Any]] = {datetime: UtcDateTime()}


class IdPrefix(StrEnum):
    REPOSITORY = "repo"
    SNAPSHOT = "snap"
    ANALYSIS_RUN = "run"
    JOB = "job"
    EVIDENCE = "ev"
    ARTIFACT = "art"


def new_id(prefix: IdPrefix) -> str:
    """Opaque contract Id: a readable prefix and 128 random bits, e.g. "job_3f2a…"."""
    return f"{prefix}_{secrets.token_hex(16)}"


def row_values(model: ContractModel, *json_fields: str) -> dict[str, Any]:
    """Contract fields as column values; nested models in json_fields become JSON data."""
    values = model.model_dump()
    values.update(model.model_dump(mode="json", include=set(json_fields)))
    return values


class RepositoryRow(Base):
    __tablename__ = "repositories"
    __table_args__ = (UniqueConstraint("allowed_root"),)

    repository_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    name: Mapped[str] = mapped_column(String(LABEL_LENGTH))
    source: Mapped[RepositorySource] = mapped_column(_enum(RepositorySource, "repository_source"))
    # The only machine path in the database; business references use repository paths.
    allowed_root: Mapped[str] = mapped_column(String(LOCAL_ROOT_LENGTH))
    created_at: Mapped[datetime]


class SnapshotRow(Base):
    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("repository_id", "commit_sha"),
        # Target of the composite key that keeps a job's snapshot in the job's repository.
        UniqueConstraint("snapshot_id", "repository_id"),
    )

    snapshot_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    repository_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("repositories.repository_id")
    )
    commit_sha: Mapped[str] = mapped_column(String(SHA_LENGTH))
    tree_sha: Mapped[str] = mapped_column(String(SHA_LENGTH))
    created_at: Mapped[datetime]


class AnalysisRunRow(Base):
    __tablename__ = "analysis_runs"
    __table_args__ = (
        UniqueConstraint("identity_key"),
        # Target of the composite key that keeps a job's run on the job's snapshot.
        UniqueConstraint("analysis_run_id", "snapshot_id"),
        CheckConstraint(
            "(model_version IS NULL) = (prompt_version IS NULL)", name="model_prompt_pair"
        ),
    )

    analysis_run_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("snapshots.snapshot_id"))
    # AnalysisRun.identity_key(): the snapshot plus every version and the config hash.
    identity_key: Mapped[str] = mapped_column(String(HASH_LENGTH))
    language: Mapped[TargetLanguage] = mapped_column(_enum(TargetLanguage, "target_language"))
    parser_version: Mapped[str] = mapped_column(String(VERSION_LENGTH))
    rule_set_version: Mapped[str] = mapped_column(String(VERSION_LENGTH))
    config_hash: Mapped[str] = mapped_column(String(HASH_LENGTH))
    pipeline_version: Mapped[str] = mapped_column(String(VERSION_LENGTH))
    model_version: Mapped[str | None] = mapped_column(String(VERSION_LENGTH))
    prompt_version: Mapped[str | None] = mapped_column(String(VERSION_LENGTH))
    created_at: Mapped[datetime]


class JobRow(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("repository_id", "idempotency_key"),
        # Job, snapshot and run always belong to one repository chain.
        ForeignKeyConstraint(
            ["snapshot_id", "repository_id"],
            ["snapshots.snapshot_id", "snapshots.repository_id"],
        ),
        ForeignKeyConstraint(
            ["analysis_run_id", "snapshot_id"],
            ["analysis_runs.analysis_run_id", "analysis_runs.snapshot_id"],
        ),
        CheckConstraint(
            "attempt >= 0 AND max_attempts >= 1 AND attempt <= max_attempts",
            name="attempt_bounds",
        ),
        CheckConstraint(
            "CASE WHEN status = 'running' THEN lease_token IS NOT NULL"
            " AND heartbeat_at IS NOT NULL AND lease_expires_at IS NOT NULL"
            " ELSE lease_token IS NULL AND heartbeat_at IS NULL AND lease_expires_at IS NULL END",
            name="lease_only_while_running",
        ),
    )

    job_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    repository_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    idempotency_key: Mapped[str] = mapped_column(String(KEY_LENGTH))
    request_hash: Mapped[str] = mapped_column(String(HASH_LENGTH))
    requested_ref: Mapped[str] = mapped_column(String(REF_LENGTH))
    snapshot_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    analysis_run_id: Mapped[str] = mapped_column(String(ID_LENGTH))
    status: Mapped[JobStatus] = mapped_column(_enum(JobStatus, "job_status"))
    stage: Mapped[JobStage] = mapped_column(_enum(JobStage, "job_stage"))
    attempt: Mapped[int]
    max_attempts: Mapped[int]
    lease_token: Mapped[str | None] = mapped_column(String(KEY_LENGTH))
    heartbeat_at: Mapped[datetime | None]
    lease_expires_at: Mapped[datetime | None]
    progress: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True))
    error: Mapped[dict[str, Any] | None] = mapped_column(JSON(none_as_null=True))
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]


class ArtifactObjectRow(Base):
    """Catalog of stored content. The file location is derived from the hash, never stored."""

    __tablename__ = "artifact_objects"
    __table_args__ = (
        CheckConstraint(
            "length(content_hash) = 71 AND substr(content_hash, 1, 7) = 'sha256:'",
            name="content_hash_format",
        ),
        CheckConstraint("size >= 0", name="size_non_negative"),
    )

    content_hash: Mapped[str] = mapped_column(String(HASH_LENGTH), primary_key=True)
    size: Mapped[int] = mapped_column(BigInteger)
    created_at: Mapped[datetime]


class AnalysisArtifactRow(Base):
    """Logical artifact: one named output of one stage of one analysis run."""

    __tablename__ = "analysis_artifacts"
    __table_args__ = (UniqueConstraint("analysis_run_id", "stage", "name"),)

    artifact_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    analysis_run_id: Mapped[str] = mapped_column(
        String(ID_LENGTH), ForeignKey("analysis_runs.analysis_run_id")
    )
    stage: Mapped[JobStage] = mapped_column(_enum(JobStage, "job_stage"))
    name: Mapped[str] = mapped_column(String(ARTIFACT_NAME_LENGTH))
    content_hash: Mapped[str] = mapped_column(
        String(HASH_LENGTH), ForeignKey("artifact_objects.content_hash")
    )
    created_at: Mapped[datetime]


class EvidenceRow(Base):
    __tablename__ = "evidence"
    __table_args__ = (UniqueConstraint("snapshot_id", "locator_key", "content_hash"),)

    evidence_id: Mapped[str] = mapped_column(String(ID_LENGTH), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(ID_LENGTH), ForeignKey("snapshots.snapshot_id"))
    type: Mapped[EvidenceType] = mapped_column(_enum(EvidenceType, "evidence_type"))
    locator: Mapped[dict[str, Any]] = mapped_column(JSON)
    # stable_hash(locator), so equal locators match regardless of JSON key order.
    locator_key: Mapped[str] = mapped_column(String(HASH_LENGTH))
    # The full captured material in artifact storage; excerpt is the part shown to reviewers.
    content_hash: Mapped[str] = mapped_column(
        String(HASH_LENGTH), ForeignKey("artifact_objects.content_hash")
    )
    excerpt: Mapped[str] = mapped_column(Text)
    captured_at: Mapped[datetime]
