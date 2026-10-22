"""Repositories, snapshots and analysis runs: written once per identity, read as contracts.

Each add_* runs inside the caller's transaction. Writing an identity that already exists
returns the stored record (its ID wins over the candidate's), so retries and replays never
create a second row.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge_ci.contracts.errors import ContractError, ErrorCode
from knowledge_ci.contracts.repository import AnalysisRun, Repository, Snapshot
from knowledge_ci.storage.models import AnalysisRunRow, RepositoryRow, SnapshotRow, row_values


def add_repository(session: Session, repository: Repository) -> Repository:
    """One repository per allowed_root; the caller normalizes the path first (T05)."""
    row = session.scalar(
        select(RepositoryRow).where(RepositoryRow.allowed_root == repository.allowed_root)
    )
    if row is None:
        row = RepositoryRow(**row_values(repository))
        session.add(row)
        session.flush()
    return Repository.model_validate(row, from_attributes=True)


def get_repository(session: Session, repository_id: str) -> Repository:
    row = session.get(RepositoryRow, repository_id)
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Repository not found")
    return Repository.model_validate(row, from_attributes=True)


def add_snapshot(session: Session, snapshot: Snapshot) -> Snapshot:
    """One snapshot per (repository_id, commit_sha). A commit always has one tree, so a
    different tree_sha means corrupted input and is refused."""
    row = session.scalar(
        select(SnapshotRow).where(
            SnapshotRow.repository_id == snapshot.repository_id,
            SnapshotRow.commit_sha == snapshot.commit_sha,
        )
    )
    if row is None:
        row = SnapshotRow(**row_values(snapshot))
        session.add(row)
        session.flush()
    elif row.tree_sha != snapshot.tree_sha:
        raise ContractError(
            ErrorCode.IDEMPOTENCY_CONFLICT, "Snapshot commit is already stored with another tree"
        )
    return Snapshot.model_validate(row, from_attributes=True)


def get_snapshot(session: Session, snapshot_id: str) -> Snapshot:
    row = session.get(SnapshotRow, snapshot_id)
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Snapshot not found")
    return Snapshot.model_validate(row, from_attributes=True)


def add_analysis_run(session: Session, run: AnalysisRun) -> AnalysisRun:
    """One run per identity_key: the same snapshot and configuration share a run, a different
    configuration gets its own and never overwrites the other's artifacts."""
    identity_key = run.identity_key()
    row = session.scalar(select(AnalysisRunRow).where(AnalysisRunRow.identity_key == identity_key))
    if row is None:
        row = AnalysisRunRow(**row_values(run), identity_key=identity_key)
        session.add(row)
        session.flush()
    return AnalysisRun.model_validate(row, from_attributes=True)


def get_analysis_run(session: Session, analysis_run_id: str) -> AnalysisRun:
    row = session.get(AnalysisRunRow, analysis_run_id)
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Analysis run not found")
    return AnalysisRun.model_validate(row, from_attributes=True)
