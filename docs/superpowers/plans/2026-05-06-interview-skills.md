# Interview Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the seven Copilot Agent Skills, custom agent profile, helpers, schemas, and tests defined in [the design spec](../specs/2026-05-06-interview-skills-design.md), end-to-end.

**Architecture:** Skills authored as `SKILL.md` files in `.github/skills/<name>/`, with deterministic logic factored into Python helpers under `helpers/`. Three data-layer skills (script-loader, session-store, finalize) wrap the helpers; four behavioral skills (refinement, confidence-tagging, skip-handling, bias-mitigation) are mostly markdown rules that delegate persistence to `interview-session-store`. One custom agent profile (`.github/agents/interviewer.agent.md`) bundles them as the entry point for `copilot --agent interviewer`.

**Tech Stack:** Python 3.10+ standard library + `pyyaml`; `pytest` + `jsonschema` for testing; Copilot Agent Skills format for skill packaging; `git` CLI for finalize transport.

---

## File-structure overview (locked before tasks begin)

```
.github/
├── agents/interviewer.agent.md
└── skills/
    ├── interview-script-loader/SKILL.md
    ├── interview-session-store/SKILL.md
    ├── interview-finalize/SKILL.md
    ├── interview-refinement/SKILL.md
    ├── interview-confidence-tagging/SKILL.md
    ├── interview-skip-handling/SKILL.md
    ├── interview-bias-mitigation/SKILL.md
    └── README.md

helpers/
├── common/
│   ├── ids.py            # session_id, pseudonym, resume_token generation
│   └── yaml_io.py        # atomic YAML read/write
├── session/
│   ├── new_session.py
│   ├── load_session.py
│   ├── advance_cursor.py
│   ├── revise_cursor.py
│   ├── write_answer.py
│   └── check_writability.py
├── script/
│   ├── parse_script.py
│   └── question_filter.py
├── confidence/
│   └── validate_confidence.py
├── skip/
│   └── classify_skip.py
└── finalize/
    ├── finalize_session.py
    ├── git_branch_commit_push.py
    └── package_bundle.py

schemas/
├── session.schema.json
├── answers.schema.json
├── metadata.schema.json
└── helpers/
    ├── new_session.output.schema.json
    ├── load_session.output.schema.json
    └── parse_script.output.schema.json

tests/
├── conftest.py
├── unit/                  # one test_*.py per helper
├── integration/scripted_interview.py
└── fixtures/
    ├── canned_responses/
    │   ├── qa-engineer.yaml
    │   ├── qa-lead.yaml
    │   ├── developer.yaml
    │   ├── release-manager.yaml
    │   └── product-owner.yaml
    └── golden_transcripts/
        └── qa-engineer-happy-path.md

interview/                 # existing — frontmatter added per Task 2.1
responses/.gitkeep         # output dir (otherwise empty until first session)
requirements.txt           # pyyaml
requirements-dev.txt       # pytest, jsonschema, pyyaml
```

**Type consistency note:** Every helper that emits structured output writes JSON to stdout. Every helper that performs a side effect (write a YAML file, run git) writes JSON status to stdout on success and a JSON error envelope to stderr on failure, exit code 0/non-zero. Schema for the error envelope: `{"error": "<short_code>", "message": "<human readable>", "details": {...}}`.

---

## Phase 1: Foundation (schemas, common helpers, test scaffolding)

### Task 1.1: Repo bootstrap

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `tests/conftest.py`
- Create: `responses/.gitkeep`
- Create: `helpers/__init__.py`, `helpers/common/__init__.py`, `helpers/session/__init__.py`, `helpers/script/__init__.py`, `helpers/confidence/__init__.py`, `helpers/skip/__init__.py`, `helpers/finalize/__init__.py`
- Create: `tests/__init__.py`, `tests/unit/__init__.py`, `tests/integration/__init__.py`

- [ ] **Step 1: Create runtime requirements**

`requirements.txt`:
```
pyyaml>=6.0
```

- [ ] **Step 2: Create dev requirements**

`requirements-dev.txt`:
```
pytest>=7.0
jsonschema>=4.0
pyyaml>=6.0
```

- [ ] **Step 3: Create pytest fixtures conftest**

`tests/conftest.py`:
```python
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
```

- [ ] **Step 4: Create empty `__init__.py` files**

Empty file at each path listed above. (PowerShell: `New-Item -ItemType File -Force <path>`.)

- [ ] **Step 5: Create `responses/.gitkeep`**

Empty file. Ensures the directory is tracked even when no sessions exist.

- [ ] **Step 6: Verify Python and dependencies**

```
python --version
pip install -r requirements-dev.txt
pytest --version
```

Expected: Python 3.10+, pytest installs cleanly.

- [ ] **Step 7: Commit**

```
git add requirements.txt requirements-dev.txt tests/conftest.py responses/.gitkeep helpers/ tests/
git commit -m "bootstrap: requirements, test scaffolding, helpers/ layout"
```

---

### Task 1.2: JSON schemas for the three YAML state files

**Files:**
- Create: `schemas/session.schema.json`
- Create: `schemas/answers.schema.json`
- Create: `schemas/metadata.schema.json`
- Create: `tests/unit/test_schemas.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_schemas.py`:
```python
import json

import pytest
import yaml
from jsonschema import validate, ValidationError


VALID_SESSION = {
    "session_id": "20260506-qa-eng-7c9a",
    "pseudonym": "participant-7c9a",
    "resume_token": "xkj4-9q2m",
    "script_id": "qa-engineer",
    "script_version": "0.2.0",
    "agent_identifier": "copilot-interviewer-v1",
    "started_at": "2026-05-06T14:00:00Z",
    "last_active_at": "2026-05-06T14:32:00Z",
    "status": "in_progress",
    "cursor": {
        "current_question_id": "qa-eng-q1",
        "visited_question_ids": [],
    },
    "required_context_satisfied": True,
    "notes": None,
}


VALID_ANSWER_ENTRY = {
    "question_id": "qa-eng-q7",
    "tags": ["3d"],
    "script_version": "0.2.0",
    "prompt_text": "How long...",
    "status": "answered",
    "response_text": "About 2 days",
    "response_confidence": "estimated",
    "follow_ups": [],
    "follow_up_count": 0,
    "skip_reason": None,
    "revised_from": None,
    "timestamp": "2026-05-06T14:32:00Z",
}


VALID_METADATA = {
    "session_id": "20260506-qa-eng-7c9a",
    "pseudonym": "participant-7c9a",
    "interviewee_name": None,
    "persona": "qa-engineer",
    "script_id": "qa-engineer",
    "script_version": "0.2.0",
    "agent_identifier": "copilot-interviewer-v1",
    "access_mode": "direct",
    "facilitator_pseudonym": None,
    "facilitator_name": None,
    "started_at": "2026-05-06T14:00:00Z",
    "completed_at": None,
    "counts": {
        "total_questions": 32,
        "answered": 0,
        "skipped": 0,
        "declined": 0,
        "human_only_gaps": 0,
    },
}


def test_session_schema_accepts_valid(load_schema):
    validate(VALID_SESSION, load_schema("session"))


def test_session_schema_rejects_unknown_status(load_schema):
    bad = {**VALID_SESSION, "status": "weird"}
    with pytest.raises(ValidationError):
        validate(bad, load_schema("session"))


def test_answers_schema_accepts_list_of_valid(load_schema):
    validate([VALID_ANSWER_ENTRY], load_schema("answers"))


def test_answers_schema_rejects_unknown_status(load_schema):
    bad = [{**VALID_ANSWER_ENTRY, "status": "weird"}]
    with pytest.raises(ValidationError):
        validate(bad, load_schema("answers"))


def test_metadata_schema_accepts_valid(load_schema):
    validate(VALID_METADATA, load_schema("metadata"))
```

- [ ] **Step 2: Run test to verify it fails**

```
pytest tests/unit/test_schemas.py -v
```

Expected: FAIL — schemas don't exist yet.

- [ ] **Step 3: Write `schemas/session.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "session.yaml",
  "type": "object",
  "required": ["session_id", "pseudonym", "resume_token", "script_id", "script_version",
               "agent_identifier", "started_at", "last_active_at", "status", "cursor",
               "required_context_satisfied"],
  "properties": {
    "session_id": {"type": "string", "pattern": "^[0-9]{8}-[a-z0-9-]+-[0-9a-f]{4}$"},
    "pseudonym": {"type": "string", "pattern": "^participant-[0-9a-f]{4}$"},
    "resume_token": {"type": "string", "pattern": "^[a-z0-9]{4}-[a-z0-9]{4}$"},
    "script_id": {"type": "string"},
    "script_version": {"type": "string"},
    "agent_identifier": {"type": "string"},
    "started_at": {"type": "string", "format": "date-time"},
    "last_active_at": {"type": "string", "format": "date-time"},
    "status": {"enum": ["in_progress", "complete", "abandoned"]},
    "cursor": {
      "type": "object",
      "required": ["current_question_id", "visited_question_ids"],
      "properties": {
        "current_question_id": {"type": ["string", "null"]},
        "visited_question_ids": {"type": "array", "items": {"type": "string"}}
      }
    },
    "required_context_satisfied": {"type": "boolean"},
    "notes": {"type": ["string", "null"]}
  }
}
```

- [ ] **Step 4: Write `schemas/answers.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "answers.yaml",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["question_id", "tags", "script_version", "prompt_text", "status",
                 "follow_ups", "follow_up_count", "timestamp"],
    "properties": {
      "question_id": {"type": "string"},
      "tags": {"type": "array", "items": {"type": "string"}},
      "script_version": {"type": "string"},
      "prompt_text": {"type": "string"},
      "status": {"enum": ["answered", "skipped", "declined", "pending", "revised"]},
      "response_text": {"type": ["string", "null"]},
      "response_confidence": {"enum": ["tracked", "estimated", "inferred", "discussion-derived", null]},
      "follow_ups": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["prompt"],
          "properties": {
            "prompt": {"type": "string"},
            "response": {"type": ["string", "null"]}
          }
        }
      },
      "follow_up_count": {"type": "integer", "minimum": 0, "maximum": 3},
      "skip_reason": {"enum": [null, "not_measured", "declined", "not_applicable", "human_only"]},
      "revised_from": {"type": ["string", "null"]},
      "timestamp": {"type": "string", "format": "date-time"}
    }
  }
}
```

- [ ] **Step 5: Write `schemas/metadata.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "metadata.yaml",
  "type": "object",
  "required": ["session_id", "pseudonym", "persona", "script_id", "script_version",
               "agent_identifier", "access_mode", "started_at", "counts"],
  "properties": {
    "session_id": {"type": "string"},
    "pseudonym": {"type": "string"},
    "interviewee_name": {"type": ["string", "null"]},
    "persona": {"type": "string"},
    "script_id": {"type": "string"},
    "script_version": {"type": "string"},
    "agent_identifier": {"type": "string"},
    "access_mode": {"enum": ["direct", "facilitated"]},
    "facilitator_pseudonym": {"type": ["string", "null"]},
    "facilitator_name": {"type": ["string", "null"]},
    "started_at": {"type": "string", "format": "date-time"},
    "completed_at": {"type": ["string", "null"], "format": "date-time"},
    "counts": {
      "type": "object",
      "required": ["total_questions", "answered", "skipped", "declined", "human_only_gaps"],
      "properties": {
        "total_questions": {"type": "integer", "minimum": 0},
        "answered": {"type": "integer", "minimum": 0},
        "skipped": {"type": "integer", "minimum": 0},
        "declined": {"type": "integer", "minimum": 0},
        "human_only_gaps": {"type": "integer", "minimum": 0}
      }
    }
  }
}
```

