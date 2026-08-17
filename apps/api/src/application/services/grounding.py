"""GroundingValidator — injection defense and output validation."""

import re


class GroundingValidator:
    """Validates LLM outputs against injection attacks and ensures they match the plan."""

    DANGEROUS_PATTERNS = [
        re.compile(r"rm\s+-rf\s+/"),
        re.compile(r">\s*/dev/sda"),
        re.compile(r"mkfs\."),
        re.compile(r"dd\s+if="),
        re.compile(r"chmod\s+777\s+/"),
        re.compile(r"curl.*\|\s*(ba)?sh"),
        re.compile(r"wget.*\|\s*(ba)?sh"),
        re.compile(r"eval\s+"),
        re.compile(r"exec\s+"),
    ]

    @classmethod
    def validate_command(cls, command: str) -> tuple[bool, str | None]:
        """Check a command for injection/dangerous patterns. Returns (safe, reason)."""
        if not command or not command.strip():
            return False, "Empty command"
        for pattern in cls.DANGEROUS_PATTERNS:
            if pattern.search(command):
                return False, f"Command matches dangerous pattern: {pattern.pattern}"
        return True, None

    @classmethod
    def sanitize_output(cls, output: str) -> str:
        """Strip potentially dangerous content from outputs."""
        # Remove ANSI escape codes
        output = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)
        # Truncate very long outputs
        if len(output) > 10000:
            output = output[:10000] + "\n... [truncated]"
        return output
