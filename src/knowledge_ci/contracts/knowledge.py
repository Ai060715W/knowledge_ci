"""Knowledge, revisions, claims, questions, reviews and verification, with their state rules.

Transition helpers are pure: they check CAS versions and state rules, then return new
immutable objects. Storage applies them inside one transaction (T04/T14/T15).
"""

from collections.abc import Iterable, Mapping
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Self

from pydantic import AfterValidator, Field, PositiveInt, model_validator

from knowledge_ci.contracts.common import (
    ContentHash,
    ContractModel,
    GitSha,
    Id,
    Label,
    RepoPath,
    Text,
    UniqueIds,
    UtcDatetime,
    VersionTag,
    evolve,
    stable_hash,
    unique_items,
)
from knowledge_ci.contracts.errors import ConflictInfo, ContractError, ErrorCode, ErrorDetail
from knowledge_ci.contracts.evidence import Evidence, EvidenceType, HumanAnswerLocator


class ClaimKind(StrEnum):
    OBSERVED = "observed"  # directly visible in the cited evidence
    INFERRED = "inferred"  # reasoning over evidence; a score never upgrades it to fact
    HUMAN_CONFIRMED = "human_confirmed"  # backed by a recorded human answer


class EvidenceSufficiency(StrEnum):
    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"
    SUFFICIENT = "sufficient"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"  # default: missing or conflicting evidence never means low


class Lifecycle(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReviewStatus(StrEnum):
    UNREVIEWED = "unreviewed"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    REJECT = "reject"


DECISION_STATUS = MappingProxyType(
    {
        ReviewDecision.APPROVE: ReviewStatus.APPROVED,
        ReviewDecision.REQUEST_CHANGES: ReviewStatus.CHANGES_REQUESTED,
        ReviewDecision.REJECT: ReviewStatus.REJECTED,
    }
)
# A decision is final for its revision; further changes need a new revision.
REVIEWABLE_STATUSES = frozenset({ReviewStatus.UNREVIEWED, ReviewStatus.IN_REVIEW})


class QuestionStatus(StrEnum):
    OPEN = "open"
    ANSWERED = "answered"
    RESOLVED = "resolved"  # the answer was adopted as evidence or the case was explicitly closed
    CANCELLED = "cancelled"


QUESTION_TRANSITIONS = MappingProxyType(
    {
        QuestionStatus.OPEN: frozenset({QuestionStatus.ANSWERED, QuestionStatus.CANCELLED}),
        QuestionStatus.ANSWERED: frozenset(
            {QuestionStatus.OPEN, QuestionStatus.RESOLVED, QuestionStatus.CANCELLED}
        ),
        QuestionStatus.RESOLVED: frozenset(),
        QuestionStatus.CANCELLED: frozenset(),
    }
)


class FreshnessResult(StrEnum):
    UNKNOWN = "unknown"
    FRESH = "fresh"
    STALE = "stale"


class VerificationMethod(StrEnum):
    HUMAN_REVIEW = "human_review"  # P0: checked by a reviewer on the source snapshot
    RULE = "rule"  # P1: version, equivalence or impact rules
    MODEL = "model"  # P1: budgeted model judgement


class Claim(ContractModel):
    claim_id: Id
    kind: ClaimKind
    text: Text
    evidence_ids: UniqueIds = ()
    gap: Text | None = None  # what is still missing; any gap blocks publication

    @model_validator(mode="after")
    def _grounded(self) -> Self:
        if self.kind is not ClaimKind.INFERRED and not self.evidence_ids:
            raise ValueError("observed and human_confirmed claims must cite evidence")
        if not self.evidence_ids and self.gap is None:
            raise ValueError("a claim without evidence must state its gap")
        return self


class InvalidationStatus(StrEnum):
    KNOWN = "known"
    UNKNOWN = "unknown"


class Invalidation(ContractModel):
    """When the knowledge stops holding. An empty list never means "valid forever"."""

    status: InvalidationStatus
    conditions: tuple[Label, ...] = ()  # with status unknown: the conditions known so far
    unknown_reason: Label | None = None

    @model_validator(mode="after")
    def _explicit(self) -> Self:
        if self.status is InvalidationStatus.KNOWN:
            if not self.conditions or self.unknown_reason is not None:
                raise ValueError("known invalidation needs conditions and no unknown_reason")
        elif self.unknown_reason is None:
            raise ValueError("unknown invalidation must explain what is missing")
        return self


class KnowledgeScope(ContractModel):
    paths: Annotated[tuple[RepoPath, ...], Field(min_length=1), AfterValidator(unique_items)]
    symbols: Annotated[tuple[Label, ...], AfterValidator(unique_items)] = ()  # qualified names


class ValidFrom(ContractModel):
    """Earliest code version the knowledge is known to apply to."""

    commit_sha: GitSha
    release_tag: VersionTag | None = None


class RevisionContent(ContractModel):
    """Editable body of a revision. Any change produces a new revision."""

    title: Label
    summary: Text
    rationale: Text
    scope: KnowledgeScope
    invalidation: Invalidation
    claims: Annotated[tuple[Claim, ...], Field(min_length=1)]
    evidence_ids: UniqueIds = ()
    evidence_sufficiency: EvidenceSufficiency
    risk_level: RiskLevel = RiskLevel.UNKNOWN
    owner_id: Id | None = None  # optional for drafts, required to publish
    model_score: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] | None = None
    valid_from: ValidFrom | None = None  # None: introduction point not established

    @model_validator(mode="after")
    def _claims_consistent(self) -> Self:
        if len({claim.claim_id for claim in self.claims}) != len(self.claims):
            raise ValueError("claim_id must be unique within a revision")
        cited = {evidence_id for claim in self.claims for evidence_id in claim.evidence_ids}
        if not cited <= set(self.evidence_ids):
            raise ValueError("claims may only cite evidence listed in evidence_ids")
        if self.evidence_sufficiency is EvidenceSufficiency.SUFFICIENT and any(
            claim.gap is not None for claim in self.claims
        ):
            raise ValueError("evidence_sufficiency cannot be sufficient while a claim has a gap")
        return self

    def content_hash(self) -> str:
        return stable_hash(self)


