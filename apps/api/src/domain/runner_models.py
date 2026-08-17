"""Runner domain models."""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4
from typing import Optional

from .runner_enums import EnvironmentState, NetworkPolicy, ProvisioningFailure


@dataclass
class RunnerEnvironment:
    id: str = field(default_factory=lambda: uuid4().hex)
    master_job_id: str = ""
    state: EnvironmentState = EnvironmentState.CREATED
    container_id: Optional[str] = None
    image: str = ""
    network_policy: NetworkPolicy = NetworkPolicy.ISOLATED
    failure_reason: Optional[ProvisioningFailure] = None
    failure_detail: Optional[str] = None
    provisioned_at: Optional[datetime] = None
    destroyed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SecurityProfile:
    read_only_root: bool = True
    no_new_privileges: bool = True
    drop_capabilities: list[str] = field(default_factory=lambda: ["ALL"])
    masked_paths: list[str] = field(default_factory=lambda: [
        "/proc/kcore", "/proc/kallsyms", "/sys/kernel"
    ])
    seccomp_profile: str = "default"
    apparmor_profile: str = "docker-default"
    allow_privilege_escalation: bool = False


@dataclass
class ResourceLimits:
    cpu_limit: str = "2.0"
    memory_limit: str = "2g"
    pids_limit: int = 100
    disk_limit: str = "10g"
    network_egress_limit: str = "1m"


@dataclass
class SourceAttachment:
    source_path: str = ""
    mount_path: str = "/workspace"
    read_only: bool = True
    commit_hash: str = ""
    verified: bool = False
