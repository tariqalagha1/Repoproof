"""Migrations script metadata."""

import os

from alembic.script import ScriptDirectory


def get_revision() -> str:
    script = ScriptDirectory.from_config(
        os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    )
    head = script.get_current_head()
    return head or "001_initial"