class KnowledgeRevision(ContractModel):
    """Immutable content version. knowledge_id is stable; revision increases by one."""

    knowledge_id: Id
    revision: PositiveInt
    snapshot_id: Id  # source snapshot; all cited evidence must belong to it
    analysis_run_id: Id | None = None  # None for human-authored edits
    based_on_revision: PositiveInt | None = None
    content: RevisionContent
    content_hash: ContentHash  # binds reviews to this exact content
    created_by: Id
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.based_on_revision is not None and self.based_on_revision >= self.revision:
            raise ValueError("based_on_revision must precede revision")
        if self.content_hash != self.content.content_hash():
            raise ValueError("content_hash does not match content")
        return self


class Knowledge(ContractModel):
    """Aggregate head. Every change that can affect publication increments state_version."""

    knowledge_id: Id
    repository_id: Id
    current_revision: PositiveInt
    published_revision: PositiveInt | None = None
    lifecycle: Lifecycle = Lifecycle.DRAFT
    review_status: ReviewStatus = ReviewStatus.UNREVIEWED  # of current_revision
    state_version: PositiveInt = 1
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @model_validator(mode="after")
    def _pointers(self) -> Self:
        published = self.published_revision
        if self.lifecycle is Lifecycle.DRAFT and published is not None:
            raise ValueError("draft knowledge has no published revision")
        if self.lifecycle is Lifecycle.PUBLISHED and published is None:
            raise ValueError("published knowledge needs a published revision")
        if published is not None and published > self.current_revision:
            raise ValueError("published_revision cannot exceed current_revision")
        if published == self.current_revision and self.review_status is not ReviewStatus.APPROVED:
            raise ValueError("the published revision must be approved")
        return self


