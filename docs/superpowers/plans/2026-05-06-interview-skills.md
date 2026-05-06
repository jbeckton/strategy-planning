# Interview Skills Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the seven Copilot Agent Skills, custom agent profile, helpers, schemas, and tests defined in [the design spec](../specs/2026-05-06-interview-skills-design.md), end-to-end. **Zero npm dependencies — runtime or dev.**

**Architecture:** Skills authored as `SKILL.md` files in `.github/skills/<name>/`, with deterministic logic factored into Node helpers under `helpers/` as plain JavaScript ESM (`.mjs`). Three data-layer skills (script-loader, session-store, finalize) wrap the helpers; four behavioral skills (refinement, confidence-tagging, skip-handling, bias-mitigation) are mostly markdown rules that delegate persistence to `interview-session-store`. One custom agent profile (`.github/agents/interviewer.agent.md`) bundles them as the entry point for `copilot --agent interviewer`.

**Tech Stack:** Node ≥ 18 (built-in `node:test`, `node:fs`, `node:crypto`, `node:child_process`, `node:path`); plain JavaScript ESM; JSON storage; `git` CLI for finalize transport. **No `npm install` is required at any point — runtime, dev, or CI — because the helpers and tests use only Node built-ins.**

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
│   ├── ids.mjs            # session_id, pseudonym, resume_token
│   ├── json_io.mjs        # atomic JSON read/write
│   └── frontmatter.mjs    # tiny flat-YAML parser (zero deps)
├── session/
│   ├── new_session.mjs
│   ├── load_session.mjs
│   ├── advance_cursor.mjs
│   ├── revise_cursor.mjs
│   ├── write_answer.mjs
│   └── check_writability.mjs
├── script/
│   ├── parse_script.mjs
│   └── question_filter.mjs
├── confidence/
│   └── validate_confidence.mjs
├── skip/
│   └── classify_skip.mjs
└── finalize/
    ├── generate_transcript.mjs
    ├── finalize_session.mjs
    ├── git_branch_commit_push.mjs
    └── package_bundle.mjs

schemas/
├── session.schema.json
├── answers.schema.json
├── metadata.schema.json
└── helpers/
    ├── new_session.output.schema.json
    ├── load_session.output.schema.json
    └── parse_script.output.schema.json

tests/
├── unit/                  # one <name>.test.mjs per helper
├── integration/scripted_interview.test.mjs
└── fixtures/
    ├── canned_responses/
    │   ├── qa-engineer.json
    │   ├── qa-lead.json
    │   ├── developer.json
    │   ├── release-manager.json
    │   └── product-owner.json
    └── golden_transcripts/
        └── qa-engineer-happy-path.md

interview/                 # existing — frontmatter added per Task 2.1
responses/.gitkeep         # output dir (otherwise empty until first session)
package.json               # type: module, no dependencies
```

**Type / name conventions (locked across tasks):**

- **Helpers export named functions** (camelCase, e.g., `newSession`, `writeAnswer`) and ALSO run as CLI when invoked directly: `if (import.meta.url === \`file://${process.argv[1]}\`) { ... }` block parses a JSON-encoded `process.argv[2]` and `process.stdout.write(JSON.stringify(result))`.
- **Stored field names stay snake_case** (`session_id`, `script_version`, `response_confidence`) per the design spec.
- **Helper outputs to stdout** are JSON; **errors to stderr** as `{"error": "<short_code>", "message": "<...>", "details": {...}}` with `process.exit(1)`.
- **All file writes are atomic** (write to `<path>.tmp`, then `fs.renameSync` to `<path>`).
- **All paths are absolute** within helpers; the agent passes `repoRoot` and `sessionDir` explicitly.
- **Tests use `node:test`** (built-in since 18) and `node:assert/strict`. Test files live at `tests/unit/<helper-name>.test.mjs`.
- **Run tests:** `node --test tests/unit/` for unit, `node --test tests/integration/` for integration, `node --test tests/` for everything.

---

## Phase 1: Foundation (package, schemas, common helpers)

### Task 1.1: Repo bootstrap

**Files:**
- Create: `package.json`
- Create: `responses/.gitkeep`

- [ ] **Step 1: Verify Node ≥ 18**

```
node --version
```

Expected: v18.x or higher. (`node:test` is built-in starting at 18.)

- [ ] **Step 2: Create `package.json`**

```json
{
  "name": "alight-qa-interview-skills",
  "version": "0.1.0",
  "description": "Copilot Agent Skills for conducting QA discovery interviews",
  "type": "module",
  "private": true,
  "scripts": {
    "test": "node --test tests/",
    "test:unit": "node --test tests/unit/",
    "test:integration": "node --test tests/integration/"
  }
}
```

`"type": "module"` makes `.mjs` and `.js` both ESM; we use `.mjs` to be explicit.

- [ ] **Step 3: Create empty `responses/.gitkeep`**

Empty file at `responses/.gitkeep` so the directory is tracked.

- [ ] **Step 4: Verify `node --test` discovers nothing yet (no error)**

```
node --test tests/
```

Expected: `# tests 0` (or similar). Empty test run, exit 0. The `tests/` directory doesn't exist yet, so this may also print a directory-not-found warning depending on Node version — that's fine; subsequent tasks create it.

- [ ] **Step 5: Commit**

```
git add package.json responses/.gitkeep
git commit -m "$(cat <<'EOF'
bootstrap: package.json (ESM, zero deps) and responses/ placeholder

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

### Task 1.2: JSON schemas for the three state files

**Files:**
- Create: `schemas/session.schema.json`
- Create: `schemas/answers.schema.json`
- Create: `schemas/metadata.schema.json`
- Create: `tests/_helpers/validate.mjs` (small stdlib-only validator; covers `type`, `required`, `enum`, `pattern`)
- Create: `tests/unit/schemas.test.mjs`

- [ ] **Step 1: Write the stdlib-only validator**

`tests/_helpers/validate.mjs`:
```javascript
// Tiny JSON Schema validator: covers required, type, enum, pattern, minimum.
// Stdlib-only. NOT a complete implementation — handles only what our schemas use.

export function validate(data, schema, path = "") {
  const errors = [];
  _check(data, schema, path, errors);
  if (errors.length) {
    const err = new Error(`Schema validation failed:\n  ${errors.join("\n  ")}`);
    err.errors = errors;
    throw err;
  }
}

function _check(data, schema, path, errors) {
  const at = (k) => (path ? `${path}.${k}` : k);

  if (schema.type === "object") {
    if (data === null || typeof data !== "object" || Array.isArray(data)) {
      errors.push(`${path || "(root)"}: expected object, got ${typeof data}`);
      return;
    }
    for (const req of schema.required ?? []) {
      if (!(req in data)) errors.push(`${at(req)}: required`);
    }
    for (const [k, sub] of Object.entries(schema.properties ?? {})) {
      if (k in data) _check(data[k], sub, at(k), errors);
    }
  } else if (schema.type === "array") {
    if (!Array.isArray(data)) {
      errors.push(`${path}: expected array`);
      return;
    }
    if (schema.items) data.forEach((d, i) => _check(d, schema.items, `${path}[${i}]`, errors));
  } else if (schema.enum) {
    if (!schema.enum.includes(data)) {
      errors.push(`${path}: ${JSON.stringify(data)} not in enum ${JSON.stringify(schema.enum)}`);
    }
  } else if (Array.isArray(schema.type)) {
    if (!schema.type.some((t) => _typeMatches(data, t))) {
      errors.push(`${path}: expected one of ${schema.type.join("|")}`);
    }
  } else if (schema.type) {
    if (!_typeMatches(data, schema.type)) {
      errors.push(`${path}: expected ${schema.type}, got ${data === null ? "null" : typeof data}`);
      return;
    }
    if (schema.type === "string" && schema.pattern) {
      if (!new RegExp(schema.pattern).test(data)) {
        errors.push(`${path}: ${JSON.stringify(data)} does not match /${schema.pattern}/`);
      }
    }
    if (schema.type === "integer" && typeof schema.minimum === "number" && data < schema.minimum) {
      errors.push(`${path}: ${data} < minimum ${schema.minimum}`);
    }
  }
}

function _typeMatches(data, t) {
  if (t === "null") return data === null;
  if (t === "string") return typeof data === "string";
  if (t === "integer") return Number.isInteger(data);
  if (t === "number") return typeof data === "number";
  if (t === "boolean") return typeof data === "boolean";
  if (t === "object") return data !== null && typeof data === "object" && !Array.isArray(data);
  if (t === "array") return Array.isArray(data);
  return false;
}
```

- [ ] **Step 2: Write the failing test**

`tests/unit/schemas.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { validate } from "../_helpers/validate.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const loadSchema = (name) =>
  JSON.parse(readFileSync(resolve(REPO, "schemas", `${name}.schema.json`), "utf-8"));

const VALID_SESSION = {
  session_id: "20260506-qa-eng-7c9a",
  pseudonym: "participant-7c9a",
  resume_token: "xkj4-9q2m",
  script_id: "qa-engineer",
  script_version: "0.2.0",
  agent_identifier: "copilot-interviewer-v1",
  started_at: "2026-05-06T14:00:00Z",
  last_active_at: "2026-05-06T14:32:00Z",
  status: "in_progress",
  cursor: { current_question_id: "qa-eng-q1", visited_question_ids: [] },
  required_context_satisfied: true,
  notes: null,
};

const VALID_ANSWER = {
  question_id: "qa-eng-q7",
  tags: ["3d"],
  script_version: "0.2.0",
  prompt_text: "How long...",
  status: "answered",
  response_text: "About 2 days",
  response_confidence: "estimated",
  follow_ups: [],
  follow_up_count: 0,
  skip_reason: null,
  revised_from: null,
  timestamp: "2026-05-06T14:32:00Z",
};

const VALID_METADATA = {
  session_id: "20260506-qa-eng-7c9a",
  pseudonym: "participant-7c9a",
  interviewee_name: null,
  persona: "qa-engineer",
  script_id: "qa-engineer",
  script_version: "0.2.0",
  agent_identifier: "copilot-interviewer-v1",
  access_mode: "direct",
  facilitator_pseudonym: null,
  facilitator_name: null,
  started_at: "2026-05-06T14:00:00Z",
  completed_at: null,
  counts: { total_questions: 32, answered: 0, skipped: 0, declined: 0, human_only_gaps: 0 },
};

test("session schema accepts valid", () => validate(VALID_SESSION, loadSchema("session")));
test("session schema rejects unknown status", () => {
  assert.throws(() => validate({ ...VALID_SESSION, status: "weird" }, loadSchema("session")));
});
test("answers schema accepts list of valid", () => validate([VALID_ANSWER], loadSchema("answers")));
test("answers schema rejects unknown status", () => {
  assert.throws(() => validate([{ ...VALID_ANSWER, status: "weird" }], loadSchema("answers")));
});
test("metadata schema accepts valid", () => validate(VALID_METADATA, loadSchema("metadata")));
```

- [ ] **Step 3: Run, verify FAIL** (`schemas/` doesn't exist yet).

```
node --test tests/unit/schemas.test.mjs
```

- [ ] **Step 4: Write `schemas/session.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "session.json",
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
    "started_at": {"type": "string"},
    "last_active_at": {"type": "string"},
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

- [ ] **Step 5: Write `schemas/answers.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "answers.json",
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
      "follow_up_count": {"type": "integer", "minimum": 0},
      "skip_reason": {"enum": [null, "not_measured", "declined", "not_applicable", "human_only"]},
      "revised_from": {"type": ["string", "null"]},
      "timestamp": {"type": "string"}
    }
  }
}
```

- [ ] **Step 6: Write `schemas/metadata.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "metadata.json",
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
    "started_at": {"type": "string"},
    "completed_at": {"type": ["string", "null"]},
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

- [ ] **Step 7: Run, verify PASS** (5 tests).

- [ ] **Step 8: Commit**

```
git add schemas/ tests/_helpers/validate.mjs tests/unit/schemas.test.mjs
git commit -m "schemas: session, answers, metadata JSON shapes + stdlib validator + tests"
```

---

### Task 1.3: ID and token generation helper

**Files:**
- Create: `helpers/common/ids.mjs`
- Create: `tests/unit/ids.test.mjs`

- [ ] **Step 1: Write the failing test**

`tests/unit/ids.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { newSessionId, newPseudonym, newResumeToken } from "../../helpers/common/ids.mjs";

test("session_id matches YYYYMMDD-{slug}-{4-hex}", () => {
  const sid = newSessionId("qa-engineer", { date: "20260506" });
  assert.match(sid, /^20260506-qa-engineer-[0-9a-f]{4}$/);
});

test("pseudonym matches participant-{4-hex}", () => {
  assert.match(newPseudonym(), /^participant-[0-9a-f]{4}$/);
});

test("resume_token has no ambiguous chars", () => {
  for (let i = 0; i < 50; i++) {
    const t = newResumeToken();
    assert.match(t, /^[a-z0-9]{4}-[a-z0-9]{4}$/);
    for (const ch of "01loi") assert.equal(t.includes(ch), false, `found '${ch}' in ${t}`);
  }
});

test("session_ids are unique across many calls", () => {
  const seen = new Set();
  for (let i = 0; i < 100; i++) {
    const s = newSessionId("qa-engineer", { date: "20260506" });
    assert.equal(seen.has(s), false, `duplicate ${s}`);
    seen.add(s);
  }
});
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/common/ids.mjs`:
```javascript
import { randomBytes } from "node:crypto";

const TOKEN_ALPHABET = "abcdefghjkmnpqrstuvwxyz23456789"; // no 0/o/1/l/i

function hex(n) {
  return randomBytes(n).toString("hex");
}

function isoDate() {
  const d = new Date();
  return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, "0")}${String(d.getUTCDate()).padStart(2, "0")}`;
}

export function newSessionId(personaSlug, { date } = {}) {
  return `${date ?? isoDate()}-${personaSlug}-${hex(2)}`;
}

export function newPseudonym() {
  return `participant-${hex(2)}`;
}

export function newResumeToken() {
  const group = () => {
    const b = randomBytes(4);
    let out = "";
    for (let i = 0; i < 4; i++) out += TOKEN_ALPHABET[b[i] % TOKEN_ALPHABET.length];
    return out;
  };
  return `${group()}-${group()}`;
}
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit**

```
git add helpers/common/ids.mjs tests/unit/ids.test.mjs
git commit -m "helpers/common: ids — session_id, pseudonym, resume_token generators"
```

---

### Task 1.4: Atomic JSON I/O helper

**Files:**
- Create: `helpers/common/json_io.mjs`
- Create: `tests/unit/json_io.test.mjs`

- [ ] **Step 1: Failing test**

`tests/unit/json_io.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { readJson, writeJsonAtomic } from "../../helpers/common/json_io.mjs";