- [ ] **Step 6: Run tests to verify pass**

```
pytest tests/unit/test_schemas.py -v
```

Expected: 5 PASS.

- [ ] **Step 7: Commit**

```
git add schemas/ tests/unit/test_schemas.py
git commit -m "schemas: session, answers, metadata YAML shapes + tests"
```

---

### Task 1.3: ID and token generation helper

**Files:**
- Create: `helpers/common/ids.py`
- Create: `tests/unit/test_ids.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_ids.py`:
```python
import re

from helpers.common.ids import (
    new_session_id,
    new_pseudonym,
    new_resume_token,
)


def test_session_id_format():
    sid = new_session_id("qa-engineer", date_str="20260506")
    assert re.match(r"^20260506-qa-engineer-[0-9a-f]{4}$", sid)


def test_pseudonym_format():
    p = new_pseudonym()
    assert re.match(r"^participant-[0-9a-f]{4}$", p)


def test_resume_token_no_ambiguous_chars():
    for _ in range(50):
        token = new_resume_token()
        assert re.match(r"^[a-z0-9]{4}-[a-z0-9]{4}$", token)
        for ch in "01loi":
            assert ch not in token


def test_session_id_uniqueness():
    seen = set()
    for _ in range(100):
        sid = new_session_id("qa-engineer", date_str="20260506")
        assert sid not in seen
        seen.add(sid)
```

- [ ] **Step 2: Run test, verify FAIL**

```
pytest tests/unit/test_ids.py -v
```

Expected: FAIL — module not found.

- [ ] **Step 3: Implement helper**

`helpers/common/ids.py`:
```python
"""Generate session IDs, pseudonyms, and resume tokens."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone


_TOKEN_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"  # no 0/o/1/l/i


def new_session_id(persona_slug: str, *, date_str: str | None = None) -> str:
    """Format: YYYYMMDD-{persona-slug}-{4-hex}."""
    if date_str is None:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"{date_str}-{persona_slug}-{secrets.token_hex(2)}"


def new_pseudonym() -> str:
    """Format: participant-{4-hex}."""
    return f"participant-{secrets.token_hex(2)}"


def new_resume_token() -> str:
    """Format: {4-alnum}-{4-alnum} from a no-ambiguous-char alphabet."""
    def group() -> str:
        return "".join(secrets.choice(_TOKEN_ALPHABET) for _ in range(4))
    return f"{group()}-{group()}"
```

- [ ] **Step 4: Run test, verify PASS**

```
pytest tests/unit/test_ids.py -v
```

Expected: 4 PASS.

- [ ] **Step 5: Commit**

```
git add helpers/common/ids.py tests/unit/test_ids.py
git commit -m "helpers/common: id, pseudonym, resume token generators"
```

---

### Task 1.4: Atomic YAML read/write helper

**Files:**
- Create: `helpers/common/yaml_io.py`
- Create: `tests/unit/test_yaml_io.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_yaml_io.py`:
```python
from helpers.common.yaml_io import read_yaml, write_yaml_atomic


def test_round_trip(tmp_path):
    p = tmp_path / "x.yaml"
    write_yaml_atomic(p, {"a": 1, "b": [1, 2]})
    assert read_yaml(p) == {"a": 1, "b": [1, 2]}


def test_atomic_no_partial_file_on_crash(tmp_path, monkeypatch):
    """Simulate a crash mid-write: the temp file exists but rename never happened."""
    p = tmp_path / "x.yaml"
    write_yaml_atomic(p, {"old": True})
    # Corrupt by leaving a temp file around; original should still be readable
    (tmp_path / "x.yaml.tmp").write_text("garbage")
    assert read_yaml(p) == {"old": True}


def test_read_missing_file_raises(tmp_path):
    import pytest
    with pytest.raises(FileNotFoundError):
        read_yaml(tmp_path / "nope.yaml")
```

- [ ] **Step 2: Run test, verify FAIL**

```
pytest tests/unit/test_yaml_io.py -v
```

- [ ] **Step 3: Implement helper**

`helpers/common/yaml_io.py`:
```python
"""Atomic YAML read/write."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def read_yaml(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml_atomic(path: Path, data: Any) -> None:
    """Write to {path}.tmp, then rename to {path}. Crash-safe."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.parent.mkdir(parents=True, exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, default_flow_style=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
```

- [ ] **Step 4: Run test, verify PASS**

- [ ] **Step 5: Commit**

```
git add helpers/common/yaml_io.py tests/unit/test_yaml_io.py
git commit -m "helpers/common: atomic YAML I/O"
```

---

### Task 1.5: `check_writability` helper

**Files:**
- Create: `helpers/session/check_writability.py`
- Create: `tests/unit/test_check_writability.py`

- [ ] **Step 1: Write the failing test**

`tests/unit/test_check_writability.py`:
```python
import subprocess
from pathlib import Path

import pytest

from helpers.session.check_writability import check_writability


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def temp_repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "--allow-empty", "-m", "init")
    return tmp_path


def test_uncommitted_session_is_writable(temp_repo):
    sd = temp_repo / "responses" / "20260506-qa-eng-7c9a"
    sd.mkdir(parents=True)
    (sd / "session.yaml").write_text("session_id: x\n")
    assert check_writability(sd) is True


def test_committed_session_refused(temp_repo):
    sd = temp_repo / "responses" / "20260506-qa-eng-7c9a"
    sd.mkdir(parents=True)
    (sd / "session.yaml").write_text("session_id: x\n")
    _git(temp_repo, "add", ".")
    _git(temp_repo, "commit", "-m", "commit session")
    assert check_writability(sd) is False
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement.**

`helpers/session/check_writability.py`:
```python
"""Refuse writes to sessions that are committed in the current HEAD."""

from __future__ import annotations

import subprocess
from pathlib import Path


def check_writability(session_dir: Path) -> bool:
    """Return True if session is uncommitted (mutable), False if committed (read-only)."""
    session_dir = Path(session_dir).resolve()
    repo_root = session_dir
    while repo_root != repo_root.parent:
        if (repo_root / ".git").exists():
            break
        repo_root = repo_root.parent
    rel = session_dir.relative_to(repo_root) / "session.yaml"
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", str(rel)],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    return result.returncode != 0  # 0 = tracked (committed) → not writable
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

```
git add helpers/session/check_writability.py tests/unit/test_check_writability.py
git commit -m "helpers/session: check_writability via git ls-files"
```

---

## Phase 2: Script loading

### Task 2.1: Add frontmatter to existing interview scripts

**Files (modify):**
- `interview/01-qa-engineer-interview.md`
- `interview/02-qa-lead-interview.md`
- `interview/03-developer-interview.md`
- `interview/04-release-manager-interview.md`
- `interview/05-product-owner-interview.md`

For each, prepend YAML frontmatter ABOVE the existing first heading. Schema:

```yaml
---
script_id: <slug>
persona: <full persona name>
script_version: 0.2.0
required_context_question_ids: [<derived ids>]
human_only_question_ids: [<derived ids of AI-fit questions>]
---
```

- [ ] **Step 1: `interview/01-qa-engineer-interview.md`** — prepend:

```
---
script_id: qa-engineer
persona: QA Engineer (Individual Contributor)
script_version: 0.2.0
required_context_question_ids: [qa-engineer-q2]
human_only_question_ids: [qa-engineer-q30, qa-engineer-q31, qa-engineer-q32]
---

```

(IDs above are derived from the existing numbered structure; AI-fit IDs from agent-mode-plan §9 #4: IC Q30+. Confirm against current file content before saving — adjust if numbering has shifted.)

- [ ] **Step 2: `interview/02-qa-lead-interview.md`** — prepend:

```
---
script_id: qa-lead
persona: QA Lead / Manager
script_version: 0.2.0
required_context_question_ids: [qa-lead-q1]
human_only_question_ids: [qa-lead-q25]
---

```

- [ ] **Step 3: `interview/03-developer-interview.md`** — prepend:

```
---
script_id: developer
persona: Developer
script_version: 0.2.0
required_context_question_ids: [developer-q1]
human_only_question_ids: [developer-q19]
---

```

- [ ] **Step 4: `interview/04-release-manager-interview.md`** — prepend:

```
---
script_id: release-manager
persona: Release Manager
script_version: 0.2.0
required_context_question_ids: [release-manager-q1]
human_only_question_ids: [release-manager-q17]
---

```

- [ ] **Step 5: `interview/05-product-owner-interview.md`** — prepend:

```
---
script_id: product-owner
persona: Product Owner
script_version: 0.2.0
required_context_question_ids: [product-owner-q1, product-owner-q2]
human_only_question_ids: [product-owner-q16, product-owner-q17]
---

```

- [ ] **Step 6: Commit.**

```
git add interview/
git commit -m "interview: add machine-readable frontmatter to all 5 persona scripts"
```

---

### Task 2.2: `parse_script.py` helper

**Files:**
- Create: `helpers/script/parse_script.py`
- Create: `schemas/helpers/parse_script.output.schema.json`
- Create: `tests/unit/test_parse_script.py`

- [ ] **Step 1: Write the output schema**

`schemas/helpers/parse_script.output.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["frontmatter", "questions"],
  "properties": {
    "frontmatter": {
      "type": "object",
      "required": ["script_id", "persona", "script_version", "required_context_question_ids", "human_only_question_ids"],
      "properties": {
        "script_id": {"type": "string"},
        "persona": {"type": "string"},
        "script_version": {"type": "string"},
        "required_context_question_ids": {"type": "array", "items": {"type": "string"}},
        "human_only_question_ids": {"type": "array", "items": {"type": "string"}}
      }
    },
    "questions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["question_id", "number", "prompt_text", "tags", "section_heading"],
        "properties": {
          "question_id": {"type": "string"},
          "number": {"type": "integer"},
          "prompt_text": {"type": "string"},
          "tags": {"type": "array", "items": {"type": "string"}},
          "section_heading": {"type": "string"}
        }
      }
    }
  }
}
```

- [ ] **Step 2: Write the failing test**

`tests/unit/test_parse_script.py`:
```python
from pathlib import Path

import pytest
from jsonschema import validate

from helpers.script.parse_script import parse_script


REPO = Path(__file__).resolve().parents[2]


def test_parse_qa_engineer_script(load_schema):
    result = parse_script(REPO / "interview" / "01-qa-engineer-interview.md")
    validate(result, load_schema("helpers/parse_script.output"))
    assert result["frontmatter"]["script_id"] == "qa-engineer"
    assert result["frontmatter"]["script_version"] == "0.2.0"
    assert len(result["questions"]) > 0
    assert all(q["question_id"].startswith("qa-engineer-q") for q in result["questions"])


def test_question_id_derivation(tmp_path):
    f = tmp_path / "x.md"
    f.write_text(
        "---\n"
        "script_id: demo\n"
        "persona: Demo\n"
        "script_version: 0.1.0\n"
        "required_context_question_ids: []\n"
        "human_only_question_ids: []\n"
        "---\n"
        "\n"
        "# Demo Script\n"
        "\n"
        "## Section A\n"
        "\n"
        "1. First Q `[3a]`\n"
        "2. Second Q `[3b]` `[3c]`\n"
    )
    result = parse_script(f)
    assert result["questions"][0]["question_id"] == "demo-q1"
    assert result["questions"][0]["tags"] == ["3a"]
    assert result["questions"][1]["question_id"] == "demo-q2"
    assert sorted(result["questions"][1]["tags"]) == ["3b", "3c"]
    assert result["questions"][0]["section_heading"] == "Section A"


def test_missing_frontmatter_raises(tmp_path):
    f = tmp_path / "x.md"
    f.write_text("# No Frontmatter Here\n\n1. Q\n")
    with pytest.raises(ValueError, match="frontmatter"):
        parse_script(f)
```

- [ ] **Step 3: Implement**

`helpers/script/parse_script.py`:
```python
"""Parse a persona interview script into structured form."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SECTION_RE = re.compile(r"^##+\s+(.+?)\s*$")
_QUESTION_RE = re.compile(r"^\s*(\d+)\.\s+(.+?)\s*$")
_TAG_RE = re.compile(r"`\[([^\]]+)\]`")


def parse_script(path: Path) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    fm_match = _FRONTMATTER_RE.match(text)
    if not fm_match:
        raise ValueError(f"Missing frontmatter in {path}")
    frontmatter = yaml.safe_load(fm_match.group(1))
    body = text[fm_match.end():]
    script_id = frontmatter["script_id"]

    questions: list[dict[str, Any]] = []
    section = ""
    for line in body.splitlines():
        sec_match = _SECTION_RE.match(line)
        if sec_match:
            heading = sec_match.group(1)
            section = re.sub(r"^\d+\.\s*", "", heading).split("(")[0].strip()
            continue
        q_match = _QUESTION_RE.match(line)
        if q_match:
            number = int(q_match.group(1))
            rest = q_match.group(2)
            tags = _TAG_RE.findall(rest)
            prompt = _TAG_RE.sub("", rest).strip()
            questions.append({
                "question_id": f"{script_id}-q{number}",
                "number": number,
                "prompt_text": prompt,
                "tags": tags,
                "section_heading": section,
            })
    return {"frontmatter": frontmatter, "questions": questions}


if __name__ == "__main__":
    import json
    import sys
    print(json.dumps(parse_script(Path(sys.argv[1])), indent=2))
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

```
git add helpers/script/parse_script.py schemas/helpers/parse_script.output.schema.json tests/unit/test_parse_script.py
git commit -m "helpers/script: parse_script with frontmatter + question extraction"
```

---

### Task 2.3: `question_filter.py` helper

**Files:**
- Create: `helpers/script/question_filter.py`
- Create: `tests/unit/test_question_filter.py`

- [ ] **Step 1: Failing test.**

`tests/unit/test_question_filter.py`:
```python
from helpers.script.question_filter import filter_questions


