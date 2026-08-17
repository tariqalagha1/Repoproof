"""Runner domain enums."""

from enum import Enum


class EnvironmentState(str, Enum):
    CREATED = "created"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    DESTROYED = "destroyed"
    PAUSING = "pausing"
    RESUMING = "resuming"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


class NetworkPolicy(str, Enum):
    ISOLATED = "isolated"
    RESTRICTED = "restricted"
    OPEN = "open"


class ProvisioningFailure(str, Enum):
    NONE = "none"
    TIMEOUT = "timeout"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    IMAGE_PULL_FAILED = "image_pull_failed"
    NETWORK_ERROR = "network_error"
    PERMISSION_DENIED = "permission_denied"
    UNKNOWN = "unknown"