class Question(ContractModel):
    """Follow-up for missing evidence. Blocking questions stop publication until resolved or
    cancelled; an answer only triggers re-evaluation."""

    question_id: Id
    knowledge_id: Id
    revision: PositiveInt  # revision the question was raised on; blocking spans later revisions
    assignee_id: Id | None = None
    text: Text
    blocking: bool = True
    status: QuestionStatus = QuestionStatus.OPEN
    answer: Text | None = None  # latest answer; kept when an insufficient answer is reopened
    answered_by: Id | None = None
    answered_at: UtcDatetime | None = None
    adopted_evidence_id: Id | None = None  # human_answer evidence created from the answer
    resolution_note: Label | None = None
    created_at: UtcDatetime
    updated_at: UtcDatetime

    @model_validator(mode="after")
    def _status_fields(self) -> Self:
        answer_fields = (self.answer, self.answered_by, self.answered_at)
        if any(value is None for value in answer_fields) != all(
            value is None for value in answer_fields
        ):
            raise ValueError("answer, answered_by and answered_at must be set together")
        closed = (self.adopted_evidence_id, self.resolution_note)
        status = self.status
        if status in (QuestionStatus.OPEN, QuestionStatus.ANSWERED) and any(closed):
            raise ValueError("open or answered questions carry no resolution")
        if status in (QuestionStatus.ANSWERED, QuestionStatus.RESOLVED) and self.answer is None:
            raise ValueError("answered and resolved questions need an answer")
        if status is QuestionStatus.RESOLVED and not any(closed):
            raise ValueError("resolved questions need adopted evidence or a resolution note")
        if status is QuestionStatus.CANCELLED and (
            self.resolution_note is None or self.adopted_evidence_id is not None
        ):
            raise ValueError("cancelled questions need a note and adopt no evidence")
        return self

    @property
    def blocks_publication(self) -> bool:
        return self.blocking and self.status in (QuestionStatus.OPEN, QuestionStatus.ANSWERED)


def _check_reason(decision: ReviewDecision, reason: str | None) -> None:
    if decision is not ReviewDecision.APPROVE and reason is None:
        raise ValueError("request_changes and reject need a reason")


class Review(ContractModel):
    """Decision bound to one revision and its exact content."""

    review_id: Id
    knowledge_id: Id
    revision: PositiveInt
    content_hash: ContentHash
    decision: ReviewDecision
    reviewer_id: Id  # server-side actor, never taken from the request body
    reason: Text | None = None
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _reason(self) -> Self:
        _check_reason(self.decision, self.reason)
        return self


class Verification(ContractModel):
    """Freshness of one revision for one snapshot and scope; never valid beyond them."""

    verification_id: Id
    knowledge_id: Id
    revision: PositiveInt
    verified_snapshot_id: Id
    scope_hash: ContentHash
    result: FreshnessResult
    method: VerificationMethod
    note: Label | None = None
    verified_at: UtcDatetime


def scope_hash(scope: KnowledgeScope) -> str:
    return stable_hash(scope)


class KnowledgeCommand(ContractModel):
    """CAS guard carried by every edit, review, publish and archive command."""

    expected_revision: PositiveInt
    expected_state_version: PositiveInt


class CreateRevisionRequest(KnowledgeCommand):
    content: RevisionContent


class ReviewRequest(KnowledgeCommand):
    decision: ReviewDecision
    reason: Text | None = None

    @model_validator(mode="after")
    def _reason(self) -> Self:
        _check_reason(self.decision, self.reason)
        return self


class CreateQuestionRequest(ContractModel):
    revision: PositiveInt
    text: Text
    assignee_id: Id | None = None
    blocking: bool = True


class AnswerQuestionRequest(ContractModel):
    answer: Text


class PublishRequest(KnowledgeCommand):
    """Publishes current_revision; the expected versions pin exactly what was reviewed."""


class ArchiveRequest(KnowledgeCommand):
    reason: Text


def require_current(knowledge: Knowledge, command: KnowledgeCommand) -> None:
    """Optimistic concurrency check: both versions must match what the caller read."""
    conflict = ConflictInfo(
        current_revision=knowledge.current_revision,
        current_state_version=knowledge.state_version,
    )
    if command.expected_revision != knowledge.current_revision:
        raise ContractError(
            ErrorCode.STALE_REVISION, "Knowledge has a newer revision", conflict=conflict
        )
    if command.expected_state_version != knowledge.state_version:
        raise ContractError(
            ErrorCode.STALE_STATE_VERSION,
            "Knowledge state changed after it was read",
            conflict=conflict,
        )


def _require_editable(knowledge: Knowledge) -> None:
    if knowledge.lifecycle is Lifecycle.ARCHIVED:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Archived knowledge cannot change")