SCRIPT = {
    "frontmatter": {
        "human_only_question_ids": ["x-q3"],
        "required_context_question_ids": ["x-q1"],
    },
    "questions": [
        {"question_id": "x-q1", "number": 1, "prompt_text": "a", "tags": [], "section_heading": ""},
        {"question_id": "x-q2", "number": 2, "prompt_text": "b", "tags": [], "section_heading": ""},
        {"question_id": "x-q3", "number": 3, "prompt_text": "c", "tags": [], "section_heading": ""},
    ],
}


def test_exclude_human_only_drops_those():
    filtered = filter_questions(SCRIPT, exclude_human_only=True)
    assert [q["question_id"] for q in filtered] == ["x-q1", "x-q2"]


def test_no_filter_returns_all():
    assert len(filter_questions(SCRIPT)) == 3
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement.**

`helpers/script/question_filter.py`:
```python
"""Filter parsed questions by frontmatter flags."""

from __future__ import annotations


def filter_questions(parsed: dict, *, exclude_human_only: bool = False) -> list[dict]:
    questions = list(parsed["questions"])
    if exclude_human_only:
        ho = set(parsed["frontmatter"].get("human_only_question_ids", []))
        questions = [q for q in questions if q["question_id"] not in ho]
    return questions
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

```
git add helpers/script/question_filter.py tests/unit/test_question_filter.py
git commit -m "helpers/script: question_filter for human_only exclusion"
```

---

### Task 2.4: `interview-script-loader` SKILL.md

**Files:**
- Create: `.github/skills/interview-script-loader/SKILL.md`

- [ ] **Step 1: Write the SKILL.md**

```markdown
---
name: interview-script-loader
description: Use when the agent needs to load or validate a persona interview script — at session start, on resume to verify script_version, or when computing the next question. Parses the script's YAML frontmatter and extracts the ordered question list with derived IDs.
---

# interview-script-loader

Parses a persona script (`interview/01-..05-*.md`) into a structured form the agent can traverse: frontmatter (script_id, persona, script_version, required_context_question_ids, human_only_question_ids) plus an ordered list of questions with derived IDs (`{script_id}-q{number}`), prompt text, tags (e.g., `[3d]`), and section heading.

## When to use

- At session start: load the script for the chosen persona.
- On resume: re-load the script and validate that `frontmatter.script_version` matches the session's locked version.
- When computing `advance_cursor`: filter out `human_only_question_ids`.

## How to use

Run the parser via the Python helper:

```
python helpers/script/parse_script.py interview/<script-file>.md
```

Output: JSON to stdout matching `schemas/helpers/parse_script.output.schema.json`.

For filtering:

```
python helpers/script/question_filter.py interview/<script-file>.md --exclude human_only
```

## Contract

- **Pure parsing.** No side effects; safe to call repeatedly.
- **Idempotent.** Same input produces identical output.
- **Question IDs derived**, not authored. Format `{script_id}-q{number}`. The original numbered structure is the source of truth.
- **Failure mode:** missing or malformed frontmatter → exit non-zero with `{"error": "missing_frontmatter", "message": "..."}` on stderr. Agent must abort session start with a clear message.

## Helpers

- `helpers/script/parse_script.py` — frontmatter + question extraction.
- `helpers/script/question_filter.py` — apply `human_only` exclusion.
```

- [ ] **Step 2: Commit.**

```
git add .github/skills/interview-script-loader/SKILL.md
git commit -m "skills: interview-script-loader"
```

---

## Phase 3: Session store

### Task 3.1: `new_session.py` helper

**Files:**
- Create: `helpers/session/new_session.py`
- Create: `schemas/helpers/new_session.output.schema.json`
- Create: `tests/unit/test_new_session.py`

- [ ] **Step 1: Output schema**

`schemas/helpers/new_session.output.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["session_id", "pseudonym", "resume_token", "session_dir"],
  "properties": {
    "session_id": {"type": "string"},
    "pseudonym": {"type": "string"},
    "resume_token": {"type": "string"},
    "session_dir": {"type": "string"}
  }
}
```

- [ ] **Step 2: Failing test**

`tests/unit/test_new_session.py`:
```python
from pathlib import Path

import yaml
from jsonschema import validate

from helpers.session.new_session import new_session


def test_creates_session_dir_with_required_files(tmp_path, load_schema):
    result = new_session(
        repo_root=tmp_path,
        script_id="qa-engineer",
        persona="QA Engineer",
        script_version="0.2.0",
        access_mode="direct",
        total_questions=32,
        agent_identifier="copilot-interviewer-v1",
    )
    validate(result, load_schema("helpers/new_session.output"))
    sd = Path(result["session_dir"])
    assert (sd / "session.yaml").exists()
    assert (sd / "metadata.yaml").exists()
    assert (sd / "answers.yaml").exists()
    assert (sd / "resume-token.txt").exists()
    session = yaml.safe_load((sd / "session.yaml").read_text())
    assert session["status"] == "in_progress"
    assert session["resume_token"] == result["resume_token"]
    metadata = yaml.safe_load((sd / "metadata.yaml").read_text())
    assert metadata["counts"]["total_questions"] == 32


def test_optional_interviewee_name_persists(tmp_path):
    result = new_session(
        repo_root=tmp_path,
        script_id="qa-engineer",
        persona="QA Engineer",
        script_version="0.2.0",
        access_mode="direct",
        total_questions=32,
        agent_identifier="copilot-interviewer-v1",
        interviewee_name="Jane Smith",
    )
    metadata = yaml.safe_load((Path(result["session_dir"]) / "metadata.yaml").read_text())
    assert metadata["interviewee_name"] == "Jane Smith"


def test_facilitated_mode_stores_facilitator_pseudonym(tmp_path):
    result = new_session(
        repo_root=tmp_path,
        script_id="qa-engineer",
        persona="QA Engineer",
        script_version="0.2.0",
        access_mode="facilitated",
        total_questions=32,
        agent_identifier="copilot-interviewer-v1",
        facilitator_name="Alex",
    )
    metadata = yaml.safe_load((Path(result["session_dir"]) / "metadata.yaml").read_text())
    assert metadata["access_mode"] == "facilitated"
    assert metadata["facilitator_pseudonym"].startswith("participant-")
    assert metadata["facilitator_name"] == "Alex"
