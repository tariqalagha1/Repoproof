"""Phase 3 — Docker SDK Integration using docker-py.

Replaces subprocess-based Docker calls with proper SDK calls.
Supports container lifecycle, inspection, exec, and network management.
"""

from __future__ import annotations

import io
from typing import Any

import docker
from docker.errors import DockerException, NotFound


class DockerSDKRunner:
    """Docker container manager using docker-py SDK."""

    def __init__(self):
        try:
            self._client = docker.from_env()
            self._available = True
        except DockerException:
            self._client = None
            self._available = False

    def available(self) -> bool:
        return self._available

    @property
    def client(self) -> docker.DockerClient:
        if not self._client:
            raise RuntimeError("Docker not available")
        return self._client

    # ── Provision ───────────────────────────────────────

    def provision(
        self,
        name: str,
        image: str = "repoproof-runner:latest",
        memory_mb: int = 512,
        cpu_shares: int = 512,
        source_mount: str | None = None,
        source_mount_mode: str = "ro",
        network_mode: str = "bridge",
    ) -> dict[str, Any]:
        """Create and start a hardened verification container."""
        kwargs: dict[str, Any] = {
            "name": name,
            "image": image,
            "detach": True,
            "user": "1000:1000",
            "security_opt": ["no-new-privileges:true"],
            "cap_drop": ["ALL"],
            "read_only": True,
            "network_mode": network_mode,
            "mem_limit": f"{memory_mb}m",
            "memswap_limit": f"{memory_mb}m",
            "cpu_shares": cpu_shares,
            "pids_limit": 64,
            "init": True,
            "tmpfs": {
                "/tmp": "exec,size=128m,mode=1777",
                "/workspace": "exec,size=1g,mode=1777",
            },
            "environment": {"HOME": "/workspace"},
        }

        # Source mount
        if source_mount:
            kwargs["volumes"] = {
                source_mount: {"bind": "/source", "mode": source_mount_mode},
            }

        container = self.client.containers.run(**kwargs)

        # Isolate by default: disconnect from bridge immediately. Network is
        # re-enabled on demand via connect_network() for dependency installation.
        # (Docker refuses to connect a container that was started in "none" mode,
        # so we provision on bridge and disconnect to reach the isolated state.)
        try:
            self.client.networks.get("bridge").disconnect(container)
        except Exception:
            pass

        return {
            "id": container.id,
            "name": container.name,
            "status": container.status,
        }

    # ── Lifecycle ───────────────────────────────────────

    def destroy(self, container_id: str) -> bool:
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=True)
            return True
        except NotFound:
            return False

    def pause(self, container_id: str) -> bool:
        try:
            self.client.containers.get(container_id).pause()
            return True
        except NotFound:
            return False

    def unpause(self, container_id: str) -> bool:
        try:
            self.client.containers.get(container_id).unpause()
            return True
        except NotFound:
            return False

    # ── Inspect ────────────────────────────────────────

    def inspect(self, container_id: str) -> dict[str, Any] | None:
        try:
            c = self.client.containers.get(container_id)
            attrs = c.attrs
            host_config = attrs.get("HostConfig", {})
            config = attrs.get("Config", {})
            state = attrs.get("State", {})
            return {
                "id": attrs.get("Id", ""),
                "status": state.get("Status", "unknown"),
                "user": config.get("User", ""),
                "privileged": host_config.get("Privileged", False),
                "read_only": host_config.get("ReadonlyRootfs", False),
                "network_mode": host_config.get("NetworkMode", ""),
                "cap_drop": host_config.get("CapDrop", []),
                "memory": host_config.get("Memory", 0),
                "cpu_shares": host_config.get("CpuShares", 0),
                "security_opt": host_config.get("SecurityOpt", []),
                "init": host_config.get("Init", False),
                "pid_mode": host_config.get("PidMode", ""),
                "mounts": [m.get("Source", "") + ":" + m.get("Destination", "")
                           for m in attrs.get("Mounts", [])],
            }
        except NotFound:
            return None

    # ── Exec ───────────────────────────────────────────

    def exec_run(
        self,
        container_id: str,
        cmd: str | list[str],
        timeout: int = 30,
        workdir: str | None = None,
    ) -> tuple[int, str, str]:
        """Run command in container, return (exit_code, stdout, stderr)."""
        try:
            kwargs: dict[str, Any] = {}
            if workdir:
                kwargs["workdir"] = workdir

            if isinstance(cmd, str):
                result = self.client.containers.get(container_id).exec_run(
                    ["sh", "-c", cmd], **kwargs,
                )
            else:
                result = self.client.containers.get(container_id).exec_run(
                    cmd, **kwargs,
                )

            exit_code = result.exit_code or 0
            stdout = result.output.decode("utf-8", errors="replace") if result.output else ""
            stderr = ""
            return exit_code, stdout, stderr
        except Exception as e:
            return -1, "", str(e)

    # ── Network ────────────────────────────────────────

    def connect_network(self, container_id: str, network: str = "bridge") -> bool:
        try:
            net = self.client.networks.get(network)
            net.connect(container_id)
            return True
        except Exception:
            return False

    def disconnect_network(self, container_id: str, network: str = "bridge") -> bool:
        try:
            net = self.client.networks.get(network)
            net.disconnect(container_id)
            return True
        except Exception:
            return False

    # ── Health ─────────────────────────────────────────

    def health_check(self, container_id: str) -> bool:
        try:
            exit_code, stdout, _ = self.exec_run(container_id, "/healthcheck.sh")
            return exit_code == 0 and "OK" in stdout
        except Exception:
            return False

    def get_uid(self, container_id: str) -> str:
        try:
            _, stdout, _ = self.exec_run(container_id, "id")
            return stdout.strip()
        except Exception:
            return "unknown"
