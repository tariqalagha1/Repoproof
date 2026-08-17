"""Unit tests — runner provider, fake runner, provisioning orchestrator."""

from src.domain.runner_enums import EnvironmentState, NetworkPolicy, ProvisioningFailure
from src.domain.runner_models import (
    RunnerEnvironment,
    SecurityProfile,
    ResourceLimits,
    SourceAttachment,
)
from src.application.services.runner_provider import (
    EnvironmentSpec,
    ProvisionResult,
    IsolationTestResult,
    create_runner_provider,
)
from src.application.services.fake_runner import ControlledFakeRunnerProvider
from src.application.services.provisioning import ProvisioningOrchestrator


# ═══════════════════════════════════════════════════════════
# Runner Domain Enums & Models
# ═══════════════════════════════════════════════════════════

class TestRunnerEnums:
    def test_environment_states(self):
        assert EnvironmentState.CREATED.value == "created"
        assert EnvironmentState.RUNNING.value == "running"
        assert EnvironmentState.DESTROYED.value == "destroyed"

    def test_network_policies(self):
        assert NetworkPolicy.ISOLATED.value == "isolated"
        assert NetworkPolicy.OPEN.value == "open"

    def test_provisioning_failures(self):
        assert ProvisioningFailure.NONE.value == "none"
        assert ProvisioningFailure.TIMEOUT.value == "timeout"


class TestRunnerModels:
    def test_runner_environment_defaults(self):
        env = RunnerEnvironment()
        assert env.state == EnvironmentState.CREATED
        assert env.network_policy == NetworkPolicy.ISOLATED

    def test_security_profile_defaults(self):
        sp = SecurityProfile()
        assert sp.read_only_root is True
        assert sp.no_new_privileges is True
        assert "ALL" in sp.drop_capabilities
        assert sp.allow_privilege_escalation is False

    def test_resource_limits_defaults(self):
        rl = ResourceLimits()
        assert rl.pids_limit == 100
        assert rl.memory_limit == "2g"

    def test_source_attachment_defaults(self):
        sa = SourceAttachment()
        assert sa.read_only is True
        assert sa.mount_path == "/workspace"


# ═══════════════════════════════════════════════════════════
# Runner Provider Factory
# ═══════════════════════════════════════════════════════════

class TestFactory:
    def test_fake_provider(self):
        assert isinstance(create_runner_provider("fake"), ControlledFakeRunnerProvider)

    def test_default_is_fake(self):
        assert isinstance(create_runner_provider(), ControlledFakeRunnerProvider)

    def test_unknown_provider_falls_back_to_fake(self):
        assert isinstance(create_runner_provider("bogus"), ControlledFakeRunnerProvider)


# ═══════════════════════════════════════════════════════════
# Fake Runner Provider
# ═══════════════════════════════════════════════════════════

class TestFakeRunner:
    async def test_provision_creates_environment(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        assert result.success
        assert result.environment_id is not None
        assert provider.environment_count == 1

    async def test_health_check(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        assert await provider.health_check(result.environment_id) is True

    async def test_destroy_removes_environment(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        destroy = await provider.destroy(result.environment_id)
        assert destroy.success
        assert provider.environment_count == 0
        assert await provider.health_check(result.environment_id) is False

    async def test_pause_and_resume(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        await provider.pause(result.environment_id)
        assert provider.get_state(result.environment_id) == "paused"
        await provider.resume(result.environment_id)
        assert provider.get_state(result.environment_id) == "running"

    async def test_isolation_tests_all_pass(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        tests = await provider.run_isolation_tests(result.environment_id)
        assert len(tests) == 16
        assert all(t.passed for t in tests)

    async def test_execute_command(self):
        provider = ControlledFakeRunnerProvider()
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        code, out, _ = await provider.execute_command(result.environment_id, "echo hi")
        assert code == 0
        assert "echo hi" in out

    async def test_provision_failure_hook(self):
        provider = ControlledFakeRunnerProvider()
        provider._next_provision_should_fail = True
        result = await provider.provision("job-1", EnvironmentSpec(image="test"))
        assert not result.success
        assert result.error == "FAKE_PROVISION_FAILURE"

    async def test_reset_clears_state(self):
        provider = ControlledFakeRunnerProvider()
        await provider.provision("job-1", EnvironmentSpec(image="test"))
        provider.reset()
        assert provider.environment_count == 0


# ═══════════════════════════════════════════════════════════
# Provisioning Orchestrator
# ═══════════════════════════════════════════════════════════

class TestProvisioningOrchestrator:
    async def test_provision_full_flow(self):
        orchestrator = ProvisioningOrchestrator(runner=ControlledFakeRunnerProvider())
        result = await orchestrator.provision_environment("job-1")
        assert result.success
        assert len(orchestrator.active_environments) == 1

    async def test_destroy_removes_active(self):
        orchestrator = ProvisioningOrchestrator(runner=ControlledFakeRunnerProvider())
        result = await orchestrator.provision_environment("job-1")
        destroy = await orchestrator.destroy_environment(result.environment_id)
        assert destroy.success
        assert orchestrator.active_environments == []

    async def test_run_isolation_tests(self):
        orchestrator = ProvisioningOrchestrator(runner=ControlledFakeRunnerProvider())
        result = await orchestrator.provision_environment("job-1")
        tests = await orchestrator.run_isolation_tests(result.environment_id)
        assert len(tests) == 16
        assert all(t["passed"] for t in tests)

    async def test_health_check(self):
        orchestrator = ProvisioningOrchestrator(runner=ControlledFakeRunnerProvider())
        result = await orchestrator.provision_environment("job-1")
        assert await orchestrator.health_check(result.environment_id) is True

    async def test_execute_command(self):
        orchestrator = ProvisioningOrchestrator(runner=ControlledFakeRunnerProvider())
        result = await orchestrator.provision_environment("job-1")
        code, out, _ = await orchestrator.execute_command(result.environment_id, "echo hi")
        assert code == 0