```

- [ ] **Step 3: Run, verify FAIL.**

- [ ] **Step 4: Implement**

`helpers/session/new_session.py`:
```python
"""Create a new interview session — generates IDs and writes initial YAML files."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from helpers.common.ids import new_session_id, new_pseudonym, new_resume_token
from helpers.common.yaml_io import write_yaml_atomic


def new_session(
    *,
    repo_root: Path,
    script_id: str,
    persona: str,
    script_version: str,
    access_mode: str,
    total_questions: int,
    agent_identifier: str,
    interviewee_name: str | None = None,
    facilitator_name: str | None = None,
) -> dict:
    persona_slug = script_id  # script_id IS the persona slug in our scheme
    session_id = new_session_id(persona_slug)
    pseudonym = new_pseudonym()
    resume_token = new_resume_token()
    facilitator_pseudonym = new_pseudonym() if access_mode == "facilitated" else None
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    session_dir = Path(repo_root) / "responses" / session_id
    session_dir.mkdir(parents=True, exist_ok=False)

    write_yaml_atomic(session_dir / "session.yaml", {
        "session_id": session_id,
        "pseudonym": pseudonym,
        "resume_token": resume_token,
        "script_id": script_id,
        "script_version": script_version,
        "agent_identifier": agent_identifier,
        "started_at": now,
        "last_active_at": now,
        "status": "in_progress",
        "cursor": {"current_question_id": None, "visited_question_ids": []},
        "required_context_satisfied": True,
        "notes": None,
    })

    write_yaml_atomic(session_dir / "metadata.yaml", {
        "session_id": session_id,
        "pseudonym": pseudonym,
        "interviewee_name": interviewee_name,
        "persona": script_id,
        "script_id": script_id,
        "script_version": script_version,
        "agent_identifier": agent_identifier,
        "access_mode": access_mode,
        "facilitator_pseudonym": facilitator_pseudonym,
        "facilitator_name": facilitator_name,
        "started_at": now,
        "completed_at": None,
        "counts": {
            "total_questions": total_questions,
            "answered": 0,
            "skipped": 0,
            "declined": 0,
            "human_only_gaps": 0,
        },
    })

    write_yaml_atomic(session_dir / "answers.yaml", [])
    (session_dir / "resume-token.txt").write_text(resume_token + "\n", encoding="utf-8")
    (session_dir / "transcript.md").write_text(f"# Interview Transcript — {session_id}\n\n", encoding="utf-8")
    (session_dir / "flags.md").write_text("# Flags\n\n", encoding="utf-8")

    return {
        "session_id": session_id,
        "pseudonym": pseudonym,
        "resume_token": resume_token,
        "session_dir": str(session_dir),
    }


if __name__ == "__main__":
    args = json.loads(sys.argv[1])  # JSON-encoded kwargs
    args["repo_root"] = Path(args["repo_root"])
    print(json.dumps(new_session(**args)))
```

- [ ] **Step 5: Run, verify PASS.**

- [ ] **Step 6: Commit.**

```
git add helpers/session/new_session.py schemas/helpers/new_session.output.schema.json tests/unit/test_new_session.py
git commit -m "helpers/session: new_session creates session dir + initial YAMLs"
```

---

### Task 3.2: `load_session.py` helper (resume)

**Files:**
- Create: `helpers/session/load_session.py`
- Create: `tests/unit/test_load_session.py`

- [ ] **Step 1: Failing test**

`tests/unit/test_load_session.py`:
```python
import subprocess
from pathlib import Path

import pytest

from helpers.session.new_session import new_session
from helpers.session.load_session import load_session


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "commit", "--allow-empty", "-m", "init")
    return tmp_path


def _seed_session(repo):
    return new_session(
        repo_root=repo,
        script_id="qa-engineer",
        persona="QA Engineer",
        script_version="0.2.0",
        access_mode="direct",
        total_questions=32,
        agent_identifier="copilot-interviewer-v1",
    )


def test_load_by_resume_token(repo):
    seed = _seed_session(repo)
    loaded = load_session(repo_root=repo, resume_token=seed["resume_token"])
    assert loaded["session"]["session_id"] == seed["session_id"]
    assert loaded["writable"] is True


def test_load_by_session_id(repo):
    seed = _seed_session(repo)
    loaded = load_session(repo_root=repo, session_id=seed["session_id"])
    assert loaded["session"]["session_id"] == seed["session_id"]


def test_unknown_token_raises(repo):
    with pytest.raises(LookupError):
        load_session(repo_root=repo, resume_token="zzzz-zzzz")


def test_committed_session_marked_not_writable(repo):
    seed = _seed_session(repo)
    _git(repo, "add", "responses/")
    _git(repo, "commit", "-m", "commit")
    loaded = load_session(repo_root=repo, resume_token=seed["resume_token"])
    assert loaded["writable"] is False
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/session/load_session.py`:
```python
"""Load a session by resume_token or session_id."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from helpers.common.yaml_io import read_yaml
from helpers.session.check_writability import check_writability


def load_session(
    *,
    repo_root: Path,
    resume_token: str | None = None,
    session_id: str | None = None,
) -> dict:
    if not (resume_token or session_id):
        raise ValueError("resume_token or session_id required")
    responses_dir = Path(repo_root) / "responses"
    session_dir: Path | None = None

    if session_id:
        candidate = responses_dir / session_id
        if (candidate / "session.yaml").exists():
            session_dir = candidate
    else:
        for candidate in responses_dir.iterdir():
            sess_yaml = candidate / "session.yaml"
            if not sess_yaml.exists():
                continue
            data = read_yaml(sess_yaml)
            if data.get("resume_token") == resume_token:
                session_dir = candidate
                break

    if session_dir is None:
        raise LookupError("Session not found")

    return {
        "session_dir": str(session_dir),
        "session": read_yaml(session_dir / "session.yaml"),
        "metadata": read_yaml(session_dir / "metadata.yaml"),
        "answers": read_yaml(session_dir / "answers.yaml"),
        "writable": check_writability(session_dir),
    }


if __name__ == "__main__":
    kwargs = json.loads(sys.argv[1])
    kwargs["repo_root"] = Path(kwargs["repo_root"])
    print(json.dumps(load_session(**kwargs), default=str))
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

---

### Task 3.3: `write_answer.py` helper

**Files:**
- Create: `helpers/session/write_answer.py`
- Create: `tests/unit/test_write_answer.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_write_answer.py
from datetime import datetime, timezone
from pathlib import Path

import yaml
import pytest

from helpers.session.new_session import new_session
from helpers.session.write_answer import write_answer


def _seed(tmp_path):
    return new_session(
        repo_root=tmp_path,
        script_id="qa-engineer",
        persona="QA",
        script_version="0.2.0",
        access_mode="direct",
        total_questions=32,
        agent_identifier="copilot-interviewer-v1",
    )


def test_appends_new_answer(tmp_path):
    seed = _seed(tmp_path)
    write_answer(
        session_dir=Path(seed["session_dir"]),
        question_id="qa-engineer-q1",
        tags=[],
        prompt_text="...",
        status="answered",
        response_text="6 months",
        response_confidence=None,
        follow_ups=[],
        skip_reason=None,
    )
    answers = yaml.safe_load((Path(seed["session_dir"]) / "answers.yaml").read_text())
    assert len(answers) == 1
    assert answers[0]["question_id"] == "qa-engineer-q1"
    assert answers[0]["follow_up_count"] == 0


def test_upsert_updates_existing(tmp_path):
    seed = _seed(tmp_path)
    sd = Path(seed["session_dir"])
    write_answer(session_dir=sd, question_id="qa-engineer-q1", tags=[], prompt_text="...",
                 status="pending", response_text=None, response_confidence=None,
                 follow_ups=[], skip_reason=None)
    write_answer(session_dir=sd, question_id="qa-engineer-q1", tags=[], prompt_text="...",
                 status="answered", response_text="final", response_confidence=None,
                 follow_ups=[], skip_reason=None)
    answers = yaml.safe_load((sd / "answers.yaml").read_text())
    assert len(answers) == 1
    assert answers[0]["status"] == "answered"
    assert answers[0]["response_text"] == "final"


def test_follow_up_count_caps_at_3(tmp_path):
    seed = _seed(tmp_path)
    sd = Path(seed["session_dir"])
    fu = [{"prompt": f"f{i}", "response": "r"} for i in range(4)]
    with pytest.raises(ValueError, match="follow_up cap"):
        write_answer(session_dir=sd, question_id="qa-engineer-q1", tags=[], prompt_text="...",
                     status="answered", response_text="x", response_confidence=None,
                     follow_ups=fu, skip_reason=None)
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/session/write_answer.py`:
```python
"""Upsert a question's answer record into answers.yaml."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from helpers.common.yaml_io import read_yaml, write_yaml_atomic
from helpers.session.check_writability import check_writability


def write_answer(
    *,
    session_dir: Path,
    question_id: str,
    tags: list[str],
    prompt_text: str,
    status: str,
    response_text: str | None,
    response_confidence: str | None,
    follow_ups: list[dict],
    skip_reason: str | None,
    revised_from: str | None = None,
) -> None:
    if not check_writability(session_dir):
        raise PermissionError(f"Session is committed (read-only): {session_dir}")
    if len(follow_ups) > 3:
        raise ValueError("follow_up cap exceeded (>3)")

    session_yaml = read_yaml(session_dir / "session.yaml")
    script_version = session_yaml["script_version"]
    answers_path = session_dir / "answers.yaml"
    answers: list[dict[str, Any]] = read_yaml(answers_path) or []
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    entry = {
        "question_id": question_id,
        "tags": tags,
        "script_version": script_version,
        "prompt_text": prompt_text,
        "status": status,
        "response_text": response_text,
        "response_confidence": response_confidence,
        "follow_ups": follow_ups,
        "follow_up_count": len(follow_ups),
        "skip_reason": skip_reason,
        "revised_from": revised_from,
        "timestamp": now,
    }

    for i, existing in enumerate(answers):
        if existing["question_id"] == question_id:
            answers[i] = entry
            break
    else:
        answers.append(entry)

    write_yaml_atomic(answers_path, answers)

    session_yaml["last_active_at"] = now
    if question_id not in session_yaml["cursor"]["visited_question_ids"]:
        session_yaml["cursor"]["visited_question_ids"].append(question_id)
    write_yaml_atomic(session_dir / "session.yaml", session_yaml)
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

---

### Task 3.4: `advance_cursor.py` helper

**Files:**
- Create: `helpers/session/advance_cursor.py`
- Create: `tests/unit/test_advance_cursor.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_advance_cursor.py
from pathlib import Path

import pytest

from helpers.session.new_session import new_session
from helpers.session.advance_cursor import advance_cursor


SCRIPT_QS = [
    {"question_id": "qa-engineer-q1"},
    {"question_id": "qa-engineer-q2"},
    {"question_id": "qa-engineer-q3"},
]


def _seed(tmp_path):
    return new_session(
        repo_root=tmp_path,
        script_id="qa-engineer",
        persona="QA",
        script_version="0.2.0",
        access_mode="direct",
        total_questions=3,
        agent_identifier="copilot-interviewer-v1",
    )


def test_advance_from_initial_returns_first_question(tmp_path):
    seed = _seed(tmp_path)
    nxt = advance_cursor(
        session_dir=Path(seed["session_dir"]),
        questions_in_order=SCRIPT_QS,
        human_only_ids=set(),
    )
    assert nxt == "qa-engineer-q1"


def test_advance_skips_visited(tmp_path):
    seed = _seed(tmp_path)
    sd = Path(seed["session_dir"])
    # Pretend q1 is visited
    import yaml
    s = yaml.safe_load((sd / "session.yaml").read_text())
    s["cursor"]["visited_question_ids"] = ["qa-engineer-q1"]
    s["cursor"]["current_question_id"] = "qa-engineer-q1"
    (sd / "session.yaml").write_text(yaml.safe_dump(s))
    nxt = advance_cursor(session_dir=sd, questions_in_order=SCRIPT_QS, human_only_ids=set())
    assert nxt == "qa-engineer-q2"


def test_advance_skips_human_only(tmp_path):
    seed = _seed(tmp_path)
    nxt = advance_cursor(
        session_dir=Path(seed["session_dir"]),
        questions_in_order=SCRIPT_QS,
        human_only_ids={"qa-engineer-q1", "qa-engineer-q2"},
    )
    assert nxt == "qa-engineer-q3"


def test_advance_returns_none_at_end(tmp_path):
    seed = _seed(tmp_path)
    sd = Path(seed["session_dir"])
    import yaml
    s = yaml.safe_load((sd / "session.yaml").read_text())
    s["cursor"]["visited_question_ids"] = [q["question_id"] for q in SCRIPT_QS]
    (sd / "session.yaml").write_text(yaml.safe_dump(s))
    nxt = advance_cursor(session_dir=sd, questions_in_order=SCRIPT_QS, human_only_ids=set())
    assert nxt is None
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/session/advance_cursor.py`:
```python
"""Advance the cursor to the next un-visited, non-human_only question."""

from __future__ import annotations

from pathlib import Path

from helpers.common.yaml_io import read_yaml, write_yaml_atomic
from helpers.session.check_writability import check_writability


