"""Evidence rows pinned to a snapshot; the captured material itself lives in artifact storage."""

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge_ci.contracts.common import stable_hash
from knowledge_ci.contracts.errors import ContractError, ErrorCode
from knowledge_ci.contracts.evidence import Evidence
from knowledge_ci.storage.models import ArtifactObjectRow, EvidenceRow, row_values


def add_evidence(session: Session, evidence: Evidence) -> Evidence:
    """One row per (snapshot, locator, content). Store the material with ArtifactStore.put()
    and record() first; evidence never points to content that is not stored."""
    locator_key = stable_hash(evidence.locator)
    row = session.scalar(
        select(EvidenceRow).where(
            EvidenceRow.snapshot_id == evidence.snapshot_id,
            EvidenceRow.locator_key == locator_key,
            EvidenceRow.content_hash == evidence.content_hash,
        )
    )
    if row is None:
        if session.get(ArtifactObjectRow, evidence.content_hash) is None:
            raise ContractError(ErrorCode.INVALID_REFERENCE, "Evidence content is not stored")
        row = EvidenceRow(**row_values(evidence, "locator"), locator_key=locator_key)
        session.add(row)
        session.flush()
    return _evidence(row)


def get_evidence(session: Session, evidence_ids: Iterable[str]) -> dict[str, Evidence]:
    """Evidence by ID for contracts.knowledge reference checks; unknown IDs are left out, so
    the check reports them as evidence_missing."""
    wanted = set(evidence_ids)
    if not wanted:
        return {}
    rows = session.scalars(select(EvidenceRow).where(EvidenceRow.evidence_id.in_(wanted)))
    return {row.evidence_id: _evidence(row) for row in rows}


def _evidence(row: EvidenceRow) -> Evidence:
    return Evidence.model_validate(row, from_attributes=True)
