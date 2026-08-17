"""ProvisioningOrchestrator — manages environment lifecycle."""

from uuid import uuid4

from .fake_runner import ControlledFakeRunnerProvider
from .runner_provider import (
    EnvironmentSpec,
    ProvisionResult,
    RunnerProvider,
)


class ProvisioningOrchestrator:
    """Orchestrates environment provisioning, lifecycle management, and policy enforcement."""

    def __init__(self, runner: RunnerProvider):
        self.runner = runner
        self._provisioned: dict[str, dict] = {}

    async def provision_environment(
        self,
        job_id: str,
        image: str = "repoproof-runner:latest",
        network_policy: str = "isolated",
        cpu_limit: str = "2.0",
        memory_limit: str = "2g",
    ) -> ProvisionResult:
        """Provision an isolated environment for a master job."""
        spec = EnvironmentSpec(
            image=image,
            network_policy=network_policy,
            cpu_limit=cpu_limit,
            memory_limit=memory_limit,
        )
        result = await self.runner.provision(job_id, spec)
        if result.success and result.environment_id:
            self._provisioned[result.environment_id] = {
                "job_id": job_id,
                "spec": spec,
            }
        return result

    async def destroy_environment(self, environment_id: str) -> ProvisionResult:
        result = await self.runner.destroy(environment_id)
        if result.success:
            self._provisioned.pop(environment_id, None)
        return result

    async def pause_environment(self, environment_id: str) -> ProvisionResult:
        return await self.runner.pause(environment_id)

    async def resume_environment(self, environment_id: str) -> ProvisionResult:
        return await self.runner.resume(environment_id)

    async def run_isolation_tests(self, environment_id: str) -> list[dict]:
        results = await self.runner.run_isolation_tests(environment_id)
        return [
            {"test_name": r.test_name, "passed": r.passed, "detail": r.detail}
            for r in results
        ]

    async def execute_command(self, environment_id: str, command: str, timeout: int = 300) -> tuple[int, str, str]:
        return await self.runner.execute_command(environment_id, command, timeout)

    async def health_check(self, environment_id: str) -> bool:
        return await self.runner.health_check(environment_id)

    @property
    def active_environments(self) -> list[str]:
        return list(self._provisioned.keys())