function freshTmp() {
  return mkdtempSync(join(tmpdir(), "json-io-"));
}

test("round trip", () => {
  const dir = freshTmp();
  try {
    const p = join(dir, "x.json");
    writeJsonAtomic(p, { a: 1, b: [1, 2] });
    assert.deepEqual(readJson(p), { a: 1, b: [1, 2] });
  } finally { rmSync(dir, { recursive: true }); }
});

test("orphaned .tmp doesn't corrupt original", () => {
  const dir = freshTmp();
  try {
    const p = join(dir, "x.json");
    writeJsonAtomic(p, { old: true });
    writeFileSync(p + ".tmp", "garbage");
    assert.deepEqual(readJson(p), { old: true });
  } finally { rmSync(dir, { recursive: true }); }
});

test("read missing file throws", () => {
  const dir = freshTmp();
  try {
    assert.throws(() => readJson(join(dir, "nope.json")));
  } finally { rmSync(dir, { recursive: true }); }
});
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/common/json_io.mjs`:
```javascript
import { readFileSync, writeFileSync, renameSync, mkdirSync } from "node:fs";
import { dirname } from "node:path";

export function readJson(path) {
  return JSON.parse(readFileSync(path, "utf-8"));
}

export function writeJsonAtomic(path, data) {
  mkdirSync(dirname(path), { recursive: true });
  const tmp = `${path}.tmp`;
  writeFileSync(tmp, JSON.stringify(data, null, 2) + "\n", "utf-8");
  renameSync(tmp, path);
}
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit**

```
git add helpers/common/json_io.mjs tests/unit/json_io.test.mjs
git commit -m "helpers/common: json_io — atomic JSON read/write"
```

---

### Task 1.5: `check_writability` helper

**Files:**
- Create: `helpers/session/check_writability.mjs`
- Create: `tests/unit/check_writability.test.mjs`

- [ ] **Step 1: Failing test**

`tests/unit/check_writability.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { checkWritability } from "../../helpers/session/check_writability.mjs";

function tempRepo() {
  const root = mkdtempSync(join(tmpdir(), "check-w-"));
  const git = (...args) => execFileSync("git", args, { cwd: root, stdio: "ignore" });
  git("init", "-q");
  git("config", "user.email", "t@t");
  git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return { root, git };
}

test("uncommitted session is writable", () => {
  const { root } = tempRepo();
  try {
    const sd = join(root, "responses", "20260506-qa-eng-7c9a");
    mkdirSync(sd, { recursive: true });
    writeFileSync(join(sd, "session.json"), "{}");
    assert.equal(checkWritability(sd), true);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("committed session is refused", () => {
  const { root, git } = tempRepo();
  try {
    const sd = join(root, "responses", "20260506-qa-eng-7c9a");
    mkdirSync(sd, { recursive: true });
    writeFileSync(join(sd, "session.json"), "{}");
    git("add", ".");
    git("commit", "-m", "commit session");
    assert.equal(checkWritability(sd), false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement**

`helpers/session/check_writability.mjs`:
```javascript
import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, dirname, relative } from "node:path";

export function checkWritability(sessionDir) {
  const abs = resolve(sessionDir);
  let repo = abs;
  while (repo !== dirname(repo)) {
    if (existsSync(resolve(repo, ".git"))) break;
    repo = dirname(repo);
  }
  const rel = relative(repo, resolve(abs, "session.json")).replaceAll("\\", "/");
  try {
    execFileSync("git", ["ls-files", "--error-unmatch", rel], { cwd: repo, stdio: "ignore" });
    return false;  // tracked = committed = read-only
  } catch {
    return true;   // not tracked = uncommitted = writable
  }
}
```

- [ ] **Step 4: Run, verify PASS.**

- [ ] **Step 5: Commit**

```
git add helpers/session/check_writability.mjs tests/unit/check_writability.test.mjs
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

For each, prepend YAML frontmatter ABOVE the existing first heading.

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

