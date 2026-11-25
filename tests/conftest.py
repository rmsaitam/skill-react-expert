import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "react-expert" / "scripts"
VALIDATORS = ROOT / "scripts"

for candidate in (SCRIPTS, VALIDATORS):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


@pytest.fixture(scope="session")
def root():
    return ROOT


@pytest.fixture(scope="session")
def fixtures():
    return ROOT / "tests" / "fixtures"


@pytest.fixture
def plugin_root(tmp_path):
    target = tmp_path / "plugin"
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".pytest_cache",
            ".venv",
            "__pycache__",
            ".coverage",
            "coverage.xml",
            "htmlcov",
        ),
    )
    return target
