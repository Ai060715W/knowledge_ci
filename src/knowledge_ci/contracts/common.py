"""Contract primitives: identifiers, UTC time, repository paths, stable hashing and paging."""

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, StringConstraints


class ContractModel(BaseModel):
    """Closed, immutable schema: unknown fields are rejected and instances never change in place."""

    model_config = ConfigDict(extra="forbid", frozen=True)


# Opaque identifier for aggregates and actors; storage generates the values.
Id = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")]
# Full lowercase Git object name; branch names are never identities.
GitSha = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{40}$")]
ContentHash = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]
VersionTag = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._+@/:-]{0,127}$")]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20_000)]


def unique_items[T](values: tuple[T, ...]) -> tuple[T, ...]:
    if len(set(values)) != len(values):
        raise ValueError("Items must be unique")
    return values


UniqueIds = Annotated[tuple[Id, ...], AfterValidator(unique_items)]


def _to_utc(value: datetime) -> datetime:
    return value.astimezone(UTC)


# Timezone-aware input only; normalized to UTC and serialized as ISO 8601 with "Z".
UtcDatetime = Annotated[AwareDatetime, AfterValidator(_to_utc)]

_DRIVE = re.compile(r"^[A-Za-z]:")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


def _check_repo_path(value: str) -> str:
    if not value or len(value) > 1024:
        raise ValueError("Repository path must contain 1-1024 characters")
    if "\\" in value or _CONTROL.search(value):
        raise ValueError("Repository path must use '/' separators without control characters")
    if value.startswith("/") or _DRIVE.match(value):
        raise ValueError("Repository path must be relative to the repository root")
    if any(part in ("", ".", "..") for part in value.split("/")):
        raise ValueError("Repository path must not contain empty, '.' or '..' segments")
    return value


# Repository-relative POSIX path, e.g. "Vue3Admin/src/router/index.ts".
RepoPath = Annotated[str, AfterValidator(_check_repo_path)]


def _check_git_ref(value: str) -> str:
    if ".." in value or "//" in value or "/." in value or value.endswith(("/", ".", ".lock")):
        raise ValueError("Git ref must name a single revision")
    return value


# User-supplied revision such as "main", "v1.2.0" or "HEAD~1"; resolved to a GitSha before use.
# A leading alphanumeric keeps refs from being read as Git options.
GitRef = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9._/~^-]{0,254}$"),
    AfterValidator(_check_git_ref),
]


def utc_now() -> datetime:
    return datetime.now(UTC)


def hash_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def stable_hash(value: object) -> str:
    """sha256 of canonical JSON (sorted keys, compact, UTF-8); models are dumped in JSON mode."""
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hash_bytes(canonical.encode("utf-8"))


def evolve[M: BaseModel](model: M, **changes: object) -> M:
    """Copy with changes and re-validate; model_copy(update=...) would skip the invariants."""
    return type(model).model_validate({**model.model_dump(), **changes})


class Page[T](ContractModel):
    """List envelope; next_cursor is opaque and absent on the last page."""

    items: tuple[T, ...]
    next_cursor: Annotated[str, StringConstraints(min_length=1, max_length=512)] | None = None