def _require_current_revision(knowledge: Knowledge, revision: KnowledgeRevision) -> None:
    if (revision.knowledge_id, revision.revision) != (
        knowledge.knowledge_id,
        knowledge.current_revision,
    ):
        raise ValueError("revision is not the current revision of this knowledge")


def reference_errors(
    content: RevisionContent, snapshot_id: str, evidence_by_id: Mapping[str, Evidence]
) -> tuple[ErrorDetail, ...]:
    """Cited evidence must exist, belong to the revision snapshot and match the claim kind."""
    errors: list[ErrorDetail] = []
    for index, evidence_id in enumerate(content.evidence_ids):
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            code, message = "evidence_missing", "Evidence does not exist"
        elif evidence.snapshot_id != snapshot_id:
            code, message = "evidence_snapshot_mismatch", "Evidence belongs to another snapshot"
        else:
            continue
        errors.append(
            ErrorDetail(field=f"evidence_ids.{index}", code=code, message=message, ref=evidence_id)
        )
    for index, claim in enumerate(content.claims):
        types = {
            evidence_by_id[evidence_id].type
            for evidence_id in claim.evidence_ids
            if evidence_id in evidence_by_id
        }
        if claim.kind is ClaimKind.HUMAN_CONFIRMED and EvidenceType.HUMAN_ANSWER not in types:
            errors.append(
                ErrorDetail(
                    field=f"claims.{index}.evidence_ids",
                    code="human_answer_missing",
                    message="human_confirmed claims must cite a human answer",
                    ref=claim.claim_id,
                )
            )
    return tuple(errors)


def _require_references(
    content: RevisionContent, snapshot_id: str, evidence_by_id: Mapping[str, Evidence]
) -> None:
    errors = reference_errors(content, snapshot_id, evidence_by_id)
    if errors:
        raise ContractError(
            ErrorCode.INVALID_REFERENCE, "Revision cites invalid evidence", details=errors
        )


def _touch(knowledge: Knowledge, now: datetime, **changes: object) -> Knowledge:
    return evolve(knowledge, state_version=knowledge.state_version + 1, updated_at=now, **changes)


def new_knowledge(
    *,
    knowledge_id: str,
    repository_id: str,
    snapshot_id: str,
    content: RevisionContent,
    created_by: str,
    now: datetime,
    evidence_by_id: Mapping[str, Evidence],
    analysis_run_id: str | None = None,
) -> tuple[Knowledge, KnowledgeRevision]:
    """First draft revision of a new knowledge aggregate."""
    _require_references(content, snapshot_id, evidence_by_id)
    revision = KnowledgeRevision(
        knowledge_id=knowledge_id,
        revision=1,
        snapshot_id=snapshot_id,
        analysis_run_id=analysis_run_id,
        content=content,
        content_hash=content.content_hash(),
        created_by=created_by,
        created_at=now,
    )
    knowledge = Knowledge(
        knowledge_id=knowledge_id,
        repository_id=repository_id,
        current_revision=1,
        created_at=now,
        updated_at=now,
    )
    return knowledge, revision


def apply_revision(
    knowledge: Knowledge,
    current: KnowledgeRevision,
    request: CreateRevisionRequest,
    *,
    created_by: str,
    now: datetime,
    evidence_by_id: Mapping[str, Evidence],
    snapshot_id: str | None = None,
    analysis_run_id: str | None = None,
) -> tuple[Knowledge, KnowledgeRevision]:
    """New content revision. Review restarts; the published pointer stays on the old revision."""
    _require_current_revision(knowledge, current)
    require_current(knowledge, request)
    _require_editable(knowledge)
    if request.content.content_hash() == current.content_hash:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Revision content is unchanged")
    snapshot_id = snapshot_id if snapshot_id is not None else current.snapshot_id
    _require_references(request.content, snapshot_id, evidence_by_id)
    revision = KnowledgeRevision(
        knowledge_id=knowledge.knowledge_id,
        revision=knowledge.current_revision + 1,
        snapshot_id=snapshot_id,
        analysis_run_id=analysis_run_id,
        based_on_revision=knowledge.current_revision,
        content=request.content,
        content_hash=request.content.content_hash(),
        created_by=created_by,
        created_at=now,
    )
    updated = _touch(
        knowledge,
        now,
        current_revision=revision.revision,
        review_status=ReviewStatus.UNREVIEWED,
    )
    return updated, revision


