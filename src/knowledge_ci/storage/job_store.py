"""Jobs: idempotent submission and lease-checked state changes in the caller's transaction.

State rules stay in contracts.jobs; this module only reads, applies and writes them. A
transition that raises (for example stale_lease) writes nothing, and the caller's rollback
also discards artifacts attached earlier in the same transaction.
"""

from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge_ci.contracts.errors import ContractError, ErrorCode
from knowledge_ci.contracts.jobs import Job, check_replay
from knowledge_ci.storage.models import JobRow, row_values

_JSON_FIELDS = ("progress", "error")
# Fixed at submission; transitions may only change the execution state.
_IDENTITY_FIELDS = frozenset(
    {
        "job_id",
        "idempotency_key",
        "request_hash",
        "repository_id",
        "requested_ref",
        "snapshot_id",
        "analysis_run_id",
        "created_at",
    }
)


def add_job(session: Session, job: Job) -> Job:
    """Store a submitted job. The same Idempotency-Key with the same request returns the
    stored job; with a different request it raises idempotency_conflict."""
    row = session.scalar(
        select(JobRow).where(
            JobRow.repository_id == job.repository_id,
            JobRow.idempotency_key == job.idempotency_key,
        )
    )
    if row is not None:
        return check_replay(_job(row), job.request_hash)
    row = JobRow(**row_values(job, *_JSON_FIELDS))
    session.add(row)
    session.flush()
    return _job(row)


def get_job(session: Session, job_id: str) -> Job:
    row = session.get(JobRow, job_id)
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Job not found")
    return _job(row)


def update_job(session: Session, job_id: str, transition: Callable[[Job], Job]) -> Job:
    """Read the job under a row lock, apply a contracts.jobs transition and write the result.

    SQLite serializes writers with BEGIN IMMEDIATE; FOR UPDATE keeps the same guarantee on
    databases with row locks. Example: ``update_job(s, job_id, lambda j: claim(j, ...))``.
    """
    row = session.scalar(select(JobRow).where(JobRow.job_id == job_id).with_for_update())
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Job not found")
    current = _job(row)
    updated = transition(current)
    if any(getattr(updated, field) != getattr(current, field) for field in _IDENTITY_FIELDS):
        raise ValueError("a job transition cannot change the job identity")
    for field, value in row_values(updated, *_JSON_FIELDS).items():
        if field not in _IDENTITY_FIELDS:
            setattr(row, field, value)
    session.flush()
    return updated


def _job(row: JobRow) -> Job:
    return Job.model_validate(row, from_attributes=True)
