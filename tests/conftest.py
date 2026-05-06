import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def schemas_dir():
    return SCHEMAS_DIR


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def load_schema():
    def _load(name: str) -> dict:
        return json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())
    return _load
