"""Repository, Snapshot, AnalysisRun and Symbol contracts, including Vue SFC line mapping."""

from enum import StrEnum
from pathlib import PurePosixPath, PureWindowsPath
from typing import Annotated, Self

from pydantic import AfterValidator, PositiveInt, StringConstraints, model_validator

from knowledge_ci.contracts.common import (
    ContentHash,
    ContractModel,
    GitSha,
    Id,
    Label,
    RepoPath,
    UtcDatetime,
    VersionTag,
    stable_hash,
)


class TargetLanguage(StrEnum):
    """Language family of the analysed repository (not the implementation language)."""

    VUE_TYPESCRIPT = "vue-typescript"  # Vue SFC + TypeScript + JavaScript


class RepositorySource(StrEnum):
    LOCAL_GIT = "local_git"


def _check_local_root(value: str) -> str:
    if not value or len(value) > 4096 or any(ord(char) < 32 for char in value):
        raise ValueError("Local path must contain 1-4096 printable characters")
    windows, posix = PureWindowsPath(value), PurePosixPath(value)
    if not (windows.is_absolute() or posix.is_absolute()):
        raise ValueError("Local path must be absolute")
    if ".." in windows.parts or ".." in posix.parts:
        raise ValueError("Local path must not contain '..' segments")
    return value


# Absolute path on the local machine. Only Repository stores it; business references
# (Evidence, Symbol, Knowledge scope) use RepoPath so artifacts stay machine-independent.
LocalRoot = Annotated[str, AfterValidator(_check_local_root)]


class Repository(ContractModel):
    repository_id: Id
    name: Label
    source: RepositorySource = RepositorySource.LOCAL_GIT
    allowed_root: LocalRoot  # Git worktree root; reads must stay inside it
    created_at: UtcDatetime


class RegisterRepositoryRequest(ContractModel):
    path: LocalRoot  # CLI resolves relative input before building the request
    name: Label | None = None


class Snapshot(ContractModel):
    """Immutable code identity: one per (repository_id, commit_sha). Refs are never stored here."""

    snapshot_id: Id
    repository_id: Id
    commit_sha: GitSha
    tree_sha: GitSha
    created_at: UtcDatetime


class AnalysisRun(ContractModel):
    """One logical analysis configuration over a snapshot; retries live on Job.attempt."""

    analysis_run_id: Id
    snapshot_id: Id
    language: TargetLanguage
    parser_version: VersionTag
    rule_set_version: VersionTag
    config_hash: ContentHash
    pipeline_version: VersionTag
    model_version: VersionTag | None = None  # both None when no model stage runs
    prompt_version: VersionTag | None = None
    created_at: UtcDatetime

    @model_validator(mode="after")
    def _model_versions_pair(self) -> Self:
        if (self.model_version is None) != (self.prompt_version is None):
            raise ValueError("model_version and prompt_version must be set together")
        return self

    def identity_key(self) -> str:
        """Dedup key: equal for the same snapshot and configuration, different otherwise."""
        return stable_hash(self.model_dump(mode="json", exclude={"analysis_run_id", "created_at"}))


class SfcBlockKind(StrEnum):
    SCRIPT = "script"
    SCRIPT_SETUP = "script_setup"
    TEMPLATE = "template"
    STYLE = "style"


class SfcBlock(ContractModel):
    """A block of a .vue file. start_line is the file line where the block content begins
    (compiler-sfc loc.start.line); end_line is the last content line."""

    kind: SfcBlockKind
    lang: Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{0,19}$")] | None = None
    start_line: PositiveInt
    end_line: PositiveInt

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        return self

    def file_line(self, block_line: int) -> int:
        """Map a 1-based line of the block content to the line in the original .vue file."""
        line = self.start_line + block_line - 1
        if block_line < 1 or line > self.end_line:
            raise ValueError("Line is outside the SFC block")
        return line


class SourceSpan(ContractModel):
    """Location in the original file: 1-based, end_line inclusive, never block-relative."""

    path: RepoPath
    start_line: PositiveInt
    end_line: PositiveInt
    sfc_block: SfcBlockKind | None = None

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.end_line < self.start_line:
            raise ValueError("end_line must not precede start_line")
        if self.sfc_block is not None and not self.path.endswith(".vue"):
            raise ValueError("sfc_block is only valid for .vue files")
        return self


class SymbolKind(StrEnum):
    MODULE = "module"
    COMPONENT = "component"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    VARIABLE = "variable"


class Symbol(ContractModel):
    symbol_id: Id
    snapshot_id: Id
    analysis_run_id: Id
    qualified_name: Label  # e.g. "Vue3Admin/src/router/index.ts#setupRouter"
    kind: SymbolKind
    exported: bool = False
    span: SourceSpan
