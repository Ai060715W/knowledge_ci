"""Content-addressed artifact files and the logical artifact IDs that name them.

put() writes bytes outside any transaction (temporary file + atomic replace), so file IO never
holds the write lock. attach() then catalogs the content and names it as a stage output inside
the caller's transaction. A rolled-back transaction leaves at most an unreferenced file that
the next put() of the same content reuses; no business row points to missing content.
"""

import os
import re
import secrets
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from knowledge_ci.contracts.common import hash_bytes, utc_now
from knowledge_ci.contracts.errors import ContractError, ErrorCode
from knowledge_ci.contracts.jobs import JobStage
from knowledge_ci.storage.database import StorageError
from knowledge_ci.storage.models import (
    AnalysisArtifactRow,
    ArtifactObjectRow,
    IdPrefix,
    new_id,
)

OBJECTS_DIR = Path("artifacts") / "objects" / "sha256"
_DIGEST = re.compile(r"sha256:([0-9a-f]{64})")
# Stage output names such as "symbols.json" or "import-graph.json".
_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_REPLACE_ATTEMPTS = 10
_REPLACE_BACKOFF = 0.01  # seconds, multiplied by the attempt number


class ArtifactIntegrityError(StorageError):
    """Stored content is missing or no longer matches its hash."""


def artifact_root(data_dir: Path) -> Path:
    return data_dir / OBJECTS_DIR


@dataclass(frozen=True)
class StoredObject:
    content_hash: str
    size: int


@dataclass(frozen=True)
class Artifact:
    """Logical reference to one named output of one stage of an analysis run."""

    artifact_id: str
    analysis_run_id: str
    stage: JobStage
    name: str
    content_hash: str
    created_at: datetime


class ArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, content_hash: str) -> Path:
        """Location derived from the hash alone; anything but a sha256 digest is refused."""
        match = _DIGEST.fullmatch(content_hash)
        if match is None:
            raise ValueError("content_hash must be a sha256 digest")
        digest = match.group(1)
        return self.root / digest[:2] / digest[2:]

    def put(self, data: bytes) -> StoredObject:
        """Store bytes under their hash. Idempotent; a damaged file is replaced."""
        content_hash = hash_bytes(data)
        target = self.path_for(content_hash)
        if self._intact(target, content_hash):
            return StoredObject(content_hash, len(data))
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f"{target.name}.{secrets.token_hex(8)}.tmp")
        try:
            with temporary.open("xb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            self._replace(temporary, target, content_hash)
        finally:
            temporary.unlink(missing_ok=True)
        return StoredObject(content_hash, len(data))

    def _replace(self, temporary: Path, target: Path, content_hash: str) -> None:
        for attempt in range(_REPLACE_ATTEMPTS):
            try:
                os.replace(temporary, target)
                return
            except PermissionError:
                # Windows refuses while another writer replaces or reads the same file;
                # that writer stores identical bytes, so an intact target is success.
                if self._intact(target, content_hash):
                    return
                if attempt == _REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(_REPLACE_BACKOFF * (attempt + 1))

    @staticmethod
    def _intact(path: Path, content_hash: str) -> bool:
        try:
            return hash_bytes(path.read_bytes()) == content_hash
        except (FileNotFoundError, PermissionError):  # PermissionError: Windows, mid-replace
            return False

    def read(self, content_hash: str) -> bytes:
        """Bytes for a hash, verified on every read."""
        try:
            data = self.path_for(content_hash).read_bytes()
        except FileNotFoundError as exc:
            raise ArtifactIntegrityError("Artifact content is missing") from exc
        if hash_bytes(data) != content_hash:
            raise ArtifactIntegrityError("Artifact content does not match its hash")
        return data

    def record(self, session: Session, stored: StoredObject) -> None:
        """Catalog stored content in the caller's transaction (idempotent)."""
        try:
            size = self.path_for(stored.content_hash).stat().st_size
        except FileNotFoundError:
            size = None
        if size != stored.size:
            raise ArtifactIntegrityError("Content must be stored before it is recorded")
        if session.get(ArtifactObjectRow, stored.content_hash) is None:
            session.add(
                ArtifactObjectRow(
                    content_hash=stored.content_hash, size=stored.size, created_at=utc_now()
                )
            )
            session.flush()

    def attach(
        self,
        session: Session,
        stored: StoredObject,
        *,
        analysis_run_id: str,
        stage: JobStage,
        name: str,
    ) -> Artifact:
        """Name stored content as a stage output. The same name and content returns the
        existing artifact; different content under a taken name is a conflict, so a late or
        repeated execution cannot overwrite a committed output."""
        if _NAME.fullmatch(name) is None:
            raise ValueError("artifact name must be lowercase letters, digits, '.', '_' or '-'")
        existing = find_artifact(session, analysis_run_id=analysis_run_id, stage=stage, name=name)
        if existing is not None:
            if existing.content_hash != stored.content_hash:
                raise ContractError(
                    ErrorCode.IDEMPOTENCY_CONFLICT,
                    "Artifact name is already bound to different content",
                )
            return existing
        self.record(session, stored)
        row = AnalysisArtifactRow(
            artifact_id=new_id(IdPrefix.ARTIFACT),
            analysis_run_id=analysis_run_id,
            stage=stage,
            name=name,
            content_hash=stored.content_hash,
            created_at=utc_now(),
        )
        session.add(row)
        session.flush()
        return _artifact(row)

    def read_artifact(self, session: Session, artifact_id: str) -> bytes:
        return self.read(get_artifact(session, artifact_id).content_hash)


def find_artifact(
    session: Session, *, analysis_run_id: str, stage: JobStage, name: str
) -> Artifact | None:
    row = session.scalar(
        select(AnalysisArtifactRow).where(
            AnalysisArtifactRow.analysis_run_id == analysis_run_id,
            AnalysisArtifactRow.stage == stage,
            AnalysisArtifactRow.name == name,
        )
    )
    return None if row is None else _artifact(row)


def get_artifact(session: Session, artifact_id: str) -> Artifact:
    row = session.get(AnalysisArtifactRow, artifact_id)
    if row is None:
        raise ContractError(ErrorCode.NOT_FOUND, "Artifact not found")
    return _artifact(row)


def _artifact(row: AnalysisArtifactRow) -> Artifact:
    return Artifact(
        artifact_id=row.artifact_id,
        analysis_run_id=row.analysis_run_id,
        stage=row.stage,
        name=row.name,
        content_hash=row.content_hash,
        created_at=row.created_at,
    )
