"""Evidence: traceable source material pinned to a snapshot. Evidence is input, not fact."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, StringConstraints, model_validator

from knowledge_ci.contracts.common import (
    ContentHash,
    ContractModel,
    GitSha,
    Id,
    RepoPath,
    UtcDatetime,
)
from knowledge_ci.contracts.repository import SourceSpan


class EvidenceType(StrEnum):
    CODE = "code"
    COMMIT = "commit"
    HUMAN_ANSWER = "human_answer"


class CodeLocator(ContractModel):
    type: Literal[EvidenceType.CODE] = EvidenceType.CODE
    span: SourceSpan
    symbol_id: Id | None = None


class CommitLocator(ContractModel):
    type: Literal[EvidenceType.COMMIT] = EvidenceType.COMMIT
    commit_sha: GitSha  # reachable from the snapshot commit; checked by the evidence collector
    path: RepoPath | None = None  # file touched by the commit, when the evidence is file-specific


class HumanAnswerLocator(ContractModel):
    type: Literal[EvidenceType.HUMAN_ANSWER] = EvidenceType.HUMAN_ANSWER
    question_id: Id
    answered_by: Id


EvidenceLocator = Annotated[
    CodeLocator | CommitLocator | HumanAnswerLocator, Field(discriminator="type")
]
# Display snippet; whitespace is significant for code, so it is not stripped.
Excerpt = Annotated[str, StringConstraints(min_length=1, max_length=8_000)]


class Evidence(ContractModel):
    """content_hash addresses the full captured material (file blob, commit record or answer)
    in artifact storage; excerpt is the bounded part shown to reviewers and models."""

    evidence_id: Id
    snapshot_id: Id
    type: EvidenceType
    locator: EvidenceLocator
    content_hash: ContentHash
    excerpt: Excerpt
    captured_at: UtcDatetime

    @model_validator(mode="after")
    def _locator_matches_type(self) -> Self:
        if self.locator.type != self.type:
            raise ValueError("locator.type must match evidence type")
        return self