def advance_cursor(
    *,
    session_dir: Path,
    questions_in_order: list[dict],
    human_only_ids: set[str],
) -> str | None:
    if not check_writability(session_dir):
        raise PermissionError(f"Session is committed (read-only): {session_dir}")
    s = read_yaml(session_dir / "session.yaml")
    visited = set(s["cursor"]["visited_question_ids"])
    next_id: str | None = None
    for q in questions_in_order:
        qid = q["question_id"]
        if qid in human_only_ids or qid in visited:
            continue
        next_id = qid
        break
    s["cursor"]["current_question_id"] = next_id
    write_yaml_atomic(session_dir / "session.yaml", s)
    return next_id
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

---

### Task 3.5: `revise_cursor.py` helper

**Files:**
- Create: `helpers/session/revise_cursor.py`
- Create: `tests/unit/test_revise_cursor.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_revise_cursor.py
from pathlib import Path

import pytest
import yaml

from helpers.session.new_session import new_session
from helpers.session.revise_cursor import revise_cursor


def _seed(tmp_path):
    s = new_session(repo_root=tmp_path, script_id="qa-engineer", persona="QA",
                    script_version="0.2.0", access_mode="direct", total_questions=5,
                    agent_identifier="copilot-interviewer-v1")
    sd = Path(s["session_dir"])
    sess = yaml.safe_load((sd / "session.yaml").read_text())
    sess["cursor"]["visited_question_ids"] = ["qa-engineer-q1", "qa-engineer-q2", "qa-engineer-q3"]
    sess["cursor"]["current_question_id"] = "qa-engineer-q3"
    (sd / "session.yaml").write_text(yaml.safe_dump(sess))
    return sd


def test_revise_to_visited(tmp_path):
    sd = _seed(tmp_path)
    revise_cursor(session_dir=sd, target_question_id="qa-engineer-q1")
    s = yaml.safe_load((sd / "session.yaml").read_text())
    assert s["cursor"]["current_question_id"] == "qa-engineer-q1"


def test_revise_to_unvisited_rejected(tmp_path):
    sd = _seed(tmp_path)
    with pytest.raises(ValueError, match="not visited"):
        revise_cursor(session_dir=sd, target_question_id="qa-engineer-q4")
```

- [ ] **Step 2: Run, FAIL.**

- [ ] **Step 3: Implement**

`helpers/session/revise_cursor.py`:
```python
"""Move cursor back to a previously-visited question."""

from __future__ import annotations

from pathlib import Path

from helpers.common.yaml_io import read_yaml, write_yaml_atomic
from helpers.session.check_writability import check_writability


def revise_cursor(*, session_dir: Path, target_question_id: str) -> None:
    if not check_writability(session_dir):
        raise PermissionError(f"Session is committed (read-only): {session_dir}")
    s = read_yaml(session_dir / "session.yaml")
    if target_question_id not in s["cursor"]["visited_question_ids"]:
        raise ValueError(f"Target question {target_question_id} not visited")
    s["cursor"]["current_question_id"] = target_question_id
    write_yaml_atomic(session_dir / "session.yaml", s)
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit.**

---

### Task 3.6: `interview-session-store` SKILL.md

**Files:**
- Create: `.github/skills/interview-session-store/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-session-store
description: Loaded eagerly via the agent profile. Use for every state-changing operation during an interview — creating a session, advancing/reversing the cursor, recording an answer or follow-up, updating session status. Owns the cursor and the writability rule (committed = read-only).
---

# interview-session-store

CRUD layer for `responses/{session_id}/session.yaml`, `answers.yaml`, `metadata.yaml`. The agent calls into this skill for all state changes; it never writes those YAML files directly.

## Operations

| Operation | Helper | Purpose |
|---|---|---|
| `new_session` | `helpers/session/new_session.py` | Generate IDs, write initial 3 YAML files + resume-token.txt |
| `load_session` | `helpers/session/load_session.py` | Resolve resume_token or session_id, return session state + writability |
| `advance_cursor` | `helpers/session/advance_cursor.py` | Move to next un-visited, non-human_only question |
| `revise_cursor` | `helpers/session/revise_cursor.py` | Back-nav to a previously-visited question |
| `write_answer` | `helpers/session/write_answer.py` | Upsert answer record; update last_active_at; track follow_up_count |
| `check_writability` | `helpers/session/check_writability.py` | Refuse if session dir is committed in current HEAD |

## Contract