def start_review(knowledge: Knowledge, command: KnowledgeCommand, *, now: datetime) -> Knowledge:
    require_current(knowledge, command)
    _require_editable(knowledge)
    if knowledge.review_status is not ReviewStatus.UNREVIEWED:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Revision is not awaiting review")
    return _touch(knowledge, now, review_status=ReviewStatus.IN_REVIEW)


def record_review(
    knowledge: Knowledge,
    revision: KnowledgeRevision,
    request: ReviewRequest,
    *,
    review_id: str,
    reviewer_id: str,
    now: datetime,
) -> tuple[Knowledge, Review]:
    _require_current_revision(knowledge, revision)
    require_current(knowledge, request)
    _require_editable(knowledge)
    if knowledge.review_status not in REVIEWABLE_STATUSES:
        raise ContractError(ErrorCode.INVALID_TRANSITION, "Revision already has a review decision")
    review = Review(
        review_id=review_id,
        knowledge_id=knowledge.knowledge_id,
        revision=revision.revision,
        content_hash=revision.content_hash,
        decision=request.decision,
        reviewer_id=reviewer_id,
        reason=request.reason,
        created_at=now,
    )
    return _touch(knowledge, now, review_status=DECISION_STATUS[request.decision]), review


def _blocker(code: str, message: str, ref: str | None = None) -> ErrorDetail:
    return ErrorDetail(code=code, message=message, ref=ref)


def publish_blockers(
    knowledge: Knowledge,
    revision: KnowledgeRevision,
    *,
    approval: Review | None,
    questions: Iterable[Question],
    evidence_by_id: Mapping[str, Evidence],
) -> tuple[ErrorDetail, ...]:
    """Every reason the current revision cannot be published; empty means publishable.

    questions: all questions of the knowledge (blocking ones apply across revisions).
    approval: the approve review of the current revision, if any.
    """
    _require_current_revision(knowledge, revision)
    content = revision.content
    blockers: list[ErrorDetail] = []
    if knowledge.lifecycle is Lifecycle.ARCHIVED:
        blockers.append(_blocker("archived", "Archived knowledge cannot be published"))
    if knowledge.published_revision == knowledge.current_revision:
        blockers.append(_blocker("already_published", "Current revision is already published"))
    if knowledge.review_status is not ReviewStatus.APPROVED:
        blockers.append(_blocker("not_approved", "Current revision is not approved"))
    elif (
        approval is None
        or approval.decision is not ReviewDecision.APPROVE
        or (approval.knowledge_id, approval.revision, approval.content_hash)
        != (revision.knowledge_id, revision.revision, revision.content_hash)
    ):
        blockers.append(
            _blocker("approval_mismatch", "Approval does not match the current revision content")
        )
    if content.owner_id is None:
        blockers.append(_blocker("owner_missing", "An owner is required to publish"))
    for question in questions:
        if question.knowledge_id != knowledge.knowledge_id:
            raise ValueError("question belongs to another knowledge")
        if question.blocks_publication:
            blockers.append(
                _blocker(
                    "blocking_question", "A blocking question is unresolved", question.question_id
                )
            )
    for claim in content.claims:
        if claim.gap is not None:  # claims without evidence always carry a gap
            blockers.append(
                _blocker("claim_unsupported", "Claim has an evidence gap", claim.claim_id)
            )
    if content.evidence_sufficiency is not EvidenceSufficiency.SUFFICIENT:
        blockers.append(_blocker("evidence_insufficient", "Evidence is not marked sufficient"))
    blockers.extend(reference_errors(content, revision.snapshot_id, evidence_by_id))
    return tuple(blockers)


