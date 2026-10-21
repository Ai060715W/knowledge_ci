"""Persistent analysis jobs: idempotent submission, leases, stage checkpoints and retries.

A Job is one logical task; each execution is an attempt holding its own lease_token.
Results are accepted only from the running attempt whose token still matches.
"""

import secrets
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Self

from pydantic import (
    Field,
    NonNegativeInt,
    PositiveInt,
    StringConstraints,
    model_validator,
)

from knowledge_ci.contracts.common import (
    ContentHash,
    ContractModel,
    GitRef,
    Id,
    Label,
    UtcDatetime,
    evolve,
    stable_hash,
)
from knowledge_ci.contracts.errors import ContractError, ErrorCode

DEFAULT_MAX_ATTEMPTS = 3

IdempotencyKey = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]{7,127}$")]
LeaseToken = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{32,128}$")]
ErrorSlug = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]{0,63}$")]


def new_lease_token() -> str:
    return secrets.token_urlsafe(32)


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"  # finished, but some inputs failed; diagnostics are kept per stage
    FAILED = "failed"
    CANCELLED = "cancelled"


TERMINAL_STATUSES = frozenset(
    {JobStatus.SUCCEEDED, JobStatus.PARTIAL, JobStatus.FAILED, JobStatus.CANCELLED}
)


class JobStage(StrEnum):
    """Pipeline stages in execution order; a job never moves back to an earlier stage."""

    SNAPSHOT = "snapshot"
    PARSE = "parse"
    GRAPH = "graph"
    RANK = "rank"
    RULES = "rules"
    EVIDENCE = "evidence"
    GENERATE = "generate"  # model drafts and questions (T12-T14)


STAGE_ORDER = MappingProxyType({stage: index for index, stage in enumerate(JobStage)})


class JobError(ContractModel):
    code: ErrorSlug  # e.g. "lease_expired", "parse_timeout", "permission_denied"
    message: Label  # actionable and redacted; no source text, paths outside the repo or secrets
    retryable: bool
    stage: JobStage | None = None


class Progress(ContractModel):
    completed: NonNegativeInt
    total: PositiveInt | None = None  # None when the denominator is unknown; show the stage only

    @model_validator(mode="after")
    def _bounded(self) -> Self:
        if self.total is not None and self.completed > self.total:
            raise ValueError("completed cannot exceed total")
        return self


class SignalWeights(ContractModel):
    """Initial Top-K weights from PROJECT_PLAN 3.2; T08 calibrates them per configuration."""

    change_frequency: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.5
    fan_in: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.3
    contributor_diversity: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.2

    @model_validator(mode="after")
    def _normalized(self) -> Self:
        if abs(self.change_frequency + self.fan_in + self.contributor_diversity - 1) > 1e-9:
            raise ValueError("signal weights must sum to 1")
        return self


class AnalysisConfig(ContractModel):
    top_k: Annotated[int, Field(ge=1, le=100)] = 10
    history_window_days: Annotated[int, Field(ge=1, le=3650)] = 90
    weights: SignalWeights = SignalWeights()

    def config_hash(self) -> str:
        return stable_hash(self)


class StartAnalysisRequest(ContractModel):
    """Body of POST /repositories/{id}/analyses; Idempotency-Key travels in the header."""

    ref: GitRef
    config: AnalysisConfig = AnalysisConfig()


def request_fingerprint(repository_id: str, request: StartAnalysisRequest) -> str:
    """Hash of the full request including defaults, so equivalent requests compare equal."""
    return stable_hash({"repository_id": repository_id, "request": request.model_dump(mode="json")})


class Job(ContractModel):
    job_id: Id
    idempotency_key: IdempotencyKey
    request_hash: ContentHash
    repository_id: Id
    requested_ref: GitRef  # display only; snapshot_id is the code identity
    snapshot_id: Id
    analysis_run_id: Id
    status: JobStatus = JobStatus.QUEUED
    stage: JobStage = JobStage.SNAPSHOT  # stage in progress; earlier stages are checkpoints
    attempt: NonNegativeInt = 0  # executions started so far
    max_attempts: PositiveInt = DEFAULT_MAX_ATTEMPTS
    lease_token: LeaseToken | None = None
    heartbeat_at: UtcDatetime | None = None
    lease_expires_at: UtcDatetime | None = None
    progress: Progress | None = None
    error: JobError | None = None  # last failure; kept while a retry is queued
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @model_validator(mode="after")
    def _status_fields(self) -> Self:
        held = [
            value is not None
            for value in (self.lease_token, self.heartbeat_at, self.lease_expires_at)
        ]
        running = self.status is JobStatus.RUNNING
        if (running and not all(held)) or (not running and any(held)):
            raise ValueError("only running jobs hold a lease, heartbeat and expiry")
        if self.attempt > self.max_attempts:
            raise ValueError("attempt cannot exceed max_attempts")
        if self.status is JobStatus.QUEUED and self.attempt >= self.max_attempts:
            raise ValueError("queued jobs need a remaining attempt")
        if self.status not in (JobStatus.QUEUED, JobStatus.CANCELLED) and self.attempt < 1:
            raise ValueError("a started job has at least one attempt")
        if self.status is JobStatus.FAILED and self.error is None:
            raise ValueError("failed jobs need an error")
        if self.status in (JobStatus.SUCCEEDED, JobStatus.PARTIAL) and self.error is not None:
            raise ValueError("finished jobs carry no error")
        return self


