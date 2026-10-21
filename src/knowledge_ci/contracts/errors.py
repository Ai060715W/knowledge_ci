"""Error codes, HTTP status mapping and the redacted error envelope for API, CLI and worker."""

from collections.abc import Iterable
from enum import StrEnum
from types import MappingProxyType

from pydantic import ValidationError

from knowledge_ci.contracts.common import ContractModel, Id


class ErrorCode(StrEnum):
    VALIDATION_FAILED = "validation_failed"
    INVALID_REFERENCE = "invalid_reference"
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"
    STALE_REVISION = "stale_revision"
    STALE_STATE_VERSION = "stale_state_version"
    INVALID_TRANSITION = "invalid_transition"
    PUBLISH_BLOCKED = "publish_blocked"
    STALE_LEASE = "stale_lease"
    IDEMPOTENCY_CONFLICT = "idempotency_conflict"
    INTERNAL_ERROR = "internal_error"


HTTP_STATUS = MappingProxyType(
    {
        ErrorCode.VALIDATION_FAILED: 422,
        ErrorCode.INVALID_REFERENCE: 422,
        ErrorCode.NOT_FOUND: 404,
        ErrorCode.FORBIDDEN: 403,
        ErrorCode.STALE_REVISION: 409,
        ErrorCode.STALE_STATE_VERSION: 409,
        ErrorCode.INVALID_TRANSITION: 409,
        ErrorCode.PUBLISH_BLOCKED: 409,
        ErrorCode.STALE_LEASE: 409,
        ErrorCode.IDEMPOTENCY_CONFLICT: 409,
        ErrorCode.INTERNAL_ERROR: 500,
    }
)


class ErrorDetail(ContractModel):
    field: str | None = None  # dotted location, e.g. "claims.0.evidence_ids"
    code: str
    message: str
    ref: Id | None = None  # system-owned object involved, e.g. a blocking question_id


class ConflictInfo(ContractModel):
    """Current versions returned with 409 so the caller can reload instead of guessing."""

    current_revision: int | None = None
    current_state_version: int | None = None


class ErrorResponse(ContractModel):
    code: ErrorCode
    message: str
    details: tuple[ErrorDetail, ...] = ()
    conflict: ConflictInfo | None = None
    request_id: Id


class ContractError(Exception):
    """Domain rule violation with a stable code; messages never include submitted values."""

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        details: Iterable[ErrorDetail] = (),
        conflict: ConflictInfo | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = tuple(details)
        self.conflict = conflict

    @property
    def http_status(self) -> int:
        return HTTP_STATUS[self.code]

    def to_response(self, request_id: str) -> ErrorResponse:
        return ErrorResponse(
            code=self.code,
            message=self.message,
            details=self.details,
            conflict=self.conflict,
            request_id=request_id,
        )


# Pydantic messages that quote the submitted value are replaced by fixed text.
_ECHOING_MESSAGES = MappingProxyType({"union_tag_invalid": "Unknown discriminator value"})
# Unknown keys appear in loc; bound their length so oversized input is not reflected.
_MAX_FIELD = 200


def field_errors(exc: ValidationError) -> tuple[ErrorDetail, ...]:
    """Field-level details without input values, URLs or validator context."""
    return tuple(
        ErrorDetail(
            field=".".join(map(str, item["loc"]))[:_MAX_FIELD] or None,
            code=item["type"],
            message=_ECHOING_MESSAGES.get(item["type"], item["msg"]),
        )
        for item in exc.errors(include_input=False, include_url=False, include_context=False)
    )


def validation_error(exc: ValidationError) -> ContractError:
    return ContractError(
        ErrorCode.VALIDATION_FAILED, "Request validation failed", details=field_errors(exc)
    )