def publish(
    knowledge: Knowledge,
    revision: KnowledgeRevision,
    request: PublishRequest,
    *,
    approval: Review | None,
    questions: Iterable[Question],
    evidence_by_id: Mapping[str, Evidence],
    now: datetime,
) -> Knowledge:
    _require_current_revision(knowledge, revision)
    require_current(knowledge, request)
    _require_editable(knowledge)
    blockers = publish_blockers(
        knowledge,
        revision,
        approval=approval,
        questions=questions,
        evidence_by_id=evidence_by_id,
    )
    if blockers:
        raise ContractError(
            ErrorCode.PUBLISH_BLOCKED, "Revision cannot be published", details=blockers
        )
    return _touch(
        knowledge,
        now,
        lifecycle=Lifecycle.PUBLISHED,
        published_revision=knowledge.current_revision,
    )


def archive(knowledge: Knowledge, request: ArchiveRequest, *, now: datetime) -> Knowledge:
    """Stop using the knowledge; revisions, reviews and the published pointer are kept."""
    require_current(knowledge, request)
    _require_editable(knowledge)
    return _touch(knowledge, now, lifecycle=Lifecycle.ARCHIVED)


def sync_question_state(
    knowledge: Knowledge, before: Question | None, after: Question, *, now: datetime
) -> Knowledge:
    """Increment state_version when a question starts or stops blocking publication."""
    if after.knowledge_id != knowledge.knowledge_id:
        raise ValueError("question belongs to another knowledge")
    was_blocking = before is not None and before.blocks_publication
    if was_blocking == after.blocks_publication:
        return knowledge
    return _touch(knowledge, now)


def _move_question(
    question: Question, target: QuestionStatus, *, now: datetime, **changes: object
) -> Question:
    if target not in QUESTION_TRANSITIONS[question.status]:
        raise ContractError(
            ErrorCode.INVALID_TRANSITION, f"Question cannot move from {question.status} to {target}"
        )
    return evolve(question, status=target, updated_at=now, **changes)


def raise_question(
    knowledge: Knowledge, request: CreateQuestionRequest, *, question_id: str, now: datetime
) -> tuple[Knowledge, Question]:
    _require_editable(knowledge)
    if request.revision > knowledge.current_revision:
        raise ContractError(
            ErrorCode.INVALID_REFERENCE,
            "Question refers to a missing revision",
            details=(
                ErrorDetail(field="revision", code="revision_missing", message="No such revision"),
            ),
        )
    question = Question(
        question_id=question_id,
        knowledge_id=knowledge.knowledge_id,
        revision=request.revision,
        assignee_id=request.assignee_id,
        text=request.text,
        blocking=request.blocking,
        created_at=now,
        updated_at=now,
    )
    return sync_question_state(knowledge, None, question, now=now), question


def answer_question(
    question: Question, request: AnswerQuestionRequest, *, answered_by: str, now: datetime
) -> Question:
    """Record an answer; it still blocks until the answer is adopted or the case is closed."""
    return _move_question(
        question,
        QuestionStatus.ANSWERED,
        now=now,
        answer=request.answer,
        answered_by=answered_by,
        answered_at=now,
    )


def reopen_question(question: Question, *, now: datetime) -> Question:
    """The answer was insufficient; it is kept for history and the question is open again."""
    return _move_question(question, QuestionStatus.OPEN, now=now)


def resolve_question(
    question: Question,
    *,
    now: datetime,
    adopted_evidence: Evidence | None = None,
    resolution_note: str | None = None,
) -> Question:
    """Close an answered question by adopting its answer as evidence or with a note."""
    if adopted_evidence is not None:
        locator = adopted_evidence.locator
        if not (
            isinstance(locator, HumanAnswerLocator) and locator.question_id == question.question_id
        ):
            raise ContractError(
                ErrorCode.INVALID_REFERENCE,
                "Adopted evidence must be the human answer to this question",
                details=(
                    ErrorDetail(
                        field="adopted_evidence_id",
                        code="evidence_mismatch",
                        message="Evidence is not this question's answer",
                        ref=adopted_evidence.evidence_id,
                    ),
                ),
            )
    return _move_question(
        question,
        QuestionStatus.RESOLVED,
        now=now,
        adopted_evidence_id=adopted_evidence.evidence_id if adopted_evidence else None,
        resolution_note=resolution_note,
    )


def cancel_question(question: Question, *, reason: str, now: datetime) -> Question:
    return _move_question(question, QuestionStatus.CANCELLED, now=now, resolution_note=reason)