class JobView(ContractModel):
    """Public job state for GET /jobs/{job_id}; the lease token never leaves the worker."""

    job_id: Id
    repository_id: Id
    snapshot_id: Id
    analysis_run_id: Id
    requested_ref: GitRef
    status: JobStatus
    stage: JobStage
    attempt: NonNegativeInt
    max_attempts: PositiveInt
    retryable: bool  # manual retry is allowed
    progress: Progress | None
    error: JobError | None
    heartbeat_at: UtcDatetime | None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @classmethod
    def from_job(cls, job: Job) -> Self:
        return cls.model_validate(
            {
                **job.model_dump(
                    exclude={"idempotency_key", "request_hash", "lease_token", "lease_expires_at"}
                ),
                "retryable": job.status is JobStatus.FAILED,
            }
        )


class StartAnalysisResponse(ContractModel):
    """202 body; a replay with the same Idempotency-Key returns the same job."""

    job_id: Id
    snapshot_id: Id
    analysis_run_id: Id
    status: JobStatus


def check_replay(existing: Job, request_hash: str) -> Job:
    """Same key and same request: same logical job. Same key, different request: conflict."""
    if existing.request_hash != request_hash:
        raise ContractError(
            ErrorCode.IDEMPOTENCY_CONFLICT,
            "Idempotency-Key was already used for a different request",
        )
    return existing


def require_lease(job: Job, *, attempt: int, lease_token: str, now: datetime) -> None:
    """Gate for every worker write: the job is running this attempt and the lease is alive."""
    valid = (
        job.status is JobStatus.RUNNING
        and job.attempt == attempt
        and job.lease_token is not None
        and secrets.compare_digest(job.lease_token.encode(), lease_token.encode())
    )
    if not valid:
        raise ContractError(ErrorCode.STALE_LEASE, "Lease is no longer valid for this job")
    assert job.lease_expires_at is not None
    if now >= job.lease_expires_at:
        raise ContractError(ErrorCode.STALE_LEASE, "Lease has expired")


def _release(job: Job, status: JobStatus, now: datetime, **changes: object) -> Job:
    return evolve(
        job,
        status=status,
        lease_token=None,
        heartbeat_at=None,
        lease_expires_at=None,
        updated_at=now,
        **changes,
    )


def _check_duration(lease_duration: timedelta) -> None:
    if lease_duration <= timedelta(0):
        raise ValueError("lease_duration must be positive")


def claim(job: Job, *, now: datetime, lease_duration: timedelta) -> Job:
    """Start the next attempt with a fresh token, resuming at the checkpointed stage."""
    _check_duration(lease_duration)
    if job.status is not JobStatus.QUEUED:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Only queued jobs can be claimed")
    return evolve(
        job,
        status=JobStatus.RUNNING,
        attempt=job.attempt + 1,
        lease_token=new_lease_token(),
        heartbeat_at=now,
        lease_expires_at=now + lease_duration,
        updated_at=now,
    )


def heartbeat(
    job: Job, *, attempt: int, lease_token: str, now: datetime, lease_duration: timedelta
) -> Job:
    _check_duration(lease_duration)
    require_lease(job, attempt=attempt, lease_token=lease_token, now=now)
    return evolve(job, heartbeat_at=now, lease_expires_at=now + lease_duration, updated_at=now)


def advance_stage(
    job: Job,
    stage: JobStage,
    *,
    attempt: int,
    lease_token: str,
    now: datetime,
    progress: Progress | None = None,
) -> Job:
    """Checkpoint: the previous stage's artifacts are committed in the same transaction."""
    require_lease(job, attempt=attempt, lease_token=lease_token, now=now)
    if STAGE_ORDER[stage] < STAGE_ORDER[job.stage]:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Job stages cannot move backwards")
    return evolve(job, stage=stage, progress=progress, updated_at=now)


def complete(
    job: Job, *, attempt: int, lease_token: str, now: datetime, partial: bool = False
) -> Job:
    require_lease(job, attempt=attempt, lease_token=lease_token, now=now)
    status = JobStatus.PARTIAL if partial else JobStatus.SUCCEEDED
    return _release(job, status, now, error=None)


def _failure(job: Job, error: JobError, now: datetime) -> Job:
    if error.retryable and job.attempt < job.max_attempts:
        return _release(job, JobStatus.QUEUED, now, error=error)
    return _release(job, JobStatus.FAILED, now, error=error)


def fail(job: Job, error: JobError, *, attempt: int, lease_token: str, now: datetime) -> Job:
    """Retryable failures are re-queued while attempts remain; permanent ones fail at once."""
    require_lease(job, attempt=attempt, lease_token=lease_token, now=now)
    return _failure(job, error, now)


def expire_lease(job: Job, *, now: datetime) -> Job:
    """Recovery for a worker that stopped heartbeating; its token can no longer commit."""
    if job.status is not JobStatus.RUNNING:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Only running jobs hold a lease")
    assert job.lease_expires_at is not None
    if now < job.lease_expires_at:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Lease has not expired yet")
    error = JobError(
        code="lease_expired",
        message="Worker stopped reporting before the lease expired",
        retryable=True,
        stage=job.stage,
    )
    return _failure(job, error, now)


def cancel(job: Job, *, now: datetime) -> Job:
    """Cancel a queued or running job; any outstanding lease token becomes invalid."""
    if job.status not in (JobStatus.QUEUED, JobStatus.RUNNING):
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Job has already finished")
    return _release(job, JobStatus.CANCELLED, now)


def retry(job: Job, *, now: datetime, extra_attempts: int = 1) -> Job:
    """Manual retry of a failed job: same logical job, kept checkpoints, more attempts."""
    if job.status is not JobStatus.FAILED:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Only failed jobs can be retried")
    if extra_attempts < 1:
        raise ValueError("extra_attempts must be positive")
    return evolve(
        job,
        status=JobStatus.QUEUED,
        max_attempts=max(job.max_attempts, job.attempt + extra_attempts),
        updated_at=now,
    )
