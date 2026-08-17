"""Pytest configuration for RepoProof API tests.

Ensures the `src` package is importable and async tests run without
explicit markers.
"""

import os
import sys

# Make `src` importable regardless of how pytest is invoked.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark a test as async (auto mode)")
