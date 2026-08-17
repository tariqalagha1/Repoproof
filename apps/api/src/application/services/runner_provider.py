"""Runner provider interface + factory."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class EnvironmentSpec:
    image: str
    network_policy: str = "isolated"
    cpu_limit: str = "2.0"
    memory_limit: str = "2g"
    pids_limit: int = 100
    source_mount_path: str = "/workspace"
    read_only_root: bool = True


@dataclass
class ProvisionResult:
    success: bool
    environment_id: Optional[str] = None
    container_id: Optional[str] = None
    error: Optional[str] = None
    detail: Optional[str] = None


@dataclass
class IsolationTestResult:
    test_name: str
    passed: bool
    detail: str = ""


class RunnerProvider(ABC):
    """Abstract interface for runner backends (Docker, fake, etc.)."""

    @abstractmethod
    async def provision(self, job_id: str, spec: EnvironmentSpec) -> ProvisionResult:
        ...

    @abstractmethod
    async def destroy(self, environment_id: str) -> ProvisionResult:
        ...

    @abstractmethod
    async def health_check(self, environment_id: str) -> bool:
        ...

    @abstractmethod
    async def pause(self, environment_id: str) -> ProvisionResult:
        ...

    @abstractmethod
    async def resume(self, environment_id: str) -> ProvisionResult:
        ...

    @abstractmethod
    async def run_isolation_tests(self, environment_id: str) -> list[IsolationTestResult]:
        ...

    @abstractmethod
    async def execute_command(self, environment_id: str, command: str, timeout: int = 300) -> tuple[int, str, str]:
        """Run command and return (exit_code, stdout, stderr)."""
        ...


def create_runner_provider(provider_type: str = "fake") -> RunnerProvider:
    """Factory for runner providers."""
    if provider_type == "fake":
        from .fake_runner import ControlledFakeRunnerProvider
        return ControlledFakeRunnerProvider()
    if provider_type == "docker":
        from .docker_runner import DockerRunnerProvider
        return DockerRunnerProvider()
    # Default: fake
    from .fake_runner import ControlledFakeRunnerProvider
    return ControlledFakeRunnerProvider()