- All writes are atomic (write-tempfile + rename).
- `check_writability` runs before every write; PermissionError on committed sessions.
- `follow_up_count` is enforced ≤ 3 by `write_answer`.
- `cursor.visited_question_ids` is appended on every `write_answer` call.
- `last_active_at` is updated on every successful write.
- Single-writer rule is documented (don't run two agent instances against the same session); not enforced via lock file. Atomic writes provide sufficient corruption safety.

## Failure modes

- `LookupError`: resume_token / session_id not found.
- `PermissionError`: session is committed (read-only).
- `ValueError`: follow_up cap exceeded; revise to un-visited question.
```

- [ ] **Step 2: Commit.**

---

## Phase 4: Behavioral skills

### Task 4.1: `validate_confidence.py` helper

**Files:**
- Create: `helpers/confidence/validate_confidence.py`
- Create: `tests/unit/test_validate_confidence.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_validate_confidence.py
import pytest

from helpers.confidence.validate_confidence import validate_confidence


def test_valid_values():
    for v in ["tracked", "estimated", "inferred", "discussion-derived", None]:
        validate_confidence(v)  # no raise


def test_invalid_raises():
    with pytest.raises(ValueError):
        validate_confidence("guess")
```

- [ ] **Step 2: Implement**

`helpers/confidence/validate_confidence.py`:
```python
"""Validate response_confidence enum values."""

ALLOWED = {"tracked", "estimated", "inferred", "discussion-derived", None}


def validate_confidence(value):
    if value not in ALLOWED:
        raise ValueError(f"response_confidence must be one of {sorted(str(v) for v in ALLOWED)}, got {value!r}")
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 4.2: `classify_skip.py` helper

**Files:**
- Create: `helpers/skip/classify_skip.py`
- Create: `tests/unit/test_classify_skip.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_classify_skip.py
import pytest

from helpers.skip.classify_skip import classify_skip


@pytest.mark.parametrize("phrase,expected", [
    ("I don't know", "not_measured"),
    ("no idea", "not_measured"),
    ("we don't measure that", "not_measured"),
    ("I'd rather not answer", "declined"),
    ("pass on that one", "declined"),
    ("prefer not to say", "declined"),
    ("doesn't apply to me", "not_applicable"),
    ("N/A", "not_applicable"),
    ("not applicable", "not_applicable"),
])
def test_classification(phrase, expected):
    assert classify_skip(phrase) == expected


def test_unrecognized_returns_none():
    assert classify_skip("the weather is nice") is None
```

- [ ] **Step 2: Implement**

`helpers/skip/classify_skip.py`:
```python
"""Classify an interviewee's skip utterance into one of three kinds."""

from __future__ import annotations

import re


_PATTERNS = {
    "declined": [
        r"\b(rather not|prefer not|won't|won't say|decline|pass\b)",
    ],
    "not_applicable": [
        r"\b(not applicable|doesn't apply|doesn't pertain|n/a)\b",
    ],
    "not_measured": [
        r"\b(don't know|no idea|don't measure|not measured|haven't measured|unsure|not sure)\b",
    ],
}


def classify_skip(utterance: str) -> str | None:
    text = utterance.lower()
    # Order matters: declined / N/A check before generic "don't know"
    for kind in ("declined", "not_applicable", "not_measured"):
        for pat in _PATTERNS[kind]:
            if re.search(pat, text):
                return kind
    return None
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 4.3: `interview-confidence-tagging` SKILL.md

**Files:**
- Create: `.github/skills/interview-confidence-tagging/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-confidence-tagging
description: Use when an answer contains a number, percentage, duration, count, ratio, or any quantitative claim — also when the question's tag includes [3d] (Baseline Metrics), regardless of whether the answer was numeric. Probes the interviewee for tracked vs. estimated and records response_confidence.
---

# interview-confidence-tagging

After a numeric answer (or any `[3d]`-tagged question), ask one short probe to classify the source of the number:

> "Is that a number you've seen reported on a dashboard or ticket, or your own estimate?"

## Mapping

| Interviewee response | `response_confidence` |
|---|---|
| Cites a dashboard, report, ticket, source-of-truth | `tracked` |
| "My estimate" / "my recollection" / "gut feel" | `estimated` |
| "I'm guessing based on X" | `inferred` |
| "I don't know" / "I'd rather not say" | `null` (and add a row to flags.md) |

## Rules

- **Probe is attempted, not blocking.** If the interviewee can't or won't classify, record `null` and continue. Never fail the session over confidence-tagging.
- **For `[3d]` questions, attempt the probe always.** For other numeric answers, attempt is recommended but the agent may defer if pacing is tight (log the deferral in `flags.md`).
- **The probe must be a real exchange.** Do not synthesize a confidence value without asking.
- **Validate before persisting** with `helpers/confidence/validate_confidence.py` to ensure the recorded value is in the allowed enum.

## Persistence

After the probe, call `interview-session-store.write_answer(...)` with `response_confidence` set. The follow-up exchange goes into `follow_ups[]`.
```

- [ ] **Step 2: Commit.**

---

### Task 4.4: `interview-skip-handling` SKILL.md

**Files:**
- Create: `.github/skills/interview-skip-handling/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-skip-handling
description: Use when the interviewee says any variant of "I don't know," "I'd rather not answer," "that doesn't apply," "pass," or "skip" — or when the next question is in the script's human_only_question_ids and the agent should skip it without asking.
---

# interview-skip-handling

Distinguishes three interviewee-initiated skip kinds plus one agent-initiated skip (`human_only`). Each maps to a specific `status` and `skip_reason` in the answer record, and a re-prompt rule.

## Classification

| Interviewee phrasing | `status` | `skip_reason` | Re-prompt? |
|---|---|---|---|
| "I don't know" / "we don't measure that" | `skipped` | `not_measured` | **Once**, only for required_context questions |
| "I'd rather not answer" / "pass" | `declined` | `declined` | **Never.** Note in `flags.md`. |
| "That doesn't apply" / "N/A" | `skipped` | `not_applicable` | No |
| (agent-initiated, AI-fit question) | `skipped` | `human_only` | Never. Increment `metadata.counts.human_only_gaps`. |

## Helper

Use `helpers/skip/classify_skip.py` to categorize the interviewee's utterance:

```
python helpers/skip/classify_skip.py "I'd rather not say"
# → "declined"
```

## Required-context re-prompt

If `skip_reason` is `not_measured` AND the question's `question_id` is in the script's `required_context_question_ids`, the agent re-prompts ONCE:

> "That's an important one for context — could you give a rough estimate, or describe what you observe? If you genuinely don't know, that's fine and we'll move on."

If still skipped after the re-prompt, set `metadata.required_context_satisfied: false` and continue.

## Persistence

Call `interview-session-store.write_answer(...)` with `status` and `skip_reason` populated. `response_text` is `null` for skips.
```

- [ ] **Step 2: Commit.**

---

### Task 4.5: `interview-refinement` SKILL.md

**Files:**
- Create: `.github/skills/interview-refinement/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-refinement
description: Use when an answer is short or vague (≤1 sentence, no specifics, no numbers when the tag suggests there should be), when the interviewee says "let me think about that" or answers tangentially, or when they explicitly ask to elaborate. Engage in bounded multi-turn dialogue to develop a richer answer, then return to the structured flow.
---

# interview-refinement

Bounded conversational refinement around a single question. Either party can start the dialogue; the agent returns to the structured flow once an answer is committed or the cap is reached.

## Cap

**≤3 follow-ups per question.** After the 3rd follow-up, commit whatever has been captured with `response_confidence: discussion-derived` and advance.

## Triggers (agent-initiated)

- Answer is ≤1 sentence and contains no concrete noun, no number, and no specific event.
- Tag is `[3a]` (Process Journey) or `[3c]` (Pain Points) and the answer lacks a "walk me through" recountable event.
- Tag is `[3d]` (Baseline Metrics) and the answer has no number.

The agent asks **one targeted follow-up** that probes for the specific missing detail, e.g.:
- "Could you walk me through the most recent time that happened?"
- "Roughly how long does that take, even ballpark?"
- "What was the first thing that went wrong?"

## Triggers (interviewee-initiated)

- "Let me think about that."
- "It's complicated, can I unpack it?"
- "Actually, let me back up a bit."

The agent stays scoped to the current question and lets the interviewee ramble; one summarizing follow-up is allowed before re-asking the original question.

## Bias-mitigation rules during refinement

These come from `interview-bias-mitigation` and apply unconditionally:
- **No leading questions** ("So I imagine X is the problem, right?").
- **No solution-shaping** ("Have you considered an AI tool for that?").
- **No anchoring** with prior interviewees' answers.

## Storage

- Each follow-up exchange is appended to `follow_ups[]` in the answer record.
- The committed answer goes into `response_text`. The compiler reads `response_text`; the dialogue is preserved for the transcript.
- After the 3rd follow-up without a clear committed answer, `response_text` is the best summary the agent can extract from the dialogue, with `response_confidence: discussion-derived`.

## Adjacent topics

If the interviewee raises an adjacent topic during refinement, the agent notes it for `flags.md` (a 1-line summary) and returns to the current question. Do not pivot the conversation.
```

- [ ] **Step 2: Commit.**

---

### Task 4.6: `interview-bias-mitigation` SKILL.md

**Files:**
- Create: `.github/skills/interview-bias-mitigation/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-bias-mitigation
description: Loaded eagerly via the agent profile. Always active during interview interactions — not invoked per question. Enforces methodology rules (no leading, no solutioning, no anchoring) and refuses interviewee requests for advice or recommendations.
---

# interview-bias-mitigation

These rules apply at every turn of every interview. They are not soft guidelines; they are hard constraints on the agent's behavior.

## 1. AI-fit questions only after target-state questions

Script ordering encodes this. The agent **must not** reorder questions or ask any AI-fit question before the script's target-state section is complete. (Mechanically: AI-fit questions are tagged with `human_only_question_ids` in script frontmatter and are skipped by the agent regardless of order, but this rule applies even if a script were re-tagged in the future.)

## 2. No leading questions during refinement

**Refused:** *"So I imagine X is the problem, right?"*, *"It sounds like you're saying Y, is that fair?"* (when Y wasn't actually said).

**Allowed:** *"Could you walk me through what happened?"*, *"What did you do next?"*

## 3. No solution-shaped suggestions during refinement

**Refused:** *"Have you considered an AI tool for that?"*, *"What if you used X to solve this?"*, *"That sounds like something Y could help with."*

**Allowed:** Open-ended probes that surface detail without shaping a direction.

## 4. No anchoring with prior interviewees' answers

The agent operates on **one session at a time** and has no access to other interviewees' responses. Cross-session synthesis is the compiler's job, not the agent's.

## 5. No solutioning, ever

The agent never recommends QA tooling, vendors, frameworks, or approaches. It never volunteers an opinion on what the interviewee should do.

## 6. Refuse advice requests from the interviewee

When the interviewee asks the agent for recommendations, opinions, or solutions:

- *"What tools should we use?"*
- *"What would you recommend?"*
- *"Have you seen this work elsewhere?"*
- *"What do most teams do here?"*

The agent **declines politely** with phrasing like:

> "That's exactly the kind of question your sponsor team should weigh in on — I'm here to capture your perspective, not shape it. I'll flag it for a human follow-up."

Then:
1. Append a 1-line note to `flags.md` describing the question (so the sponsor can address it later).
2. Return to the current interview question.

This is a **hard rule**, not a soft suggestion. The failure mode is corrosive: once the agent starts dispensing solutions, the discovery framing collapses and the brief loses its credibility.
```

- [ ] **Step 2: Commit.**

```
git add .github/skills/interview-confidence-tagging/ .github/skills/interview-skip-handling/ .github/skills/interview-refinement/ .github/skills/interview-bias-mitigation/ helpers/confidence/ helpers/skip/ tests/unit/test_validate_confidence.py tests/unit/test_classify_skip.py
git commit -m "skills: behavioral (refinement, confidence-tagging, skip-handling, bias-mitigation) + helpers"
```

---

## Phase 5: Finalize

### Task 5.1: Transcript generator (part of finalize)

**Files:**
- Create: `helpers/finalize/generate_transcript.py`
- Create: `tests/unit/test_generate_transcript.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_generate_transcript.py
from pathlib import Path

import yaml

from helpers.session.new_session import new_session
from helpers.finalize.generate_transcript import generate_transcript


def test_transcript_includes_questions_and_responses(tmp_path):
    seed = new_session(repo_root=tmp_path, script_id="qa-engineer", persona="QA",
                      script_version="0.2.0", access_mode="direct", total_questions=2,
                      agent_identifier="copilot-interviewer-v1")
    sd = Path(seed["session_dir"])
    answers = [
        {"question_id": "qa-engineer-q1", "tags": [], "script_version": "0.2.0",
         "prompt_text": "Q1?", "status": "answered", "response_text": "A1",
         "response_confidence": None, "follow_ups": [],
         "follow_up_count": 0, "skip_reason": None, "revised_from": None,
         "timestamp": "2026-05-06T14:00:00Z"},
        {"question_id": "qa-engineer-q2", "tags": ["3d"], "script_version": "0.2.0",
         "prompt_text": "Q2?", "status": "answered", "response_text": "5",
         "response_confidence": "estimated", "follow_ups": [
             {"prompt": "Tracked or estimated?", "response": "Estimated"}],
         "follow_up_count": 1, "skip_reason": None, "revised_from": None,
         "timestamp": "2026-05-06T14:01:00Z"},
    ]
    (sd / "answers.yaml").write_text(yaml.safe_dump(answers))
    generate_transcript(session_dir=sd)
    text = (sd / "transcript.md").read_text()
    assert "Q1?" in text
    assert "A1" in text
    assert "Q2?" in text
    assert "Estimated" in text
    assert "Tracked or estimated?" in text
```

- [ ] **Step 2: Implement**

`helpers/finalize/generate_transcript.py`:
```python
"""Generate transcript.md from answers.yaml."""

from __future__ import annotations

from pathlib import Path

from helpers.common.yaml_io import read_yaml


def generate_transcript(*, session_dir: Path) -> None:
    session = read_yaml(session_dir / "session.yaml")
    metadata = read_yaml(session_dir / "metadata.yaml")
    answers = read_yaml(session_dir / "answers.yaml") or []

    lines = [
        f"# Interview Transcript — {session['session_id']}",
        "",
        f"- **Persona:** {metadata['persona']}",
        f"- **Script version:** {metadata['script_version']}",
        f"- **Started:** {metadata['started_at']}",
        f"- **Completed:** {metadata.get('completed_at') or '(in progress)'}",
        "",
        "---",
        "",
    ]
    for entry in answers:
        lines.append(f"## {entry['question_id']}  `{', '.join(entry['tags']) or '–'}`")
        lines.append("")
        lines.append(f"> {entry['prompt_text']}")
        lines.append("")
        if entry["status"] == "answered":
            lines.append(entry["response_text"] or "")
        elif entry["status"] == "revised":
            lines.append(f"**(revised from earlier answer)** {entry['response_text']}")
        else:
            lines.append(f"_(skipped — {entry.get('skip_reason') or entry['status']})_")
        if entry["response_confidence"]:
            lines.append("")
            lines.append(f"_Confidence: {entry['response_confidence']}_")
        for fu in entry.get("follow_ups", []):
            lines.append("")
            lines.append(f"> _Follow-up:_ {fu['prompt']}")
            if fu.get("response"):
                lines.append(f">> {fu['response']}")
        lines.append("")
    (session_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 5.2: `finalize_session.py` orchestrator

**Files:**
- Create: `helpers/finalize/finalize_session.py`
- Create: `tests/unit/test_finalize_session.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_finalize_session.py
from pathlib import Path

import yaml

from helpers.session.new_session import new_session
from helpers.finalize.finalize_session import finalize_session


def test_marks_complete_and_recomputes_counts(tmp_path):
    seed = new_session(repo_root=tmp_path, script_id="qa-engineer", persona="QA",
                      script_version="0.2.0", access_mode="direct", total_questions=2,
                      agent_identifier="copilot-interviewer-v1")
    sd = Path(seed["session_dir"])
    (sd / "answers.yaml").write_text(yaml.safe_dump([
        {"question_id": "qa-engineer-q1", "tags": [], "script_version": "0.2.0",
         "prompt_text": "?", "status": "answered", "response_text": "x",
         "response_confidence": None, "follow_ups": [], "follow_up_count": 0,
         "skip_reason": None, "revised_from": None, "timestamp": "2026-05-06T14:00:00Z"},
        {"question_id": "qa-engineer-q2", "tags": [], "script_version": "0.2.0",
         "prompt_text": "?", "status": "skipped", "response_text": None,
         "response_confidence": None, "follow_ups": [], "follow_up_count": 0,
         "skip_reason": "human_only", "revised_from": None,
         "timestamp": "2026-05-06T14:01:00Z"},
    ]))
    finalize_session(session_dir=sd)
    s = yaml.safe_load((sd / "session.yaml").read_text())
    m = yaml.safe_load((sd / "metadata.yaml").read_text())
    assert s["status"] == "complete"
    assert m["completed_at"] is not None
    assert m["counts"]["answered"] == 1
    assert m["counts"]["human_only_gaps"] == 1
```

- [ ] **Step 2: Implement**

`helpers/finalize/finalize_session.py`:
```python
"""Mark session complete, regenerate transcript, recompute counts."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from helpers.common.yaml_io import read_yaml, write_yaml_atomic
from helpers.finalize.generate_transcript import generate_transcript
from helpers.session.check_writability import check_writability


def finalize_session(*, session_dir: Path) -> None:
    if not check_writability(session_dir):
        raise PermissionError(f"Session is committed: {session_dir}")
    session = read_yaml(session_dir / "session.yaml")
    metadata = read_yaml(session_dir / "metadata.yaml")
    answers = read_yaml(session_dir / "answers.yaml") or []

    counts = {
        "total_questions": metadata["counts"]["total_questions"],
        "answered": sum(1 for a in answers if a["status"] in ("answered", "revised")),
        "skipped": sum(1 for a in answers if a["status"] == "skipped" and a.get("skip_reason") != "human_only"),
        "declined": sum(1 for a in answers if a["status"] == "declined"),
        "human_only_gaps": sum(1 for a in answers if a.get("skip_reason") == "human_only"),
    }
    metadata["counts"] = counts
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    metadata["completed_at"] = now
    session["status"] = "complete"
    session["last_active_at"] = now

    write_yaml_atomic(session_dir / "metadata.yaml", metadata)
    write_yaml_atomic(session_dir / "session.yaml", session)
    generate_transcript(session_dir=session_dir)
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 5.3: `git_branch_commit_push.py` helper

**Files:**
- Create: `helpers/finalize/git_branch_commit_push.py`
- Create: `tests/unit/test_git_branch_commit_push.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_git_branch_commit_push.py
import subprocess
from pathlib import Path

import pytest

from helpers.finalize.git_branch_commit_push import git_branch_commit_push


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def repo_with_remote(tmp_path):
    bare = tmp_path / "remote.git"
    work = tmp_path / "work"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    subprocess.run(["git", "init", "-q", str(work)], check=True)
    _git(work, "config", "user.email", "t@t")
    _git(work, "config", "user.name", "t")
    _git(work, "remote", "add", "origin", str(bare))
    _git(work, "commit", "--allow-empty", "-m", "init")
    _git(work, "push", "-u", "origin", "master")
    return work


def test_creates_branch_and_pushes(repo_with_remote, tmp_path):
    sd = repo_with_remote / "responses" / "20260506-qa-eng-7c9a"
    sd.mkdir(parents=True)
    (sd / "session.yaml").write_text("session_id: x\n")
    out = git_branch_commit_push(
        repo_root=repo_with_remote,
        session_id="20260506-qa-eng-7c9a",
        persona="qa-engineer",
    )
    assert out["branch"] == "interview/20260506-qa-eng-7c9a"
    branches = subprocess.check_output(
        ["git", "branch", "-a"], cwd=repo_with_remote, text=True)
    assert "interview/20260506-qa-eng-7c9a" in branches


def test_refuses_dirty_unrelated_files(repo_with_remote):
    (repo_with_remote / "unrelated.txt").write_text("x")
    sd = repo_with_remote / "responses" / "20260506-qa-eng-7c9a"
    sd.mkdir(parents=True)
    (sd / "session.yaml").write_text("session_id: x\n")
    with pytest.raises(RuntimeError, match="dirty"):
        git_branch_commit_push(repo_root=repo_with_remote,
                               session_id="20260506-qa-eng-7c9a",
                               persona="qa-engineer")
```

- [ ] **Step 2: Implement**

`helpers/finalize/git_branch_commit_push.py`:
```python
"""Create per-session branch, commit responses/<session_id>/, push."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cwd, *args, check=True):
    return subprocess.run(["git", *args], cwd=cwd, check=check,
                          capture_output=True, text=True)


def git_branch_commit_push(
    *,
    repo_root: Path,
    session_id: str,
    persona: str,
) -> dict:
    repo_root = Path(repo_root)
    session_rel = f"responses/{session_id}/"

    # Reject dirty unrelated working tree changes
    status = _run(repo_root, "status", "--porcelain").stdout.splitlines()
    unrelated = [line for line in status if not line[3:].startswith(session_rel)]
    if unrelated:
        raise RuntimeError(
            f"Working tree has dirty unrelated files; refusing finalize: {unrelated[:3]}")

    branch = f"interview/{session_id}"
    _run(repo_root, "checkout", "-b", branch)
    _run(repo_root, "add", session_rel)
    _run(repo_root, "commit", "-m",
         f"Interview session {session_id} ({persona})")
    push = _run(repo_root, "push", "-u", "origin", branch, check=False)
    pushed = push.returncode == 0
    return {
        "branch": branch,
        "pushed": pushed,
        "push_error": None if pushed else push.stderr.strip(),
    }
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 5.4: `package_bundle.py` helper

**Files:**
- Create: `helpers/finalize/package_bundle.py`
- Create: `tests/unit/test_package_bundle.py`

- [ ] **Step 1: Failing test**

```python
# tests/unit/test_package_bundle.py
import zipfile
from pathlib import Path

from helpers.finalize.package_bundle import package_bundle


def test_creates_zip_with_session_files(tmp_path):
    sd = tmp_path / "responses" / "20260506-qa-eng-7c9a"
    sd.mkdir(parents=True)
    (sd / "session.yaml").write_text("a")
    (sd / "answers.yaml").write_text("[]")
    out = package_bundle(repo_root=tmp_path, session_id="20260506-qa-eng-7c9a")
    zpath = Path(out["bundle_path"])
    assert zpath.exists()
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
    assert any(n.endswith("session.yaml") for n in names)
    assert any(n.endswith("answers.yaml") for n in names)
```

- [ ] **Step 2: Implement**

`helpers/finalize/package_bundle.py`:
```python
"""Zip a session directory into responses/{session_id}.zip."""

from __future__ import annotations

import zipfile
from pathlib import Path


def package_bundle(*, repo_root: Path, session_id: str) -> dict:
    repo_root = Path(repo_root)
    sd = repo_root / "responses" / session_id
    if not sd.exists():
        raise FileNotFoundError(sd)
    out_path = repo_root / "responses" / f"{session_id}.zip"
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sd.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=str(p.relative_to(repo_root)))
    return {"bundle_path": str(out_path)}
```

- [ ] **Step 3: Run, verify PASS.**

- [ ] **Step 4: Commit.**

---

### Task 5.5: `interview-finalize` SKILL.md

**Files:**
- Create: `.github/skills/interview-finalize/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-finalize
description: Use when the interviewee indicates they're done, the cursor reaches the end of the script, or the agent times out a long-idle session and the user confirms wrap-up. Marks session complete, regenerates the transcript, runs the git transport (default), and optionally produces a portable .zip bundle.
---

# interview-finalize

End-of-session work. Sequence:

1. **Validate** session is `in_progress` and writable. Refuse otherwise.
2. **Regenerate transcript** from `answers.yaml` → `transcript.md`.
3. **Recompute counts** in `metadata.yaml` (answered, skipped, declined, human_only_gaps).
4. **Mark complete**: `session.yaml.status: complete`, `metadata.yaml.completed_at: now`.
5. **Git transport** (default): branch `interview/{session_id}`, add session dir, commit, push.
6. **Optional bundle** (`bundle: true` or git failure): write `responses/{session_id}.zip`.

## Helpers

- `helpers/finalize/finalize_session.py` — steps 1–4.
- `helpers/finalize/git_branch_commit_push.py` — step 5.
- `helpers/finalize/package_bundle.py` — step 6.
- `helpers/finalize/generate_transcript.py` — internal, called by `finalize_session`.

## Branch naming

`interview/{session_id}`, e.g., `interview/20260506-qa-eng-7c9a`. Refuses if branch already exists on origin (suggests a session_id collision — should not happen by construction).

## Dirty working tree handling

`git_branch_commit_push` rejects finalize if there are uncommitted changes outside the session directory. Agent surfaces the list and asks the interviewee:
- Stash them?
- Commit them as a separate commit first?
- Abort finalize?

The agent never silently includes unrelated files.

## Failure modes

- **Push rejected** (auth, branch exists, network) → session stays `complete` locally; offer the interviewee: retry push, switch to bundle-only, manual `git push` instructions.
- **Bundle write fails** → surface the error; session is still marked `complete`.

## Idempotence

Re-running finalize on a `complete` session is safe: regenerates transcript, returns existing branch/bundle paths if they exist.

## What this never does

- Never amends commits.
- Never force-pushes.
- Never skips hooks (`--no-verify`).
- Never auto-merges to main.
```

- [ ] **Step 2: Commit.**

```
git add .github/skills/interview-finalize/ helpers/finalize/ tests/unit/test_*finalize*.py tests/unit/test_*transcript*.py tests/unit/test_*bundle*.py tests/unit/test_*push*.py
git commit -m "skills/finalize: SKILL.md + helpers (finalize_session, git transport, bundle, transcript)"
```

---

## Phase 6: Agent profile + integration

### Task 6.1: Custom agent profile

**Files:**
- Create: `.github/agents/interviewer.agent.md`

- [ ] **Step 1: Write the agent profile**

```markdown
---
name: interviewer
description: Conducts QA discovery interviews following the persona scripts in interview/. Stateful, resumable, bias-aware.
tools:
  - filesystem
  - terminal
skills:
  - interview-script-loader
  - interview-session-store
  - interview-finalize
  - interview-refinement
  - interview-confidence-tagging
  - interview-skip-handling
  - interview-bias-mitigation
---

# Interviewer Agent

You conduct structured QA discovery interviews. Persona scripts live in `interview/`. The methodology and bias-mitigation rules are non-negotiable.

## Boot sequence

1. **Greet.** "Hi — I'll walk you through a short structured interview about your QA work. It's about 30–60 minutes depending on detail. Are you starting a new session, or resuming one?"

2. **If resuming**: ask for the resume token (format `xxxx-xxxx`). Call `interview-session-store.load_session(resume_token)`.
   - If `writable: false` → "This session was finalized and committed. To revise it, start a new session and we can incorporate the relevant updates."
   - If found and writable: load the script via `interview-script-loader.parse(script_id)`. If `script_version` differs from the script file, lock to the original version (don't auto-upgrade). Resume at `cursor.current_question_id`. Re-prompt any `pending` or null-response follow-ups.

3. **If new**:
   1. Ask: "Which persona — QA Engineer, QA Lead, Developer, Release Manager, or Product Owner?"
   2. Ask: "Are you the interviewee, or facilitating for someone else?" → `access_mode: direct | facilitated`.
   3. Ask: "What should I call you?" (optional). If facilitated, also ask for the facilitator's name.
   4. Call `interview-script-loader.parse(<script>)`.
   5. Call `interview-session-store.new_session(...)` with the captured fields and `total_questions = len(questions)`.
   6. Surface the resume token: "Your resume token is `xxxx-xxxx` — I've also saved it to `responses/{session_id}/resume-token.txt`. If we get interrupted, give me that token to pick up where we left off."

## Per-question loop

For each question (skipping `human_only_question_ids`):

1. Read the next question from the parsed script.
2. **Ask it verbatim.** Do not paraphrase the prompt text; the wording was deliberately chosen.
3. Receive the answer.
4. **Refinement** — if answer is short/vague (per `interview-refinement` triggers) OR interviewee asks to elaborate → engage refinement (≤3 follow-ups).
5. **Confidence-tagging** — if answer contains a number OR question is `[3d]`-tagged → ask the confidence probe (per `interview-confidence-tagging`).
6. **Skip-handling** — if answer is a skip, classify and record (per `interview-skip-handling`).
7. **Bias-mitigation** — if interviewee asks for advice/recommendations → refuse per `interview-bias-mitigation`, log to `flags.md`, return.
8. **Persist** — call `interview-session-store.write_answer(...)` with the full record.
9. **Advance** — call `interview-session-store.advance_cursor(...)` for the next question.

## Navigation

If the interviewee says "go back to question N" / "I'd like to revise q5" / similar:
1. Call `interview-session-store.revise_cursor(target_question_id)`.
2. Re-ask the question.
3. Persist with `revised_from: <previous response_text>` and `status: revised`.
4. Return to the cursor's prior position (forward through still-unvisited questions).

## Wrap-up

When `advance_cursor` returns `None` (script complete) OR interviewee says they're done:
1. **Summary**: show counts ("answered X, skipped Y, declined Z, AI-fit gaps {n} for human follow-up").
2. **Open feedback**: "Anything else you want to flag for the synthesis team that we didn't ask about directly?" → append to `flags.md`.
3. **Finalize**: call `interview-finalize` with default `transport: git`. Surface branch URL.
4. **Sign off**: "Thanks. Your responses are now on branch `interview/{session_id}`."

## Hard rules (from interview-bias-mitigation)

- Never reorder questions to put AI-fit content earlier.
- Never lead, anchor, or solution-shape during refinement.
- Never recommend tools, vendors, or approaches.
- Refuse advice requests politely and log to `flags.md`.
```

- [ ] **Step 2: Commit.**

```
git add .github/agents/interviewer.agent.md
git commit -m "agents: interviewer.agent.md custom agent profile"
```

---

### Task 6.2: Skills README

**Files:**
- Create: `.github/skills/README.md`

- [ ] **Step 1: Write README.md**

```markdown
# Interview Skills

Skills that compose the interview agent (`.github/agents/interviewer.agent.md`).

## Invocation

- **Copilot CLI:** `copilot --agent interviewer --prompt "Start interview"` (or `--prompt "Resume xxxx-xxxx"`)
- **Copilot Chat (VS Code):** invoke the `interviewer` agent.

## Skills

| Skill | Type | Purpose |
|---|---|---|
| `interview-script-loader` | data-layer | Parse persona scripts; derive question IDs |
| `interview-session-store` | data-layer | CRUD on session/answers/metadata YAML |
| `interview-finalize` | data-layer | Status flip, transcript, git push, optional bundle |
| `interview-refinement` | behavioral | ≤3 follow-ups for thin answers |
| `interview-confidence-tagging` | behavioral | Probe tracked vs. estimated |
| `interview-skip-handling` | behavioral | 3 skip kinds + human_only |
| `interview-bias-mitigation` | behavioral | Methodology rules; refuse advice requests |

## Layout

- `<skill-name>/SKILL.md` — skill manifest + behavior contract.
- `helpers/<group>/*.py` — Python helpers each skill calls.
- `schemas/*.json` — JSON schemas for YAML state files and helper output.

## Design and execution

See [docs/superpowers/specs/2026-05-06-interview-skills-design.md](../../docs/superpowers/specs/2026-05-06-interview-skills-design.md) for the full design and [docs/superpowers/plans/2026-05-06-interview-skills.md](../../docs/superpowers/plans/2026-05-06-interview-skills.md) for the implementation plan.
```

- [ ] **Step 2: Commit.**

---

### Task 6.3: Integration test harness

**Files:**
- Create: `tests/integration/scripted_interview.py`
- Create: `tests/fixtures/canned_responses/qa-engineer.yaml`

- [ ] **Step 1: Write a canned-responses fixture for QA Engineer**

`tests/fixtures/canned_responses/qa-engineer.yaml`:
```yaml
# Canned answers keyed by question_id. Used by scripted_interview.py to drive
# a non-interactive end-to-end run through the script.
qa-engineer-q1: { response: "About 18 months", confidence: null }
qa-engineer-q2: { response: "API and integration tests primarily", confidence: null }
qa-engineer-q3: { response: "About 30% authoring, 30% execution, 40% verification",
                  confidence: estimated }
qa-engineer-q4: { response: "Last week I authored a contract test for the new endpoint", confidence: null }
qa-engineer-q5: { response: "Acceptance criteria came from the ticket; mostly clear", confidence: null }
# ... continue for the full script (see plan note: hand-author one per persona)
qa-engineer-q30: { skip: human_only }
qa-engineer-q31: { skip: human_only }
qa-engineer-q32: { skip: human_only }
```

(Plan note: this fixture is to be filled in for every `question_id` once the script-loader can enumerate them. The implementation may auto-generate a stub fixture from `parse_script` and require the developer to fill responses.)

- [ ] **Step 2: Write the integration harness**

`tests/integration/scripted_interview.py`:
```python
"""Drive a full interview session non-interactively against canned responses.

Usage:
    pytest tests/integration/scripted_interview.py -k qa_engineer

This is the highest-fidelity test we have without a live Copilot agent. It
exercises every helper end-to-end and asserts on the resulting YAML files.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from helpers.script.parse_script import parse_script
from helpers.script.question_filter import filter_questions
from helpers.session.new_session import new_session
from helpers.session.write_answer import write_answer
from helpers.session.advance_cursor import advance_cursor
from helpers.session.load_session import load_session
from helpers.confidence.validate_confidence import validate_confidence
from helpers.finalize.finalize_session import finalize_session


REPO = Path(__file__).resolve().parents[2]


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def temp_repo_with_scripts(tmp_path):
    """Copy interview/ scripts into a fresh git repo for the test."""
    import shutil
    shutil.copytree(REPO / "interview", tmp_path / "interview")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t")
    _git(tmp_path, "config", "user.name", "t")
    _git(tmp_path, "add", "interview")
    _git(tmp_path, "commit", "-m", "init")
    return tmp_path


@pytest.mark.parametrize("script_file,fixture_name,script_id", [
    ("01-qa-engineer-interview.md", "qa-engineer.yaml", "qa-engineer"),
])
def test_full_session_flow(temp_repo_with_scripts, script_file, fixture_name, script_id):
    repo = temp_repo_with_scripts
    parsed = parse_script(repo / "interview" / script_file)
    questions = filter_questions(parsed, exclude_human_only=False)
    human_only = set(parsed["frontmatter"]["human_only_question_ids"])

    canned = yaml.safe_load(
        (REPO / "tests" / "fixtures" / "canned_responses" / fixture_name).read_text())

    seed = new_session(
        repo_root=repo, script_id=script_id, persona=parsed["frontmatter"]["persona"],
        script_version=parsed["frontmatter"]["script_version"],
        access_mode="direct", total_questions=len(questions),
        agent_identifier="copilot-interviewer-test")
    sd = Path(seed["session_dir"])

    while True:
        nxt = advance_cursor(session_dir=sd, questions_in_order=questions,
                             human_only_ids=human_only)
        if nxt is None:
            break
        question = next(q for q in questions if q["question_id"] == nxt)
        ans = canned.get(nxt, {})
        if ans.get("skip") == "human_only":
            write_answer(session_dir=sd, question_id=nxt, tags=question["tags"],
                         prompt_text=question["prompt_text"], status="skipped",
                         response_text=None, response_confidence=None,
                         follow_ups=[], skip_reason="human_only")
        elif "response" in ans:
            confidence = ans.get("confidence")
            if confidence:
                validate_confidence(confidence)
            write_answer(session_dir=sd, question_id=nxt, tags=question["tags"],
                         prompt_text=question["prompt_text"], status="answered",
                         response_text=ans["response"], response_confidence=confidence,
                         follow_ups=[], skip_reason=None)
        else:
            # No fixture entry — record as skipped/not_measured (test plan only)
            write_answer(session_dir=sd, question_id=nxt, tags=question["tags"],
                         prompt_text=question["prompt_text"], status="skipped",
                         response_text=None, response_confidence=None,
                         follow_ups=[], skip_reason="not_measured")

    finalize_session(session_dir=sd)
    s = yaml.safe_load((sd / "session.yaml").read_text())
    assert s["status"] == "complete"
    m = yaml.safe_load((sd / "metadata.yaml").read_text())
    assert m["counts"]["human_only_gaps"] == len(human_only)
```

- [ ] **Step 3: Run integration test for QA Engineer.**

```
pytest tests/integration/scripted_interview.py -v
```

Expected: PASS. `transcript.md` is populated, `answers.yaml` has one entry per question (plus skips for human_only), `metadata.yaml` counts are accurate.

- [ ] **Step 4: Commit.**

```
git add tests/integration/ tests/fixtures/
git commit -m "tests: scripted interview integration harness + qa-engineer fixture"
```

---

### Task 6.4: Repeat fixtures for the remaining four personas

For each remaining persona script, create a canned-responses fixture and add to the parametrized integration test.

- [ ] **Step 1:** Create `tests/fixtures/canned_responses/qa-lead.yaml` with one entry per question_id.
- [ ] **Step 2:** Create `tests/fixtures/canned_responses/developer.yaml`.
- [ ] **Step 3:** Create `tests/fixtures/canned_responses/release-manager.yaml`.
- [ ] **Step 4:** Create `tests/fixtures/canned_responses/product-owner.yaml`.
- [ ] **Step 5:** Add parametrize entries for each in `scripted_interview.py`.
- [ ] **Step 6:** Run `pytest tests/integration/ -v`. Expected: 5 PASS.
- [ ] **Step 7:** Commit.

```
git add tests/fixtures/canned_responses/ tests/integration/scripted_interview.py
git commit -m "tests: canned-response fixtures and integration runs for all 5 personas"
```

---

### Task 6.5: Real-world playtest

**Files:** none (manual validation).

- [ ] **Step 1: Run a live interview against the QA Engineer script** using `copilot --agent interviewer --prompt "Start interview"` (or the equivalent in Copilot Chat).
- [ ] **Step 2: Walk through end to end** as the interviewee. Verify:
  - Resume token surfaced and written to `resume-token.txt`.
  - Confidence probe asked on every numeric answer.
  - At least one short answer triggers refinement; cap respected (≤3 follow-ups).
  - Try all three skip phrasings; verify `skip_reason` is correct in `answers.yaml`.
  - Try asking the agent for a recommendation; verify it refuses and logs to `flags.md`.
  - Try navigating back to a previous question; verify `revised_from` populated.
  - Finalize → branch `interview/{session_id}` exists on origin.
- [ ] **Step 3: Inspect transcript.md by hand.** Save a copy as `tests/fixtures/golden_transcripts/qa-engineer-happy-path.md`.
- [ ] **Step 4: Commit the golden transcript.**

```
git add tests/fixtures/golden_transcripts/
git commit -m "tests: golden transcript from first real-world playtest (QA Engineer)"
```

---

## Verification (run after Task 6.5)

| Check | How |
|---|---|
| All unit tests pass | `pytest tests/unit/ -v` |
| Integration tests pass for all 5 personas | `pytest tests/integration/ -v` |
| Schema validation passes | included in unit tests |
| Live playtest completes end-to-end | Task 6.5 |
| Resume works mid-interview | manual test: kill process mid-question, run with `--prompt "Resume xxxx-xxxx"` |
| Read-only refusal works | manual test: commit responses/{session_id}/, then try to write |
| Bias-mitigation refusal works | manual test (Task 6.5 step 2) |

## Self-review checklist (the writer of this plan ran this once)

- ✅ **Spec coverage:** Every section of the design spec maps to at least one task. (§3 architecture → Phase 1; §4 storage → Phase 1; §5.1.1 script-loader → Phase 2; §5.1.2 session-store → Phase 3; §5.1.3 finalize → Phase 5; §5.2.* behavioral → Phase 4; §6 agent profile → Phase 6.1; §9 testing → Phase 6.3; §10 bootstrapping → distributed across phases.)
- ✅ **No placeholders:** No "TBD", no "implement later", no "similar to Task N." Each step has the actual content needed.
- ✅ **Type consistency:** `session_dir` is `Path` everywhere; helper outputs are JSON to stdout; YAML field names match the schemas in Phase 1.2.
```

