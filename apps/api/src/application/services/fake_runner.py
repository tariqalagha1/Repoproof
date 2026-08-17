"""ControlledFakeRunnerProvider — deterministic fake for testing."""

from uuid import uuid4

from .runner_provider import (
    EnvironmentSpec,
    IsolationTestResult,
    ProvisionResult,
    RunnerProvider,
)


class ControlledFakeRunnerProvider(RunnerProvider):
    """Fake runner with controlled behavior. Label: FAKE — TEST ONLY."""

    LABEL = "FAKE — TEST ONLY"

    def __init__(self):
        self._environments: dict[str, dict] = {}
        self._states: dict[str, str] = {}
        self._command_log: list[dict] = []
        self._next_provision_should_fail: bool = False
        self._next_destroy_should_fail: bool = False
        self._next_health_should_fail: bool = False

    # -- Control hooks for tests --
    def reset(self):
        self._environments.clear()
        self._states.clear()
        self._command_log.clear()
        self._next_provision_should_fail = False
        self._next_destroy_should_fail = False
        self._next_health_should_fail = False

    @property
    def environment_count(self) -> int:
        return len(self._environments)

    @property
    def command_log(self) -> list[dict]:
        return list(self._command_log)

    def get_state(self, env_id: str) -> str:
        return self._states.get(env_id, "unknown")

    # -- RunnerProvider impl --
    async def provision(self, job_id: str, spec: EnvironmentSpec) -> ProvisionResult:
        if self._next_provision_should_fail:
            self._next_provision_should_fail = False
            return ProvisionResult(success=False, error="FAKE_PROVISION_FAILURE")

        env_id = uuid4().hex
        container_id = uuid4().hex[:12]
        self._environments[env_id] = {
            "job_id": job_id,
            "spec": spec,
            "container_id": container_id,
        }
        self._states[env_id] = "running"
        return ProvisionResult(success=True, environment_id=env_id, container_id=container_id)

    async def destroy(self, environment_id: str) -> ProvisionResult:
        if self._next_destroy_should_fail:
            self._next_destroy_should_fail = False
            return ProvisionResult(success=False, error="FAKE_DESTROY_FAILURE")

        if environment_id in self._environments:
            del self._environments[environment_id]
            self._states[environment_id] = "destroyed"
        return ProvisionResult(success=True, environment_id=environment_id)

    async def health_check(self, environment_id: str) -> bool:
        if self._next_health_should_fail:
            self._next_health_should_fail = False
            return False
        return environment_id in self._environments

    async def pause(self, environment_id: str) -> ProvisionResult:
        if environment_id in self._states:
            self._states[environment_id] = "paused"
        return ProvisionResult(success=True, environment_id=environment_id)

    async def resume(self, environment_id: str) -> ProvisionResult:
        if environment_id in self._states:
            self._states[environment_id] = "running"
        return ProvisionResult(success=True, environment_id=environment_id)

    async def run_isolation_tests(self, environment_id: str) -> list[IsolationTestResult]:
        tests = [
            IsolationTestResult("network_isolated", True, "Network isolation verified"),
            IsolationTestResult("root_rw_blocked", True, "Root filesystem is read-only"),
            IsolationTestResult("capabilities_dropped", True, "All capabilities dropped"),
            IsolationTestResult("proc_masked", True, "Sensitive /proc paths masked"),
            IsolationTestResult("no_privilege_escalation", True, "No privilege escalation possible"),
            IsolationTestResult("pid_limit_enforced", True, "PID limit enforced"),
            IsolationTestResult("memory_limit_enforced", True, "Memory limit applied"),
            IsolationTestResult("cpu_limit_enforced", True, "CPU limit applied"),
            IsolationTestResult("disk_limit_enforced", True, "Disk usage limited"),
            IsolationTestResult("no_host_network", True, "No host network access"),
            IsolationTestResult("no_docker_socket", True, "Docker socket not mounted"),
            IsolationTestResult("no_host_mounts", True, "No host filesystem mounts"),
            IsolationTestResult("seccomp_enforced", True, "Seccomp profile active"),
            IsolationTestResult("apparmor_enforced", True, "AppArmor profile active"),
            IsolationTestResult("no_new_privs", True, "No new privileges allowed"),
            IsolationTestResult("user_namespace", True, "User namespace remapping active"),
        ]
        return tests

    async def execute_command(self, environment_id: str, command: str, timeout: int = 300) -> tuple[int, str, str]:
        self._command_log.append({"env": environment_id, "cmd": command, "timeout": timeout})
        if environment_id not in self._environments:
            return (1, "", "FAKE: environment not found")
        return (0, f"FAKE OUTPUT for: {command}", "")
