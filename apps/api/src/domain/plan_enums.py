"""Plan domain enums."""

from enum import Enum


class PlanStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CommandSource(str, Enum):
    LLM = "llm"
    DETERMINISTIC = "deterministic"
    MANUAL = "manual"
    FALLBACK = "fallback"


class CommandConfidence(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class CommandExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMED_OUT = "timed_out"


class Ecosystem(str, Enum):
    PYTHON = "python"
    NODE = "node"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    DOTNET = "dotnet"
    RUBY = "ruby"
    PHP = "php"
    UNKNOWN = "unknown"
