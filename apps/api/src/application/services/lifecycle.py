"""Lifecycle transition management."""

from src.domain.enums import ALLOWED_TRANSITIONS, RunLifecycle


class InvalidTransitionError(ValueError):
    """Raised when a lifecycle transition is not allowed."""
    pass


def transition(current: RunLifecycle, target: RunLifecycle) -> RunLifecycle:
    """Validate and execute a lifecycle transition."""
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from {current.value} to {target.value}. "
            f"Allowed: {[a.value for a in allowed]}"
        )
    return target


def can_transition(current: RunLifecycle, target: RunLifecycle) -> bool:
    """Check if a transition is allowed."""
    return target in ALLOWED_TRANSITIONS.get(current, set())


def is_terminal(state: RunLifecycle) -> bool:
    """Check if a state is terminal (no allowed transitions)."""
    return len(ALLOWED_TRANSITIONS.get(state, set())) == 0
