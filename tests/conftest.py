"""
Pytest configuration for OpenGlider tests.

- Ensures tests/ is on sys.path so ``from common import ...`` works when run from project root.
- Registers the ``visual`` marker for visual/GUI tests.
- Marks all tests from modules named visual_test_*.py with @pytest.mark.visual (excluded by default).
"""
import sys
from pathlib import Path

import pytest

# Allow "from common import ..." when running pytest from project root
_tests_dir = Path(__file__).resolve().parent
if str(_tests_dir) not in sys.path:
    sys.path.insert(0, str(_tests_dir))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "visual: mark test as visual/GUI test (excluded by default, run with -m visual)",
    )


def pytest_collection_modifyitems(items):
    """Mark tests from visual_test_*.py modules with @pytest.mark.visual."""
    for item in items:
        try:
            mod = item.module
            if mod is not None and "visual_test" in (getattr(mod, "__name__", "") or ""):
                item.add_marker(pytest.mark.visual)
        except Exception:
            pass