(IDs above are derived from the existing numbered structure; AI-fit IDs from agent-mode-plan §9 #4: IC Q30+. Confirm against the current file's numbering before saving — adjust if drift has occurred.)

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

- [ ] **Step 6: Commit**

```
git add interview/
git commit -m "interview: add machine-readable frontmatter to all 5 persona scripts"
```

---

### Task 2.2: Frontmatter parser + `parse_script` helper

This task ships two related files: a tiny zero-dep flat-YAML parser for frontmatter, plus the script parser that uses it.

**Files:**
- Create: `helpers/common/frontmatter.mjs`
- Create: `helpers/script/parse_script.mjs`
- Create: `schemas/helpers/parse_script.output.schema.json`
- Create: `tests/unit/frontmatter.test.mjs`
- Create: `tests/unit/parse_script.test.mjs`

- [ ] **Step 1: Failing test for frontmatter**

`tests/unit/frontmatter.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseFrontmatter } from "../../helpers/common/frontmatter.mjs";

test("parses simple flat keys", () => {
  const { data, body } = parseFrontmatter("---\na: 1\nb: hello\n---\nbody\n");
  assert.deepEqual(data, { a: 1, b: "hello" });
  assert.equal(body, "body\n");
});

test("parses inline arrays of strings", () => {
  const { data } = parseFrontmatter(
    "---\nlist: [foo, bar-baz, hyphen-id-q3]\nempty: []\n---\n"
  );
  assert.deepEqual(data, { list: ["foo", "bar-baz", "hyphen-id-q3"], empty: [] });
});

test("preserves quoted strings with spaces", () => {
  const { data } = parseFrontmatter("---\npersona: QA Engineer (IC)\n---\n");
  assert.equal(data.persona, "QA Engineer (IC)");
});

test("returns null when no frontmatter", () => {
  const { data, body } = parseFrontmatter("# Just a Title\n\nBody\n");
  assert.equal(data, null);
  assert.equal(body, "# Just a Title\n\nBody\n");
});
```

- [ ] **Step 2: Run, verify FAIL.**

- [ ] **Step 3: Implement frontmatter parser**

`helpers/common/frontmatter.mjs`:
```javascript
// Tiny flat-YAML frontmatter parser. Supports:
//   - flat keys (no nested objects)
//   - string and integer scalars
//   - inline arrays of identifier-like strings: [foo, bar, baz-q2]
// Refuses to parse anything more complex (returns the raw line).
//
// Why hand-rolled: avoids any npm dependency. Our frontmatter shape is
// intentionally simple; this is enough for it.

const FRONTMATTER_RE = /^---\s*\r?\n([\s\S]*?)\r?\n---\s*\r?\n/;

export function parseFrontmatter(text) {
  const m = FRONTMATTER_RE.exec(text);
  if (!m) return { data: null, body: text };
  const data = {};
  for (const raw of m[1].split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const colon = line.indexOf(":");
    if (colon < 0) continue;
    const key = line.slice(0, colon).trim();
    let val = line.slice(colon + 1).trim();
    data[key] = parseValue(val);
  }
  return { data, body: text.slice(m[0].length) };
}

function parseValue(v) {
  if (v === "") return "";
  if (v === "null") return null;
  if (v === "true") return true;
  if (v === "false") return false;
  if (/^-?\d+$/.test(v)) return parseInt(v, 10);
  if (/^-?\d+\.\d+$/.test(v)) return parseFloat(v);
  if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
    return v.slice(1, -1);
  }
  if (v.startsWith("[") && v.endsWith("]")) {
    const inner = v.slice(1, -1).trim();
    if (inner === "") return [];
    return inner.split(",").map((s) => s.trim()).filter((s) => s.length > 0)
      .map((s) =>
        (s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))
          ? s.slice(1, -1) : s
      );
  }
  return v; // bare string
}
```

- [ ] **Step 4: Run frontmatter tests, verify PASS.**

- [ ] **Step 5: Failing test for parse_script**

`tests/unit/parse_script.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseScript } from "../../helpers/script/parse_script.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("parses qa-engineer script with derived ids", () => {
  const out = parseScript(join(REPO, "interview", "01-qa-engineer-interview.md"));
  assert.equal(out.frontmatter.script_id, "qa-engineer");
  assert.equal(out.frontmatter.script_version, "0.2.0");
  assert.ok(out.questions.length > 0);
  for (const q of out.questions) {
    assert.match(q.question_id, /^qa-engineer-q\d+$/);
  }
});

test("derives ids from numbered structure and extracts tags", () => {
  const dir = mkdtempSync(join(tmpdir(), "ps-"));
  try {
    const p = join(dir, "x.md");
    writeFileSync(p, [
      "---",
      "script_id: demo",
      "persona: Demo",
      "script_version: 0.1.0",
      "required_context_question_ids: []",
      "human_only_question_ids: []",
      "---",
      "",
      "# Demo Script",
      "",
      "## Section A",
      "",
      "1. First Q `[3a]`",
      "2. Second Q `[3b]` `[3c]`",
      "",
    ].join("\n"));
    const out = parseScript(p);
    assert.equal(out.questions[0].question_id, "demo-q1");
    assert.deepEqual(out.questions[0].tags, ["3a"]);
    assert.equal(out.questions[1].question_id, "demo-q2");
    assert.deepEqual(out.questions[1].tags.sort(), ["3b", "3c"]);
    assert.equal(out.questions[0].section_heading, "Section A");
  } finally { rmSync(dir, { recursive: true, force: true }); }
});

test("missing frontmatter throws", () => {
  const dir = mkdtempSync(join(tmpdir(), "ps-"));
  try {
    const p = join(dir, "x.md");
    writeFileSync(p, "# No frontmatter\n\n1. Q\n");
    assert.throws(() => parseScript(p), /frontmatter/i);
  } finally { rmSync(dir, { recursive: true, force: true }); }
});
```

- [ ] **Step 6: Implement parse_script + output schema**

`helpers/script/parse_script.mjs`:
```javascript
import { readFileSync } from "node:fs";
import { parseFrontmatter } from "../common/frontmatter.mjs";

const SECTION_RE = /^##+\s+(.+?)\s*$/;
const QUESTION_RE = /^\s*(\d+)\.\s+(.+?)\s*$/;
const TAG_RE = /`\[([^\]]+)\]`/g;

export function parseScript(path) {
  const text = readFileSync(path, "utf-8");
  const { data: frontmatter, body } = parseFrontmatter(text);
  if (!frontmatter) throw new Error(`Missing frontmatter in ${path}`);

  const scriptId = frontmatter.script_id;
  const questions = [];
  let section = "";

  for (const line of body.split(/\r?\n/)) {
    const sec = SECTION_RE.exec(line);
    if (sec) {
      section = sec[1].replace(/^\d+\.\s*/, "").split("(")[0].trim();
      continue;
    }
    const q = QUESTION_RE.exec(line);
    if (q) {
      const number = parseInt(q[1], 10);
      const rest = q[2];
      const tags = [...rest.matchAll(TAG_RE)].map((m) => m[1]);
      const promptText = rest.replace(TAG_RE, "").trim();
      questions.push({
        question_id: `${scriptId}-q${number}`,
        number,
        prompt_text: promptText,
        tags,
        section_heading: section,
      });
    }
  }
  return { frontmatter, questions };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    const out = parseScript(process.argv[2]);
    process.stdout.write(JSON.stringify(out, null, 2) + "\n");
  } catch (e) {
    process.stderr.write(JSON.stringify({ error: "parse_failed", message: e.message }) + "\n");
    process.exit(1);
  }
}
```

`schemas/helpers/parse_script.output.schema.json`:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["frontmatter", "questions"],
  "properties": {
    "frontmatter": {
      "type": "object",
      "required": ["script_id", "persona", "script_version", "required_context_question_ids", "human_only_question_ids"]
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

- [ ] **Step 7: Run all parse_script tests, verify PASS.** Note: the qa-engineer test depends on Task 2.1 having added frontmatter to that file.

- [ ] **Step 8: Commit**

```
git add helpers/common/frontmatter.mjs helpers/script/parse_script.mjs schemas/helpers/parse_script.output.schema.json tests/unit/frontmatter.test.mjs tests/unit/parse_script.test.mjs
git commit -m "helpers: frontmatter parser + parse_script (with derived ids)"
```

---

### Task 2.3: `question_filter` helper

**Files:**
- Create: `helpers/script/question_filter.mjs`
- Create: `tests/unit/question_filter.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/question_filter.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { filterQuestions } from "../../helpers/script/question_filter.mjs";

const SCRIPT = {
  frontmatter: {
    human_only_question_ids: ["x-q3"],
    required_context_question_ids: ["x-q1"],
  },
  questions: [
    { question_id: "x-q1", number: 1, prompt_text: "a", tags: [], section_heading: "" },
    { question_id: "x-q2", number: 2, prompt_text: "b", tags: [], section_heading: "" },
    { question_id: "x-q3", number: 3, prompt_text: "c", tags: [], section_heading: "" },
  ],
};

test("excludeHumanOnly drops human_only ids", () => {
  const f = filterQuestions(SCRIPT, { excludeHumanOnly: true });
  assert.deepEqual(f.map((q) => q.question_id), ["x-q1", "x-q2"]);
});

test("no filter returns all", () => {
  assert.equal(filterQuestions(SCRIPT).length, 3);
});
```

- [ ] **Step 2: Implement**

`helpers/script/question_filter.mjs`:
```javascript
export function filterQuestions(parsed, { excludeHumanOnly = false } = {}) {
  let qs = [...parsed.questions];
  if (excludeHumanOnly) {
    const ho = new Set(parsed.frontmatter?.human_only_question_ids ?? []);
    qs = qs.filter((q) => !ho.has(q.question_id));
  }
  return qs;
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

```
git add helpers/script/question_filter.mjs tests/unit/question_filter.test.mjs
git commit -m "helpers/script: question_filter for human_only exclusion"
```

---

### Task 2.4: `interview-script-loader` SKILL.md

**Files:**
- Create: `.github/skills/interview-script-loader/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: interview-script-loader
description: Use when the agent needs to load or validate a persona interview script — at session start, on resume to verify script_version, or when computing the next question. Parses the YAML frontmatter and derives an ordered question list with IDs.
---

# interview-script-loader

Parses a persona script (`interview/01-..05-*.md`) into a structured form: frontmatter (script_id, persona, script_version, required_context_question_ids, human_only_question_ids) plus an ordered list of questions with derived IDs (`{script_id}-q{number}`), prompt text, tags, and section heading.

## When to use

- At session start: load the script for the chosen persona.
- On resume: re-load the script and validate that `frontmatter.script_version` matches the session's locked version.
- When computing `advance_cursor`: filter out `human_only_question_ids`.

## How to invoke

```
node helpers/script/parse_script.mjs interview/<script-file>.md
```

Output: JSON to stdout matching `schemas/helpers/parse_script.output.schema.json`.

The agent typically imports the helper directly rather than spawning a subprocess:

```javascript
import { parseScript } from "../helpers/script/parse_script.mjs";
import { filterQuestions } from "../helpers/script/question_filter.mjs";
const parsed = parseScript("interview/02-qa-lead-interview.md");
const askable = filterQuestions(parsed, { excludeHumanOnly: true });
```

## Contract

- **Pure parsing.** No side effects; safe to call repeatedly.
- **Idempotent.** Same input produces identical output.
- **Question IDs derived**, not authored. Format `{script_id}-q{number}`. The numbered structure in the script file is the source of truth.
- **Failure mode:** missing or malformed frontmatter → throws (or exits non-zero with `{"error": "parse_failed", ...}` on stderr if invoked as CLI). Agent must abort session start with a clear message.

## Helpers

- `helpers/script/parse_script.mjs` — frontmatter + question extraction.
- `helpers/script/question_filter.mjs` — apply `human_only` exclusion.
- `helpers/common/frontmatter.mjs` — flat-YAML parser used by parse_script.
```

- [ ] **Step 2: Commit**

```
git add .github/skills/interview-script-loader/SKILL.md
git commit -m "skills: interview-script-loader"
```

---

## Phase 3: Session store

### Task 3.1: `new_session` helper

**Files:**
- Create: `helpers/session/new_session.mjs`
- Create: `schemas/helpers/new_session.output.schema.json`
- Create: `tests/unit/new_session.test.mjs`

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

`tests/unit/new_session.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { newSession } from "../../helpers/session/new_session.mjs";

const args = (overrides = {}) => ({
  scriptId: "qa-engineer",
  persona: "QA Engineer",
  scriptVersion: "0.2.0",
  accessMode: "direct",
  totalQuestions: 32,
  agentIdentifier: "copilot-interviewer-v1",
  ...overrides,
});

test("creates session dir with required files", () => {
  const root = mkdtempSync(join(tmpdir(), "ns-"));
  try {
    const r = newSession({ repoRoot: root, ...args() });
    assert.match(r.session_id, /^\d{8}-qa-engineer-[0-9a-f]{4}$/);
    const sd = r.session_dir;
    for (const f of ["session.json", "metadata.json", "answers.json", "resume-token.txt", "transcript.md", "flags.md"]) {
      assert.equal(existsSync(join(sd, f)), true, `missing ${f}`);
    }
    const session = JSON.parse(readFileSync(join(sd, "session.json"), "utf-8"));
    assert.equal(session.status, "in_progress");
    assert.equal(session.resume_token, r.resume_token);
    const meta = JSON.parse(readFileSync(join(sd, "metadata.json"), "utf-8"));
    assert.equal(meta.counts.total_questions, 32);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("optional interviewee_name persists in metadata", () => {
  const root = mkdtempSync(join(tmpdir(), "ns-"));
  try {
    const r = newSession({ repoRoot: root, ...args({ intervieweeName: "Jane Smith" }) });
    const meta = JSON.parse(readFileSync(join(r.session_dir, "metadata.json"), "utf-8"));
    assert.equal(meta.interviewee_name, "Jane Smith");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("facilitated mode writes facilitator_pseudonym + name", () => {
  const root = mkdtempSync(join(tmpdir(), "ns-"));
  try {
    const r = newSession({ repoRoot: root, ...args({ accessMode: "facilitated", facilitatorName: "Alex" }) });
    const meta = JSON.parse(readFileSync(join(r.session_dir, "metadata.json"), "utf-8"));
    assert.equal(meta.access_mode, "facilitated");
    assert.match(meta.facilitator_pseudonym, /^participant-[0-9a-f]{4}$/);
    assert.equal(meta.facilitator_name, "Alex");
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 3: Implement**

`helpers/session/new_session.mjs`:
```javascript
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { newSessionId, newPseudonym, newResumeToken } from "../common/ids.mjs";
import { writeJsonAtomic } from "../common/json_io.mjs";

export function newSession({
  repoRoot,
  scriptId,
  persona,
  scriptVersion,
  accessMode,
  totalQuestions,
  agentIdentifier,
  intervieweeName = null,
  facilitatorName = null,
}) {
  const sessionId = newSessionId(scriptId);
  const pseudonym = newPseudonym();
  const resumeToken = newResumeToken();
  const facilitatorPseudonym = accessMode === "facilitated" ? newPseudonym() : null;
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  const sessionDir = join(repoRoot, "responses", sessionId);
  mkdirSync(sessionDir, { recursive: false });

  writeJsonAtomic(join(sessionDir, "session.json"), {
    session_id: sessionId,
    pseudonym,
    resume_token: resumeToken,
    script_id: scriptId,
    script_version: scriptVersion,
    agent_identifier: agentIdentifier,
    started_at: now,
    last_active_at: now,
    status: "in_progress",
    cursor: { current_question_id: null, visited_question_ids: [] },
    required_context_satisfied: true,
    notes: null,
  });

  writeJsonAtomic(join(sessionDir, "metadata.json"), {
    session_id: sessionId,
    pseudonym,
    interviewee_name: intervieweeName,
    persona: scriptId,
    script_id: scriptId,
    script_version: scriptVersion,
    agent_identifier: agentIdentifier,
    access_mode: accessMode,
    facilitator_pseudonym: facilitatorPseudonym,
    facilitator_name: facilitatorName,
    started_at: now,
    completed_at: null,
    counts: { total_questions: totalQuestions, answered: 0, skipped: 0, declined: 0, human_only_gaps: 0 },
  });

  writeJsonAtomic(join(sessionDir, "answers.json"), []);
  writeFileSync(join(sessionDir, "resume-token.txt"), resumeToken + "\n", "utf-8");
  writeFileSync(join(sessionDir, "transcript.md"), `# Interview Transcript — ${sessionId}\n\n`, "utf-8");
  writeFileSync(join(sessionDir, "flags.md"), "# Flags\n\n", "utf-8");

  return { session_id: sessionId, pseudonym, resume_token: resumeToken, session_dir: sessionDir };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = JSON.parse(process.argv[2]);
  process.stdout.write(JSON.stringify(newSession(args)) + "\n");
}
```

- [ ] **Step 4: Run, verify PASS. Commit.**

```
git add helpers/session/new_session.mjs schemas/helpers/new_session.output.schema.json tests/unit/new_session.test.mjs
git commit -m "helpers/session: new_session — generate ids + write initial JSONs"
```

---

### Task 3.2: `load_session` helper (resume)

**Files:**
- Create: `helpers/session/load_session.mjs`
- Create: `tests/unit/load_session.test.mjs`

- [ ] **Step 1: Failing test**

`tests/unit/load_session.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { loadSession } from "../../helpers/session/load_session.mjs";

function tempRepo() {
  const root = mkdtempSync(join(tmpdir(), "ls-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q");
  git("config", "user.email", "t@t");
  git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return { root, git };
}

const seedArgs = {
  scriptId: "qa-engineer", persona: "QA", scriptVersion: "0.2.0",
  accessMode: "direct", totalQuestions: 32, agentIdentifier: "copilot-interviewer-v1",
};

test("load by resume_token", () => {
  const { root } = tempRepo();
  try {
    const seed = newSession({ repoRoot: root, ...seedArgs });
    const got = loadSession({ repoRoot: root, resumeToken: seed.resume_token });
    assert.equal(got.session.session_id, seed.session_id);
    assert.equal(got.writable, true);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("load by session_id", () => {
  const { root } = tempRepo();
  try {
    const seed = newSession({ repoRoot: root, ...seedArgs });
    const got = loadSession({ repoRoot: root, sessionId: seed.session_id });
    assert.equal(got.session.session_id, seed.session_id);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("unknown token throws", () => {
  const { root } = tempRepo();
  try {
    assert.throws(() => loadSession({ repoRoot: root, resumeToken: "zzzz-zzzz" }), /not found/i);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("committed session marked not writable", () => {
  const { root, git } = tempRepo();
  try {
    const seed = newSession({ repoRoot: root, ...seedArgs });
    git("add", "responses/");
    git("commit", "-m", "commit");
    const got = loadSession({ repoRoot: root, resumeToken: seed.resume_token });
    assert.equal(got.writable, false);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/session/load_session.mjs`:
```javascript
import { readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { readJson } from "../common/json_io.mjs";
import { checkWritability } from "./check_writability.mjs";

export function loadSession({ repoRoot, resumeToken = null, sessionId = null }) {
  if (!resumeToken && !sessionId) {
    throw new Error("resumeToken or sessionId required");
  }
  const responsesDir = join(repoRoot, "responses");
  let sessionDir = null;

  if (sessionId) {
    const candidate = join(responsesDir, sessionId);
    if (existsSync(join(candidate, "session.json"))) sessionDir = candidate;
  } else {
    for (const entry of readdirSync(responsesDir, { withFileTypes: true })) {
      if (!entry.isDirectory()) continue;
      const candidate = join(responsesDir, entry.name);
      const sf = join(candidate, "session.json");
      if (!existsSync(sf)) continue;
      const data = readJson(sf);
      if (data.resume_token === resumeToken) {
        sessionDir = candidate;
        break;
      }
    }
  }

  if (sessionDir === null) throw new Error("Session not found");

  return {
    session_dir: sessionDir,
    session: readJson(join(sessionDir, "session.json")),
    metadata: readJson(join(sessionDir, "metadata.json")),
    answers: readJson(join(sessionDir, "answers.json")),
    writable: checkWritability(sessionDir),
  };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = JSON.parse(process.argv[2]);
  process.stdout.write(JSON.stringify(loadSession(args)) + "\n");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

```
git add helpers/session/load_session.mjs tests/unit/load_session.test.mjs
git commit -m "helpers/session: load_session by resume_token or session_id"
```

---

### Task 3.3: `write_answer` helper

**Files:**
- Create: `helpers/session/write_answer.mjs`
- Create: `tests/unit/write_answer.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/write_answer.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { writeAnswer } from "../../helpers/session/write_answer.mjs";
import { readJson } from "../../helpers/common/json_io.mjs";

function repo() {
  const root = mkdtempSync(join(tmpdir(), "wa-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return root;
}
const seed = (root) => newSession({
  repoRoot: root, scriptId: "qa-engineer", persona: "QA", scriptVersion: "0.2.0",
  accessMode: "direct", totalQuestions: 32, agentIdentifier: "copilot-interviewer-v1",
});

const baseAns = {
  questionId: "qa-engineer-q1", tags: [], promptText: "...",
  status: "answered", responseText: "x", responseConfidence: null,
  followUps: [], skipReason: null,
};

test("appends new answer", () => {
  const root = repo();
  try {
    const s = seed(root);
    writeAnswer({ sessionDir: s.session_dir, ...baseAns });
    const ans = readJson(join(s.session_dir, "answers.json"));
    assert.equal(ans.length, 1);
    assert.equal(ans[0].question_id, "qa-engineer-q1");
    assert.equal(ans[0].follow_up_count, 0);
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("upsert updates existing", () => {
  const root = repo();
  try {
    const s = seed(root);
    writeAnswer({ sessionDir: s.session_dir, ...baseAns, status: "pending", responseText: null });
    writeAnswer({ sessionDir: s.session_dir, ...baseAns, responseText: "final" });
    const ans = readJson(join(s.session_dir, "answers.json"));
    assert.equal(ans.length, 1);
    assert.equal(ans[0].status, "answered");
    assert.equal(ans[0].response_text, "final");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("follow_up_count caps at 3", () => {
  const root = repo();
  try {
    const s = seed(root);
    const followUps = [0, 1, 2, 3].map((i) => ({ prompt: `f${i}`, response: "r" }));
    assert.throws(
      () => writeAnswer({ sessionDir: s.session_dir, ...baseAns, followUps }),
      /follow_up cap/i,
    );
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/session/write_answer.mjs`:
```javascript
import { join } from "node:path";
import { readJson, writeJsonAtomic } from "../common/json_io.mjs";
import { checkWritability } from "./check_writability.mjs";

export function writeAnswer({
  sessionDir,
  questionId,
  tags,
  promptText,
  status,
  responseText,
  responseConfidence,
  followUps,
  skipReason,
  revisedFrom = null,
}) {
  if (!checkWritability(sessionDir)) {
    const err = new Error(`Session is committed (read-only): ${sessionDir}`);
    err.code = "SESSION_READ_ONLY";
    throw err;
  }
  if (followUps.length > 3) throw new Error("follow_up cap exceeded (>3)");

  const sessionPath = join(sessionDir, "session.json");
  const session = readJson(sessionPath);
  const answersPath = join(sessionDir, "answers.json");
  const answers = readJson(answersPath) ?? [];
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");

  const entry = {
    question_id: questionId,
    tags,
    script_version: session.script_version,
    prompt_text: promptText,
    status,
    response_text: responseText,
    response_confidence: responseConfidence,
    follow_ups: followUps,
    follow_up_count: followUps.length,
    skip_reason: skipReason,
    revised_from: revisedFrom,
    timestamp: now,
  };

  const i = answers.findIndex((a) => a.question_id === questionId);
  if (i >= 0) answers[i] = entry;
  else answers.push(entry);
  writeJsonAtomic(answersPath, answers);

  session.last_active_at = now;
  if (!session.cursor.visited_question_ids.includes(questionId)) {
    session.cursor.visited_question_ids.push(questionId);
  }
  writeJsonAtomic(sessionPath, session);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = JSON.parse(process.argv[2]);
  writeAnswer(args);
  process.stdout.write(JSON.stringify({ ok: true }) + "\n");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

```
git add helpers/session/write_answer.mjs tests/unit/write_answer.test.mjs
git commit -m "helpers/session: write_answer — upsert + follow_up cap"
```

---

### Task 3.4: `advance_cursor` helper

**Files:**
- Create: `helpers/session/advance_cursor.mjs`
- Create: `tests/unit/advance_cursor.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/advance_cursor.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { advanceCursor } from "../../helpers/session/advance_cursor.mjs";
import { readJson, writeJsonAtomic } from "../../helpers/common/json_io.mjs";

const QS = [{ question_id: "x-q1" }, { question_id: "x-q2" }, { question_id: "x-q3" }];

function repo() {
  const root = mkdtempSync(join(tmpdir(), "ac-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return root;
}
const seed = (root) => newSession({
  repoRoot: root, scriptId: "x", persona: "X", scriptVersion: "0.0.0",
  accessMode: "direct", totalQuestions: 3, agentIdentifier: "test",
});

test("advance from initial returns first question", () => {
  const root = repo();
  try {
    const s = seed(root);
    const next = advanceCursor({ sessionDir: s.session_dir, questionsInOrder: QS, humanOnlyIds: new Set() });
    assert.equal(next, "x-q1");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("skips visited", () => {
  const root = repo();
  try {
    const s = seed(root);
    const sp = join(s.session_dir, "session.json");
    const ss = readJson(sp);
    ss.cursor.visited_question_ids = ["x-q1"];
    ss.cursor.current_question_id = "x-q1";
    writeJsonAtomic(sp, ss);
    const next = advanceCursor({ sessionDir: s.session_dir, questionsInOrder: QS, humanOnlyIds: new Set() });
    assert.equal(next, "x-q2");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("skips human_only", () => {
  const root = repo();
  try {
    const s = seed(root);
    const next = advanceCursor({
      sessionDir: s.session_dir, questionsInOrder: QS, humanOnlyIds: new Set(["x-q1", "x-q2"]),
    });
    assert.equal(next, "x-q3");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("returns null at end", () => {
  const root = repo();
  try {
    const s = seed(root);
    const sp = join(s.session_dir, "session.json");
    const ss = readJson(sp);
    ss.cursor.visited_question_ids = QS.map((q) => q.question_id);
    writeJsonAtomic(sp, ss);
    const next = advanceCursor({ sessionDir: s.session_dir, questionsInOrder: QS, humanOnlyIds: new Set() });
    assert.equal(next, null);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/session/advance_cursor.mjs`:
```javascript
import { join } from "node:path";
import { readJson, writeJsonAtomic } from "../common/json_io.mjs";
import { checkWritability } from "./check_writability.mjs";

export function advanceCursor({ sessionDir, questionsInOrder, humanOnlyIds }) {
  if (!checkWritability(sessionDir)) {
    throw new Error(`Session is committed (read-only): ${sessionDir}`);
  }
  const sessionPath = join(sessionDir, "session.json");
  const s = readJson(sessionPath);
  const visited = new Set(s.cursor.visited_question_ids);
  let nextId = null;
  for (const q of questionsInOrder) {
    if (humanOnlyIds.has(q.question_id) || visited.has(q.question_id)) continue;
    nextId = q.question_id;
    break;
  }
  s.cursor.current_question_id = nextId;
  writeJsonAtomic(sessionPath, s);
  return nextId;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const args = JSON.parse(process.argv[2]);
  args.humanOnlyIds = new Set(args.humanOnlyIds ?? []);
  process.stdout.write(JSON.stringify({ next_question_id: advanceCursor(args) }) + "\n");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 3.5: `revise_cursor` helper

**Files:**
- Create: `helpers/session/revise_cursor.mjs`
- Create: `tests/unit/revise_cursor.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/revise_cursor.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { reviseCursor } from "../../helpers/session/revise_cursor.mjs";
import { readJson, writeJsonAtomic } from "../../helpers/common/json_io.mjs";

function repo() {
  const root = mkdtempSync(join(tmpdir(), "rc-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return root;
}
const seed = (root) => newSession({
  repoRoot: root, scriptId: "x", persona: "X", scriptVersion: "0.0.0",
  accessMode: "direct", totalQuestions: 5, agentIdentifier: "test",
});
function setup(root) {
  const s = seed(root);
  const sp = join(s.session_dir, "session.json");
  const ss = readJson(sp);
  ss.cursor.visited_question_ids = ["x-q1", "x-q2", "x-q3"];
  ss.cursor.current_question_id = "x-q3";
  writeJsonAtomic(sp, ss);
  return s.session_dir;
}

test("revise to visited works", () => {
  const root = repo();
  try {
    const sd = setup(root);
    reviseCursor({ sessionDir: sd, targetQuestionId: "x-q1" });
    assert.equal(readJson(join(sd, "session.json")).cursor.current_question_id, "x-q1");
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("revise to unvisited throws", () => {
  const root = repo();
  try {
    const sd = setup(root);
    assert.throws(() => reviseCursor({ sessionDir: sd, targetQuestionId: "x-q4" }), /not visited/i);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/session/revise_cursor.mjs`:
```javascript
import { join } from "node:path";
import { readJson, writeJsonAtomic } from "../common/json_io.mjs";
import { checkWritability } from "./check_writability.mjs";

export function reviseCursor({ sessionDir, targetQuestionId }) {
  if (!checkWritability(sessionDir)) {
    throw new Error(`Session is committed (read-only): ${sessionDir}`);
  }
  const sp = join(sessionDir, "session.json");
  const s = readJson(sp);
  if (!s.cursor.visited_question_ids.includes(targetQuestionId)) {
    throw new Error(`Target question ${targetQuestionId} not visited`);
  }
  s.cursor.current_question_id = targetQuestionId;
  writeJsonAtomic(sp, s);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  reviseCursor(JSON.parse(process.argv[2]));
  process.stdout.write(JSON.stringify({ ok: true }) + "\n");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

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

CRUD layer for `responses/{session_id}/session.json`, `answers.json`, `metadata.json`. The agent calls into this skill for all state changes; it never writes those JSON files directly.

## Operations

| Operation | Helper | Purpose |
|---|---|---|
| `newSession` | `helpers/session/new_session.mjs` | Generate IDs, write initial 3 JSON files + resume-token.txt |
| `loadSession` | `helpers/session/load_session.mjs` | Resolve resume_token or session_id, return session state + writability |
| `advanceCursor` | `helpers/session/advance_cursor.mjs` | Move to next un-visited, non-human_only question |
| `reviseCursor` | `helpers/session/revise_cursor.mjs` | Back-nav to a previously-visited question |
| `writeAnswer` | `helpers/session/write_answer.mjs` | Upsert answer record; update last_active_at; track follow_up_count |
| `checkWritability` | `helpers/session/check_writability.mjs` | Refuse if session dir is committed in current HEAD |

## Contract

- All writes are atomic (write-tempfile + rename via `helpers/common/json_io.mjs`).
- `checkWritability` runs before every write; throws on committed sessions.
- `follow_up_count` is enforced ≤ 3 by `writeAnswer`.
- `cursor.visited_question_ids` is appended on every `writeAnswer` call.
- `last_active_at` is updated on every successful write.
- Single-writer rule is documented (don't run two agent instances against the same session); not enforced via lock file. Atomic writes provide sufficient corruption safety.

## Failure modes

- Session not found → throws "Session not found".
- Session committed (read-only) → throws with code `SESSION_READ_ONLY`.
- `follow_up_count` exceeded → throws "follow_up cap exceeded".
- Revise to un-visited question → throws "not visited".
```

- [ ] **Step 2: Commit**

```
git add helpers/session/advance_cursor.mjs helpers/session/revise_cursor.mjs tests/unit/advance_cursor.test.mjs tests/unit/revise_cursor.test.mjs .github/skills/interview-session-store/SKILL.md
git commit -m "skills: interview-session-store + advance_cursor + revise_cursor helpers"
```

---

## Phase 4: Behavioral skills

### Task 4.1: `validate_confidence` helper

**Files:**
- Create: `helpers/confidence/validate_confidence.mjs`
- Create: `tests/unit/validate_confidence.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/validate_confidence.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { validateConfidence } from "../../helpers/confidence/validate_confidence.mjs";

test("accepts valid values", () => {
  for (const v of ["tracked", "estimated", "inferred", "discussion-derived", null]) {
    validateConfidence(v); // no throw
  }
});
test("rejects invalid", () => {
  assert.throws(() => validateConfidence("guess"), /response_confidence/);
});
```

- [ ] **Step 2: Implement**

`helpers/confidence/validate_confidence.mjs`:
```javascript
const ALLOWED = new Set(["tracked", "estimated", "inferred", "discussion-derived", null]);

export function validateConfidence(value) {
  if (!ALLOWED.has(value)) {
    throw new Error(`response_confidence must be one of [tracked, estimated, inferred, discussion-derived, null], got ${JSON.stringify(value)}`);
  }
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 4.2: `classify_skip` helper

**Files:**
- Create: `helpers/skip/classify_skip.mjs`
- Create: `tests/unit/classify_skip.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/classify_skip.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { classifySkip } from "../../helpers/skip/classify_skip.mjs";

const cases = [
  ["I don't know", "not_measured"],
  ["no idea", "not_measured"],
  ["we don't measure that", "not_measured"],
  ["I'd rather not answer", "declined"],
  ["pass on that one", "declined"],
  ["prefer not to say", "declined"],
  ["doesn't apply to me", "not_applicable"],
  ["N/A", "not_applicable"],
  ["not applicable", "not_applicable"],
];
for (const [phrase, expected] of cases) {
  test(`${phrase} -> ${expected}`, () => assert.equal(classifySkip(phrase), expected));
}
test("unrecognized -> null", () => assert.equal(classifySkip("the weather is nice"), null));
```

- [ ] **Step 2: Implement**

`helpers/skip/classify_skip.mjs`:
```javascript
const PATTERNS = {
  declined: [/\b(rather not|prefer not|won't|won't say|decline|pass)\b/i],
  not_applicable: [/\b(not applicable|doesn't apply|doesn't pertain|n\/a)\b/i],
  not_measured: [/\b(don't know|no idea|don't measure|not measured|haven't measured|unsure|not sure)\b/i],
};

export function classifySkip(utterance) {
  const text = utterance.toLowerCase();
  for (const kind of ["declined", "not_applicable", "not_measured"]) {
    for (const p of PATTERNS[kind]) if (p.test(text)) return kind;
  }
  return null;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  process.stdout.write(JSON.stringify({ kind: classifySkip(process.argv[2]) }) + "\n");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 4.3: `interview-confidence-tagging` SKILL.md

- [ ] **Step 1: Write `.github/skills/interview-confidence-tagging/SKILL.md`** — same content as previous plan iteration but pointing at `.mjs` helpers:

```markdown
---
name: interview-confidence-tagging
description: Use when an answer contains a number, percentage, duration, count, ratio, or any quantitative claim — also when the question's tag includes [3d] (Baseline Metrics), regardless of whether the answer was numeric. Probes for tracked vs. estimated and records response_confidence.
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
- **Validate before persisting** with `helpers/confidence/validate_confidence.mjs` to ensure the recorded value is in the allowed enum.

## Persistence

After the probe, call `interview-session-store.writeAnswer(...)` with `responseConfidence` set. The follow-up exchange goes into `followUps[]`.
```

- [ ] **Step 2: Commit.**

---

### Task 4.4: `interview-skip-handling` SKILL.md

- [ ] **Step 1: Write `.github/skills/interview-skip-handling/SKILL.md`:**

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
| "I don't know" / "we don't measure that" | `skipped` | `not_measured` | **Once**, only for required-context questions |
| "I'd rather not answer" / "pass" | `declined` | `declined` | **Never.** Note in `flags.md`. |
| "That doesn't apply" / "N/A" | `skipped` | `not_applicable` | No |
| (agent-initiated, AI-fit question) | `skipped` | `human_only` | Never. Increment `metadata.counts.human_only_gaps`. |

## Helper

Use `helpers/skip/classify_skip.mjs`:

```javascript
import { classifySkip } from "../helpers/skip/classify_skip.mjs";
const kind = classifySkip("I'd rather not say"); // -> "declined"
```

## Required-context re-prompt

If `skip_reason` is `not_measured` AND the question's `question_id` is in the script's `required_context_question_ids`, the agent re-prompts ONCE:

> "That's an important one for context — could you give a rough estimate, or describe what you observe? If you genuinely don't know, that's fine and we'll move on."

If still skipped after the re-prompt, set `metadata.required_context_satisfied: false` and continue.

## Persistence

Call `interview-session-store.writeAnswer(...)` with `status` and `skipReason` populated. `responseText` is `null` for skips.
```

- [ ] **Step 2: Commit.**

---

### Task 4.5: `interview-refinement` SKILL.md

- [ ] **Step 1: Write `.github/skills/interview-refinement/SKILL.md`:**

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

- Each follow-up exchange is appended to `followUps[]` in the answer record.
- The committed answer goes into `responseText`. The compiler reads `response_text`; the dialogue is preserved for the transcript.
- After the 3rd follow-up without a clear committed answer, `responseText` is the best summary the agent can extract from the dialogue, with `responseConfidence: discussion-derived`.

## Adjacent topics

If the interviewee raises an adjacent topic during refinement, the agent notes it for `flags.md` (a 1-line summary) and returns to the current question. Do not pivot the conversation.
```

- [ ] **Step 2: Commit.**

---

### Task 4.6: `interview-bias-mitigation` SKILL.md

- [ ] **Step 1: Write `.github/skills/interview-bias-mitigation/SKILL.md`:**

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
git add .github/skills/interview-confidence-tagging/ .github/skills/interview-skip-handling/ .github/skills/interview-refinement/ .github/skills/interview-bias-mitigation/ helpers/confidence/ helpers/skip/ tests/unit/validate_confidence.test.mjs tests/unit/classify_skip.test.mjs
git commit -m "skills: behavioral (refinement, confidence-tagging, skip-handling, bias-mitigation) + helpers"
```

---

## Phase 5: Finalize

### Task 5.1: `generate_transcript` helper

**Files:**
- Create: `helpers/finalize/generate_transcript.mjs`
- Create: `tests/unit/generate_transcript.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/generate_transcript.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { generateTranscript } from "../../helpers/finalize/generate_transcript.mjs";
import { writeJsonAtomic } from "../../helpers/common/json_io.mjs";

function repo() {
  const root = mkdtempSync(join(tmpdir(), "gt-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return root;
}

test("transcript includes questions, responses, follow-ups", () => {
  const root = repo();
  try {
    const s = newSession({
      repoRoot: root, scriptId: "qa-engineer", persona: "QA",
      scriptVersion: "0.2.0", accessMode: "direct", totalQuestions: 2,
      agentIdentifier: "test",
    });
    writeJsonAtomic(join(s.session_dir, "answers.json"), [
      { question_id: "qa-engineer-q1", tags: [], script_version: "0.2.0",
        prompt_text: "Q1?", status: "answered", response_text: "A1",
        response_confidence: null, follow_ups: [], follow_up_count: 0,
        skip_reason: null, revised_from: null, timestamp: "2026-05-06T14:00:00Z" },
      { question_id: "qa-engineer-q2", tags: ["3d"], script_version: "0.2.0",
        prompt_text: "Q2?", status: "answered", response_text: "5",
        response_confidence: "estimated",
        follow_ups: [{ prompt: "Tracked or estimated?", response: "Estimated" }],
        follow_up_count: 1, skip_reason: null, revised_from: null,
        timestamp: "2026-05-06T14:01:00Z" },
    ]);
    generateTranscript({ sessionDir: s.session_dir });
    const text = readFileSync(join(s.session_dir, "transcript.md"), "utf-8");
    for (const expected of ["Q1?", "A1", "Q2?", "Estimated", "Tracked or estimated?"]) {
      assert.ok(text.includes(expected), `missing "${expected}"`);
    }
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/finalize/generate_transcript.mjs`:
```javascript
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { readJson } from "../common/json_io.mjs";

export function generateTranscript({ sessionDir }) {
  const session = readJson(join(sessionDir, "session.json"));
  const metadata = readJson(join(sessionDir, "metadata.json"));
  const answers = readJson(join(sessionDir, "answers.json")) ?? [];

  const lines = [
    `# Interview Transcript — ${session.session_id}`,
    "",
    `- **Persona:** ${metadata.persona}`,
    `- **Script version:** ${metadata.script_version}`,
    `- **Started:** ${metadata.started_at}`,
    `- **Completed:** ${metadata.completed_at ?? "(in progress)"}`,
    "",
    "---",
    "",
  ];

  for (const e of answers) {
    lines.push(`## ${e.question_id}  \`${e.tags.join(", ") || "–"}\``);
    lines.push("");
    lines.push(`> ${e.prompt_text}`);
    lines.push("");
    if (e.status === "answered") lines.push(e.response_text ?? "");
    else if (e.status === "revised") lines.push(`**(revised from earlier answer)** ${e.response_text}`);
    else lines.push(`_(skipped — ${e.skip_reason ?? e.status})_`);
    if (e.response_confidence) {
      lines.push("");
      lines.push(`_Confidence: ${e.response_confidence}_`);
    }
    for (const fu of e.follow_ups ?? []) {
      lines.push("");
      lines.push(`> _Follow-up:_ ${fu.prompt}`);
      if (fu.response) lines.push(`>> ${fu.response}`);
    }
    lines.push("");
  }
  writeFileSync(join(sessionDir, "transcript.md"), lines.join("\n"), "utf-8");
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 5.2: `finalize_session` orchestrator

**Files:**
- Create: `helpers/finalize/finalize_session.mjs`
- Create: `tests/unit/finalize_session.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/finalize_session.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { newSession } from "../../helpers/session/new_session.mjs";
import { finalizeSession } from "../../helpers/finalize/finalize_session.mjs";
import { readJson, writeJsonAtomic } from "../../helpers/common/json_io.mjs";

function repo() {
  const root = mkdtempSync(join(tmpdir(), "fs-"));
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q"); git("config", "user.email", "t@t"); git("config", "user.name", "t");
  git("commit", "--allow-empty", "-m", "init");
  return root;
}

test("marks complete and recomputes counts", () => {
  const root = repo();
  try {
    const s = newSession({
      repoRoot: root, scriptId: "qa-engineer", persona: "QA",
      scriptVersion: "0.2.0", accessMode: "direct", totalQuestions: 2,
      agentIdentifier: "test",
    });
    writeJsonAtomic(join(s.session_dir, "answers.json"), [
      { question_id: "qa-engineer-q1", tags: [], script_version: "0.2.0", prompt_text: "?",
        status: "answered", response_text: "x", response_confidence: null,
        follow_ups: [], follow_up_count: 0, skip_reason: null, revised_from: null,
        timestamp: "2026-05-06T14:00:00Z" },
      { question_id: "qa-engineer-q2", tags: [], script_version: "0.2.0", prompt_text: "?",
        status: "skipped", response_text: null, response_confidence: null,
        follow_ups: [], follow_up_count: 0, skip_reason: "human_only", revised_from: null,
        timestamp: "2026-05-06T14:01:00Z" },
    ]);
    finalizeSession({ sessionDir: s.session_dir });
    const ss = readJson(join(s.session_dir, "session.json"));
    const meta = readJson(join(s.session_dir, "metadata.json"));
    assert.equal(ss.status, "complete");
    assert.notEqual(meta.completed_at, null);
    assert.equal(meta.counts.answered, 1);
    assert.equal(meta.counts.human_only_gaps, 1);
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/finalize/finalize_session.mjs`:
```javascript
import { join } from "node:path";
import { readJson, writeJsonAtomic } from "../common/json_io.mjs";
import { checkWritability } from "../session/check_writability.mjs";
import { generateTranscript } from "./generate_transcript.mjs";

export function finalizeSession({ sessionDir }) {
  if (!checkWritability(sessionDir)) {
    throw new Error(`Session is committed: ${sessionDir}`);
  }
  const sp = join(sessionDir, "session.json");
  const mp = join(sessionDir, "metadata.json");
  const session = readJson(sp);
  const meta = readJson(mp);
  const answers = readJson(join(sessionDir, "answers.json")) ?? [];

  const counts = {
    total_questions: meta.counts.total_questions,
    answered: answers.filter((a) => a.status === "answered" || a.status === "revised").length,
    skipped: answers.filter((a) => a.status === "skipped" && a.skip_reason !== "human_only").length,
    declined: answers.filter((a) => a.status === "declined").length,
    human_only_gaps: answers.filter((a) => a.skip_reason === "human_only").length,
  };
  meta.counts = counts;
  const now = new Date().toISOString().replace(/\.\d{3}Z$/, "Z");
  meta.completed_at = now;
  session.status = "complete";
  session.last_active_at = now;

  writeJsonAtomic(mp, meta);
  writeJsonAtomic(sp, session);
  generateTranscript({ sessionDir });
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 5.3: `git_branch_commit_push` helper

**Files:**
- Create: `helpers/finalize/git_branch_commit_push.mjs`
- Create: `tests/unit/git_branch_commit_push.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/git_branch_commit_push.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { gitBranchCommitPush } from "../../helpers/finalize/git_branch_commit_push.mjs";

function repoWithRemote() {
  const root = mkdtempSync(join(tmpdir(), "gbcp-"));
  const bare = join(root, "remote.git");
  const work = join(root, "work");
  execFileSync("git", ["init", "--bare", "-q", bare], { stdio: "ignore" });
  execFileSync("git", ["init", "-q", work], { stdio: "ignore" });
  const git = (...a) => execFileSync("git", a, { cwd: work, stdio: "ignore" });
  git("config", "user.email", "t@t");
  git("config", "user.name", "t");
  git("remote", "add", "origin", bare);
  git("commit", "--allow-empty", "-m", "init");
  // Use whatever default branch the repo has
  const branch = execFileSync("git", ["rev-parse", "--abbrev-ref", "HEAD"], { cwd: work, encoding: "utf-8" }).trim();
  git("push", "-u", "origin", branch);
  return { root, work };
}

test("creates branch and pushes", () => {
  const { root, work } = repoWithRemote();
  try {
    const sd = join(work, "responses", "20260506-qa-eng-7c9a");
    mkdirSync(sd, { recursive: true });
    writeFileSync(join(sd, "session.json"), "{}");
    const out = gitBranchCommitPush({ repoRoot: work, sessionId: "20260506-qa-eng-7c9a", persona: "qa-engineer" });
    assert.equal(out.branch, "interview/20260506-qa-eng-7c9a");
    const branches = execFileSync("git", ["branch", "-a"], { cwd: work, encoding: "utf-8" });
    assert.ok(branches.includes("interview/20260506-qa-eng-7c9a"));
  } finally { rmSync(root, { recursive: true, force: true }); }
});

test("refuses dirty unrelated working tree", () => {
  const { root, work } = repoWithRemote();
  try {
    writeFileSync(join(work, "unrelated.txt"), "x");
    const sd = join(work, "responses", "20260506-qa-eng-7c9a");
    mkdirSync(sd, { recursive: true });
    writeFileSync(join(sd, "session.json"), "{}");
    assert.throws(
      () => gitBranchCommitPush({ repoRoot: work, sessionId: "20260506-qa-eng-7c9a", persona: "qa-engineer" }),
      /dirty/i
    );
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/finalize/git_branch_commit_push.mjs`:
```javascript
import { execFileSync } from "node:child_process";

function git(cwd, args, { allowFail = false } = {}) {
  try {
    return { stdout: execFileSync("git", args, { cwd, encoding: "utf-8" }), code: 0 };
  } catch (e) {
    if (allowFail) return { stdout: e.stdout?.toString() ?? "", stderr: e.stderr?.toString() ?? "", code: e.status ?? 1 };
    throw e;
  }
}

export function gitBranchCommitPush({ repoRoot, sessionId, persona }) {
  const sessionRel = `responses/${sessionId}/`;
  const status = git(repoRoot, ["status", "--porcelain"]).stdout
    .split(/\r?\n/).filter(Boolean);
  const unrelated = status.filter((line) => !line.slice(3).replaceAll("\\", "/").startsWith(sessionRel));
  if (unrelated.length > 0) {
    throw new Error(`Working tree has dirty unrelated files; refusing finalize: ${JSON.stringify(unrelated.slice(0, 3))}`);
  }

  const branch = `interview/${sessionId}`;
  git(repoRoot, ["checkout", "-b", branch]);
  git(repoRoot, ["add", sessionRel]);
  git(repoRoot, ["commit", "-m", `Interview session ${sessionId} (${persona})`]);
  const push = git(repoRoot, ["push", "-u", "origin", branch], { allowFail: true });
  return {
    branch,
    pushed: push.code === 0,
    push_error: push.code === 0 ? null : (push.stderr ?? "").trim(),
  };
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

---

### Task 5.4: `package_bundle` helper

**Note:** Stdlib-only ZIP writers are ~150 lines. Pragmatic alternative: shell out to system `tar` (present on Windows 10+, Mac, Linux). The bundle becomes `.tar.gz` instead of `.zip` — same outcome (a portable archive). Spec mentions `.zip` but the format choice is implementation-time per [spec §12 #5](../specs/2026-05-06-interview-skills-design.md). Implementing as `.tar.gz` here.

**Files:**
- Create: `helpers/finalize/package_bundle.mjs`
- Create: `tests/unit/package_bundle.test.mjs`

- [ ] **Step 1: Failing test**

```javascript
// tests/unit/package_bundle.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, existsSync, rmSync, statSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { packageBundle } from "../../helpers/finalize/package_bundle.mjs";

test("produces a non-empty archive containing session files", () => {
  const root = mkdtempSync(join(tmpdir(), "pb-"));
  try {
    const sd = join(root, "responses", "20260506-qa-eng-7c9a");
    mkdirSync(sd, { recursive: true });
    writeFileSync(join(sd, "session.json"), "{}");
    writeFileSync(join(sd, "answers.json"), "[]");
    const out = packageBundle({ repoRoot: root, sessionId: "20260506-qa-eng-7c9a" });
    assert.ok(existsSync(out.bundle_path));
    assert.ok(statSync(out.bundle_path).size > 0);
    // List contents to verify
    const list = execFileSync("tar", ["-tzf", out.bundle_path], { encoding: "utf-8" });
    assert.ok(list.includes("session.json"));
    assert.ok(list.includes("answers.json"));
  } finally { rmSync(root, { recursive: true, force: true }); }
});
```

- [ ] **Step 2: Implement**

`helpers/finalize/package_bundle.mjs`:
```javascript
import { existsSync } from "node:fs";
import { join } from "node:path";
import { execFileSync } from "node:child_process";

export function packageBundle({ repoRoot, sessionId }) {
  const sessionDir = join(repoRoot, "responses", sessionId);
  if (!existsSync(sessionDir)) throw new Error(`Session dir not found: ${sessionDir}`);
  const outPath = join(repoRoot, "responses", `${sessionId}.tar.gz`);
  // -C cd into responses/, then archive sessionId/. This way paths in the archive are session-relative.
  execFileSync("tar", ["-czf", outPath, "-C", join(repoRoot, "responses"), sessionId], { stdio: "ignore" });
  return { bundle_path: outPath };
}
```

- [ ] **Step 3: Run, verify PASS. Commit.**

```
git add helpers/finalize/ tests/unit/generate_transcript.test.mjs tests/unit/finalize_session.test.mjs tests/unit/git_branch_commit_push.test.mjs tests/unit/package_bundle.test.mjs
git commit -m "helpers/finalize: generate_transcript, finalize_session, git_branch_commit_push, package_bundle"
```

---

### Task 5.5: `interview-finalize` SKILL.md

- [ ] **Step 1: Write `.github/skills/interview-finalize/SKILL.md`:**

```markdown
---
name: interview-finalize
description: Use when the interviewee indicates they're done, the cursor reaches the end of the script, or the agent times out a long-idle session and the user confirms wrap-up. Marks session complete, regenerates the transcript, runs the git transport (default), and optionally produces a portable bundle.
---

# interview-finalize

End-of-session work. Sequence:

1. **Validate** session is `in_progress` and writable. Refuse otherwise.
2. **Regenerate transcript** from `answers.json` → `transcript.md`.
3. **Recompute counts** in `metadata.json` (answered, skipped, declined, human_only_gaps).
4. **Mark complete**: `session.json.status: complete`, `metadata.json.completed_at: now`.
5. **Git transport** (default): branch `interview/{session_id}`, add session dir, commit, push.
6. **Optional bundle** (`bundle: true` or git failure): write `responses/{session_id}.tar.gz` via system `tar`.

## Helpers

- `helpers/finalize/finalize_session.mjs` — steps 1–4.
- `helpers/finalize/git_branch_commit_push.mjs` — step 5.
- `helpers/finalize/package_bundle.mjs` — step 6.
- `helpers/finalize/generate_transcript.mjs` — internal, called by `finalize_session`.

## Branch naming

`interview/{session_id}`, e.g., `interview/20260506-qa-eng-7c9a`. Refuses if branch already exists on origin.

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

2. **If resuming**: ask for the resume token (format `xxxx-xxxx`). Call `interview-session-store.loadSession({ resumeToken })`.
   - If `writable: false` → "This session was finalized and committed. To revise it, start a new session and we can incorporate the relevant updates."
   - If found and writable: load the script via `interview-script-loader.parseScript(script_id)`. If `script_version` differs from the script file, lock to the original version (don't auto-upgrade). Resume at `cursor.current_question_id`. Re-prompt any `pending` or null-response follow-ups.

3. **If new**:
   1. Ask: "Which persona — QA Engineer, QA Lead, Developer, Release Manager, or Product Owner?"
   2. Ask: "Are you the interviewee, or facilitating for someone else?" → `accessMode: direct | facilitated`.
   3. Ask: "What should I call you?" (optional). If facilitated, also ask for the facilitator's name.
   4. Call `interview-script-loader.parseScript(<script>)`.
   5. Call `interview-session-store.newSession(...)` with the captured fields and `totalQuestions = parsed.questions.length`.
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
8. **Persist** — call `interview-session-store.writeAnswer(...)` with the full record.
9. **Advance** — call `interview-session-store.advanceCursor(...)` for the next question.

## Navigation

If the interviewee says "go back to question N" / "I'd like to revise q5" / similar:
1. Call `interview-session-store.reviseCursor({ targetQuestionId })`.
2. Re-ask the question.
3. Persist with `revisedFrom: <previous response_text>` and `status: revised`.
4. Return to the cursor's prior position (forward through still-unvisited questions).

## Wrap-up

When `advanceCursor` returns `null` (script complete) OR interviewee says they're done:
1. **Summary**: show counts ("answered X, skipped Y, declined Z, AI-fit gaps {n} for human follow-up").
2. **Open feedback**: "Anything else you want to flag for the synthesis team that we didn't ask about directly?" → append to `flags.md`.
3. **Finalize**: call `interview-finalize` with default git transport. Surface branch URL.
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
| `interview-session-store` | data-layer | CRUD on session/answers/metadata JSON |
| `interview-finalize` | data-layer | Status flip, transcript, git push, optional bundle |
| `interview-refinement` | behavioral | ≤3 follow-ups for thin answers |
| `interview-confidence-tagging` | behavioral | Probe tracked vs. estimated |
| `interview-skip-handling` | behavioral | 3 skip kinds + human_only |
| `interview-bias-mitigation` | behavioral | Methodology rules; refuse advice requests |

## Layout

- `<skill-name>/SKILL.md` — skill manifest + behavior contract.
- `helpers/<group>/*.mjs` — Node helpers each skill calls. **Zero npm dependencies.**
- `schemas/*.json` — JSON schemas for state files and helper output.

## Running tests

```
node --test tests/         # all tests
node --test tests/unit/    # unit only
```

No `npm install` required — uses Node ≥ 18 built-ins (`node:test`, `node:fs`, `node:crypto`, `node:child_process`).

## Design and execution

See [docs/superpowers/specs/2026-05-06-interview-skills-design.md](../../docs/superpowers/specs/2026-05-06-interview-skills-design.md) for the full design and [docs/superpowers/plans/2026-05-06-interview-skills.md](../../docs/superpowers/plans/2026-05-06-interview-skills.md) for the implementation plan.
```

- [ ] **Step 2: Commit.**

---

### Task 6.3: Integration test harness + qa-engineer fixture

**Files:**
- Create: `tests/integration/scripted_interview.test.mjs`
- Create: `tests/fixtures/canned_responses/qa-engineer.json` (skeleton; expanded in Task 6.4)

- [ ] **Step 1: Skeleton canned-responses fixture for QA Engineer**

`tests/fixtures/canned_responses/qa-engineer.json`:
```json
{
  "qa-engineer-q1": { "response": "About 18 months", "confidence": null },
  "qa-engineer-q2": { "response": "API and integration tests primarily", "confidence": null },
  "qa-engineer-q3": { "response": "About 30% authoring, 30% execution, 40% verification", "confidence": "estimated" },
  "qa-engineer-q4": { "response": "Last week I authored a contract test for the new endpoint", "confidence": null },
  "qa-engineer-q5": { "response": "Acceptance criteria came from the ticket; mostly clear", "confidence": null },
  "qa-engineer-q30": { "skip": "human_only" },
  "qa-engineer-q31": { "skip": "human_only" },
  "qa-engineer-q32": { "skip": "human_only" }
}
```

(Expanded to a full one-entry-per-question_id fixture in Task 6.4. Missing keys are treated by the harness as `skip: not_measured`.)

- [ ] **Step 2: Write the integration harness**

`tests/integration/scripted_interview.test.mjs`:
```javascript
import { test } from "node:test";
import assert from "node:assert/strict";
import { cpSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";

import { parseScript } from "../../helpers/script/parse_script.mjs";
import { filterQuestions } from "../../helpers/script/question_filter.mjs";
import { newSession } from "../../helpers/session/new_session.mjs";
import { writeAnswer } from "../../helpers/session/write_answer.mjs";
import { advanceCursor } from "../../helpers/session/advance_cursor.mjs";
import { validateConfidence } from "../../helpers/confidence/validate_confidence.mjs";
import { finalizeSession } from "../../helpers/finalize/finalize_session.mjs";
import { readJson } from "../../helpers/common/json_io.mjs";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function tempRepoWithScripts() {
  const root = mkdtempSync(join(tmpdir(), "si-"));
  cpSync(join(REPO, "interview"), join(root, "interview"), { recursive: true });
  const git = (...a) => execFileSync("git", a, { cwd: root, stdio: "ignore" });
  git("init", "-q");
  git("config", "user.email", "t@t");
  git("config", "user.name", "t");
  git("add", "interview");
  git("commit", "-m", "init");
  return root;
}

const cases = [
  { scriptFile: "01-qa-engineer-interview.md", fixture: "qa-engineer.json", scriptId: "qa-engineer" },
];

for (const c of cases) {
  test(`full session flow: ${c.scriptId}`, () => {
    const root = tempRepoWithScripts();
    try {
      const parsed = parseScript(join(root, "interview", c.scriptFile));
      const questions = filterQuestions(parsed, { excludeHumanOnly: false });
      const humanOnlyIds = new Set(parsed.frontmatter.human_only_question_ids ?? []);
      const canned = JSON.parse(readFileSync(join(REPO, "tests/fixtures/canned_responses", c.fixture), "utf-8"));

      const seed = newSession({
        repoRoot: root, scriptId: c.scriptId, persona: parsed.frontmatter.persona,
        scriptVersion: parsed.frontmatter.script_version, accessMode: "direct",
        totalQuestions: questions.length, agentIdentifier: "copilot-interviewer-test",
      });

      while (true) {
        const next = advanceCursor({ sessionDir: seed.session_dir, questionsInOrder: questions, humanOnlyIds });
        if (next === null) break;
        const q = questions.find((x) => x.question_id === next);
        const ans = canned[next] ?? {};
        if (ans.skip === "human_only") {
          writeAnswer({
            sessionDir: seed.session_dir, questionId: next, tags: q.tags, promptText: q.prompt_text,
            status: "skipped", responseText: null, responseConfidence: null,
            followUps: [], skipReason: "human_only",
          });
        } else if ("response" in ans) {
          if (ans.confidence) validateConfidence(ans.confidence);
          writeAnswer({
            sessionDir: seed.session_dir, questionId: next, tags: q.tags, promptText: q.prompt_text,
            status: "answered", responseText: ans.response, responseConfidence: ans.confidence ?? null,
            followUps: [], skipReason: null,
          });
        } else {
          writeAnswer({
            sessionDir: seed.session_dir, questionId: next, tags: q.tags, promptText: q.prompt_text,
            status: "skipped", responseText: null, responseConfidence: null,
            followUps: [], skipReason: "not_measured",
          });
        }
      }

      finalizeSession({ sessionDir: seed.session_dir });
      const ss = readJson(join(seed.session_dir, "session.json"));
      const meta = readJson(join(seed.session_dir, "metadata.json"));
      assert.equal(ss.status, "complete");
      assert.equal(meta.counts.human_only_gaps, humanOnlyIds.size);
    } finally { rmSync(root, { recursive: true, force: true }); }
  });
}
```

- [ ] **Step 3: Run integration test for QA Engineer**

```
node --test tests/integration/scripted_interview.test.mjs
```

Expected: PASS. (May print a warning about partial fixture coverage; that's fine — Task 6.4 fills it in.)

- [ ] **Step 4: Commit.**

```
git add tests/integration/ tests/fixtures/
git commit -m "tests: scripted interview integration harness + qa-engineer skeleton fixture"
```

---

### Task 6.4: Fixtures for the remaining four personas

For each remaining persona script, create a canned-responses fixture file with **one entry per `question_id`** (skip-or-response). Add the persona to the `cases` parametrize list in `scripted_interview.test.mjs`.

The pattern for each fixture file:
```json
{
  "<persona>-q1": { "response": "...", "confidence": null },
  "<persona>-q2": { "response": "..." },
  "<persona>-qN": { "skip": "human_only" }   // for AI-fit Qs
}
```

- [ ] **Step 1:** Create `tests/fixtures/canned_responses/qa-lead.json` with one entry per `question_id`. Use `parseScript` output to enumerate ids; populate sensible canned answers (the goal is integration-test coverage, not realism).
- [ ] **Step 2:** Create `tests/fixtures/canned_responses/developer.json`.
- [ ] **Step 3:** Create `tests/fixtures/canned_responses/release-manager.json`.
- [ ] **Step 4:** Create `tests/fixtures/canned_responses/product-owner.json`.
- [ ] **Step 5:** In `tests/integration/scripted_interview.test.mjs`, expand the `cases` array:

```javascript
const cases = [
  { scriptFile: "01-qa-engineer-interview.md", fixture: "qa-engineer.json", scriptId: "qa-engineer" },
  { scriptFile: "02-qa-lead-interview.md", fixture: "qa-lead.json", scriptId: "qa-lead" },
  { scriptFile: "03-developer-interview.md", fixture: "developer.json", scriptId: "developer" },
  { scriptFile: "04-release-manager-interview.md", fixture: "release-manager.json", scriptId: "release-manager" },
  { scriptFile: "05-product-owner-interview.md", fixture: "product-owner.json", scriptId: "product-owner" },
];
```

- [ ] **Step 6:** Run all integration tests.

```
node --test tests/integration/
```

Expected: 5 PASS.

- [ ] **Step 7:** Commit.

```
git add tests/fixtures/canned_responses/ tests/integration/scripted_interview.test.mjs
git commit -m "tests: canned-response fixtures and integration runs for all 5 personas"
```

---

### Task 6.5: Real-world playtest *(manual; user runs on their machine)*

**Files:** none.

This task can't be automated — it requires running the agent inside Copilot Chat or Copilot CLI. The user runs it; the implementer's role is to document what to verify.

- [ ] **Step 1:** User runs a live interview against the QA Engineer script: `copilot --agent interviewer --prompt "Start interview"` (or via Copilot Chat).
- [ ] **Step 2:** User walks through end-to-end as the interviewee. Verifies:
  - Resume token surfaced and written to `resume-token.txt`.
  - Confidence probe asked on every numeric answer.
  - At least one short answer triggers refinement; cap respected (≤3 follow-ups).
  - All three skip phrasings produce correct `skip_reason` in `answers.json`.
  - Asking the agent for a recommendation triggers refusal + `flags.md` log.
  - Navigating back to a previous question populates `revised_from`.
  - Finalize → branch `interview/{session_id}` exists on origin.
- [ ] **Step 3:** User saves `transcript.md` to `tests/fixtures/golden_transcripts/qa-engineer-happy-path.md` for regression reference.
- [ ] **Step 4:** Commit the golden transcript.

```
git add tests/fixtures/golden_transcripts/
git commit -m "tests: golden transcript from first real-world playtest (QA Engineer)"
```

---

## Verification (run after Task 6.5)

| Check | How |
|---|---|
| All unit tests pass | `node --test tests/unit/` |
| Integration tests pass for all 5 personas | `node --test tests/integration/` |
| Schema validation passes | included in `tests/unit/schemas.test.mjs` |
| Live playtest completes end-to-end | Task 6.5 |
| Resume works mid-interview | manual: kill process mid-question, run with `--prompt "Resume xxxx-xxxx"` |
| Read-only refusal works | manual: commit responses/{session_id}/, then try to write |
| Bias-mitigation refusal works | manual (Task 6.5 step 2) |

## Self-review checklist (the writer of this plan ran this once)

- ✅ **Spec coverage:** Every section of the design spec maps to at least one task.
  - §3 architecture → Phase 1.1 + distributed
  - §4 storage → Phase 1.2 (schemas), Phase 3 (session-store helpers)
  - §5.1.1 script-loader → Phase 2 (Tasks 2.2–2.4)
  - §5.1.2 session-store → Phase 3
  - §5.1.3 finalize → Phase 5
  - §5.2.* behavioral → Phase 4
  - §6 agent profile → Task 6.1
  - §9 testing → Phase 1.2 + integration in 6.3 + manual in 6.5
  - §10 bootstrapping → distributed
- ✅ **No placeholders:** No "TBD", no "implement later." Each step has the actual content. Two notes:
  - Task 5.4 documents the `tar.gz` choice over `.zip` (spec §12 #5 left this open).
  - Task 6.3's fixture is a starter expanded in 6.4.
- ✅ **Type consistency:**
  - `sessionDir` is a string path everywhere; helpers use `node:path.join` to compose paths.
  - Helper inputs use camelCase (`scriptId`, `sessionDir`, `targetQuestionId`); stored field names stay snake_case (`session_id`, `script_version`).
  - Helper return objects use snake_case for keys that match stored fields (`session_id`, `resume_token`, `session_dir`).
  - Atomic writes use `writeJsonAtomic` everywhere; no direct `writeFileSync` for state files.
  - All tests use `node:test` + `node:assert/strict`; test files end in `.test.mjs`.
- ✅ **Zero npm install** — verified by spot-checking each helper: only `node:` built-ins are imported, plus relative imports of sibling helpers. No `package.json` `dependencies` field.
