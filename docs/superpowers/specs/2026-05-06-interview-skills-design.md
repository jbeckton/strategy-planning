# Interview Skills — Design Spec

**Status:** Draft v0.1 — pending implementation plan.
**Date:** 2026-05-06.
**Author:** brainstormed with Claude Code (superpowers).
**Successor doc:** an implementation plan (writing-plans skill).
**Companion docs:** [agent-mode-plan.md](../../../agent-mode-plan.md), [interview/00-interview-guide-overview.md](../../../interview/00-interview-guide-overview.md), [SCRATCH.md](../../../SCRATCH.md).

---

## 1. Context

The QA AI automation discovery effort uses five persona interview scripts (`interview/01-..05-*.md`) feeding a synthesis brief (`qa-ai-automation-strategy-brief-template.md`). To run the interviews efficiently and consistently, an LLM agent will conduct them — capturing structured responses, probing for richer detail when answers are thin, tagging numbers as tracked vs. estimated, handling skips properly, and enforcing the methodology's bias-mitigation rules.

This spec defines the **skills** that compose that agent. The agent itself runs on **GitHub Copilot** — Copilot Chat in VS Code and Copilot CLI. Copilot Agent Skills (announced 2025-12-18, GA in VS Code stable Jan 2026) is the cross-surface skill format and the implementation target.

The agent-mode-plan ([§7](../../../agent-mode-plan.md)) listed five capability-aligned skills; this spec re-decomposes them along the **state-vs-behavior seam** into seven skills, closes the open decisions in [§9](../../../agent-mode-plan.md), and finalizes the on-disk storage contract.

## 2. Scope

**In scope:**
- Seven skills (three data-layer, four behavioral) and one custom agent profile.
- On-disk storage shape: `session.yaml`, `answers.yaml`, `metadata.yaml`, `transcript.md`, `flags.md`, `resume-token.txt`.
- Question-metadata changes to existing `interview/01-..05-*.md` scripts (frontmatter only; question text untouched).
- Two access modes: **direct** (interviewee at the keyboard) and **facilitated** (someone running the agent on their behalf during a live session).
- Helpers in **Python** (assumed present on corporate-image dev machines).

**Out of scope:**
- Async questionnaire skill (separate spec, will be requested next). Shared seam = the storage format defined here.
- Brief compiler — deterministic, LLM-free, separate spec.
- Vendor / inference-provider configuration — Copilot is the runtime; this design doesn't reach into model config.
- Privacy / consent / retention controls. This is an internal agent for ~10 people in the sponsor's org, used for efficiency. Interviewee names are captured directly in `metadata.yaml`; no consent flow, no separate identity file.
- Cross-session divergence detection — happens at compile time.
- Authentication beyond the resume token.

## 3. Architecture

### 3.1 Directory layout

```
.
├── .github/
│   ├── agents/
│   │   └── interviewer.agent.md          # Custom agent profile (entry point)
│   └── skills/
│       ├── interview-script-loader/SKILL.md
│       ├── interview-session-store/SKILL.md
│       ├── interview-finalize/SKILL.md
│       ├── interview-refinement/SKILL.md
│       ├── interview-confidence-tagging/SKILL.md
│       ├── interview-skip-handling/SKILL.md
│       └── interview-bias-mitigation/SKILL.md
├── helpers/
│   ├── session/
│   │   ├── new_session.py
│   │   ├── load_session.py
│   │   ├── advance_cursor.py
│   │   ├── revise_cursor.py
│   │   ├── write_answer.py
│   │   └── check_writability.py
│   ├── script/
│   │   ├── parse_script.py
│   │   └── question_filter.py
│   ├── confidence/
│   │   └── validate_confidence.py
│   ├── skip/
│   │   └── classify_skip.py
│   └── finalize/
│       ├── finalize_session.py
│       ├── git_branch_commit_push.py
│       └── package_bundle.py
├── interview/                            # (existing) persona scripts + overview
├── responses/                            # output dir; populated per session
│   └── {session_id}/
│       ├── session.yaml
│       ├── metadata.yaml
│       ├── answers.yaml
│       ├── transcript.md
│       ├── flags.md
│       ├── resume-token.txt
│       └── identity.yaml                 # optional, only with consent
├── schemas/                              # JSON schemas for validation
│   ├── session.schema.json
│   ├── answers.schema.json
│   ├── metadata.schema.json
│   └── helpers/                          # per-helper output schemas
└── tests/
    ├── unit/
    ├── integration/
    └── fixtures/
```

`.github/skills/` is the documented Copilot location. `.claude/skills/` is also accepted by Copilot Agent Skills, so Claude Code's `skill-creator` can scaffold compatible skills in this repo without modifying the runtime expectation.

### 3.2 Entry point

The interviewee starts the agent by either:

- **Copilot CLI:** `copilot --agent interviewer --prompt "Start interview"` (or `--prompt "Resume xkj4-9q2m"`).
- **Copilot Chat (VS Code):** invoke the `interviewer` agent in chat.

Both surfaces load the same `.github/agents/interviewer.agent.md` profile, which references all seven skills.

### 3.3 Git workflow (per [SCRATCH.md](../../../SCRATCH.md))

- Users clone `main`. `main` accumulates committed sessions over time.
- The agent at session start ensures no responses for the new `session_id` are committed yet (otherwise refuses).
- During an in-progress session, response files live uncommitted in the working tree.
- At finalize, the agent creates `interview/{session_id}` branch, commits the session directory, and pushes.
- **Mutability rule:** uncommitted = mutable; committed = read-only. Enforced by `check_writability.py` (`git ls-files --error-unmatch responses/{session_id}/session.yaml` — exit 0 means committed → refuse).
- No `.gitignore` for `responses/` (would conflict between branches).

## 4. Storage spec

### 4.1 `session.yaml`

```yaml
session_id: 20260506-qa-eng-7c9a
pseudonym: participant-7c9a
resume_token: xkj4-9q2m
script_id: qa-engineer
script_version: 0.2.0
agent_identifier: copilot-interviewer-v1
started_at: 2026-05-06T14:00:00Z
last_active_at: 2026-05-06T14:32:00Z
status: in_progress           # in_progress | complete | abandoned
cursor:
  current_question_id: qa-eng-q12
  visited_question_ids: [qa-eng-q1, ..., qa-eng-q11]
required_context_satisfied: true
notes: null
```

### 4.2 `answers.yaml` (one entry per question)

```yaml
- question_id: qa-eng-q7
  tags: [3d]
  script_version: 0.2.0
  prompt_text: "How long did it take from..."
  status: answered              # answered | skipped | declined | pending | revised
  response_text: "..."
  response_confidence: tracked  # tracked | estimated | inferred | discussion-derived | null
  follow_ups:
    - prompt: "Is that tracked or estimated?"
      response: "Estimated"
  follow_up_count: 1            # explicit ≤3 cap enforcement
  skip_reason: null             # null | not_measured | declined | not_applicable | human_only
  revised_from: null            # populated when navigating back and revising
  timestamp: 2026-05-06T14:32:00Z
```

### 4.3 `metadata.yaml`

```yaml
session_id: 20260506-qa-eng-7c9a
pseudonym: participant-7c9a
interviewee_name: "Jane Smith"  # optional, captured directly when offered
persona: qa-engineer
script_id: qa-engineer
script_version: 0.2.0
agent_identifier: copilot-interviewer-v1
access_mode: direct           # direct | facilitated
facilitator_pseudonym: null   # participant-{4-hex} when access_mode: facilitated
facilitator_name: null        # optional, when access_mode: facilitated
started_at: 2026-05-06T14:00:00Z
completed_at: null
counts:
  total_questions: 32
  answered: 18
  skipped: 4
  declined: 0
  human_only_gaps: 3          # AI-fit questions skipped, await human follow-up
```

### 4.4 ID schemes

| Field | Format | Example |
|---|---|---|
| `session_id` | `YYYYMMDD-{persona-slug}-{4-hex}` | `20260506-qa-eng-7c9a` |
| `pseudonym` | `participant-{4-hex}` (independent random source from session_id) | `participant-7c9a` |
| `resume_token` | two 4-char alphanumeric groups, lowercase, no `0/o/1/l/i` | `xkj4-9q2m` |
| Branch name (finalize) | `interview/{session_id}` | `interview/20260506-qa-eng-7c9a` |

### 4.5 Question-metadata changes to existing scripts

Each `interview/01-..05-*.md` file gains YAML frontmatter:

```yaml
---
script_id: qa-engineer
persona: QA Engineer (Individual Contributor)
script_version: 0.2.0
required_context_question_ids: [qa-eng-q2]
human_only_question_ids: [qa-eng-q30, qa-eng-q31, qa-eng-q32]
---
```

Question IDs are **derived** from the existing numbered structure by `interview-script-loader` (`{script_id}-q{number}`). The visible question text is not modified beyond adding frontmatter, honoring [agent-mode-plan §2](../../../agent-mode-plan.md).

### 4.6 Interviewee name handling

The agent asks for the interviewee's name at session start ("optional — what should I call you?"). If provided, it's stored in `metadata.yaml.interviewee_name`. No separate file, no consent flow. The `pseudonym` (system-generated `participant-{4-hex}`) remains the primary key for cross-session aggregation in compilation; the name is just a convenience for the sponsor when reading transcripts. Same pattern for `facilitator_name` when in facilitated mode.

### 4.7 Closed open decisions (from [agent-mode-plan §9](../../../agent-mode-plan.md))

| # | Decision | Resolution |
|---|---|---|
| 1 | Storage format | YAML for machine records, sibling `transcript.md` |
| 2 | Interview ID scheme | `YYYYMMDD-{persona-slug}-{4-hex}` |
| 3 | `responses/` in version control | Yes, on every branch; no `.gitignore`. Mutability via `check_writability` |
| 4 | AI-fit questions agent-asked or human-only | **Human-only.** Listed in `human_only_question_ids` frontmatter; agent skips them with `skip_reason: human_only` |
| 5 | Consent and retention | Not implemented. Internal-org tool for ~10 people; no consent flow needed. |
| 6 | Real-name collection | Captured directly in `metadata.yaml.interviewee_name` (optional). No separate file. |
| 7 | Resume token delivery | Surfaced on screen at session start AND written to `resume-token.txt` in the session dir |
| 8 | Script-version mismatch on resume | Lock session to original version |
| 9 | Transport channels | `git` (default) and optional `bundle` (`.zip`). Email/Slack/drive remain interviewee-driven and not implemented as agent transports |
| 10 | Interaction surface | Text only (Copilot CLI / Copilot Chat). Voice/web are out of scope for v1 |
| 11 | Conversational refinement cap | **3 follow-ups max** per question (compromise between SCRATCH and plan §7b) |

## 5. Skills

All skills live at `.github/skills/<skill-name>/SKILL.md`. They call helpers in `helpers/`. The data-layer skills are loaded eagerly via the agent profile; the behavioral skills load when their trigger description fires.

### 5.1 Data-layer skills

#### 5.1.1 `interview-script-loader`

Parses a persona script, returns structured frontmatter + ordered question list with derived IDs.

- **Trigger description:** *"Use when the agent needs to load or validate a persona interview script — at session start, on resume to verify script_version, or when computing the next question."*
- **Operations:** `parse(script_id) → {frontmatter, questions[]}`; `filter(script_id, --exclude human_only)`.
- **Helpers:** `helpers/script/parse_script.py`, `helpers/script/question_filter.py`.
- **Contract:** pure parsing, idempotent. Question IDs derived as `{script_id}-q{number}`. Malformed frontmatter or missing `script_version` → exit non-zero with diagnostic JSON; agent aborts session start.

#### 5.1.2 `interview-session-store`

CRUD on `session.yaml` / `answers.yaml` / `metadata.yaml`. Owns cursor state and the writability rule.

- **Trigger description:** *"Loaded eagerly via the agent profile. Use for every state-changing operation: creating a session, advancing/reversing the cursor, recording an answer or follow-up, updating session status."*
- **Operations:**
  - `new_session(script_id, persona, access_mode, interviewee_name?, facilitator_name?)` → returns `{session_id, resume_token, pseudonym}`. Writes initial 3 YAML files + `resume-token.txt`.
  - `load_session(resume_token | session_id)` → returns full session state; runs `check_writability` first.
  - `advance_cursor(session_id)` → moves to next question, skipping `human_only` and already-visited IDs.
  - `revise_cursor(session_id, target_question_id)` → back-nav to a previously-visited question.
  - `write_answer(session_id, question_id, ...)` → upsert in `answers.yaml`; updates `last_active_at`.
  - `mark_revised(session_id, question_id, new_response)` → moves prior answer to `revised_from`, writes new with `status: revised`.
  - `check_writability(session_id)` → refuses if session directory is committed in current `HEAD`.
- **Helpers:** the six files under `helpers/session/`.
- **Contract:**
  - All writes are atomic: write-tempfile + rename.
  - `check_writability` runs before every write.
  - Single-writer rule is documented as a user-facing rule, not enforced via lock file (atomic writes provide sufficient safety).
  - Updates `cursor.visited_question_ids` and `last_active_at` on every successful write.

#### 5.1.3 `interview-finalize`

End-of-session work — status flip, transcript generation, git transport, optional bundle.

- **Trigger description:** *"Use when the interviewee indicates they're done, the cursor reaches the end of the script, or the agent times out a long-idle session and the user confirms wrap-up."*
- **Operations (sequential):**
  1. Validate session is `in_progress` and writable.
  2. Generate `transcript.md` from `answers.yaml`.
  3. Recompute `metadata.yaml` counts.
  4. Flip `session.yaml.status: complete`, set `completed_at`.
  5. **Git transport** (default): create branch `interview/{session_id}`, add session dir, commit, push.
  6. **Optional bundle:** `responses/{session_id}.zip` if requested or git fails.
- **Helpers:** `helpers/finalize/finalize_session.py`, `helpers/finalize/git_branch_commit_push.py`, `helpers/finalize/package_bundle.py`.
- **Contract:**
  - Idempotent: re-running on a complete session returns existing branch URL or bundle path.
  - Git failure (push rejected) → session stays `complete` locally; bundle offered as fallback. Agent surfaces error and asks: retry push, switch to bundle, or stop.
  - Never amends, never force-pushes, never skips hooks.
  - `git status --porcelain` check before branch creation; warns and asks how to handle unrelated dirty files.
  - Refuses if `interview/{session_id}` already exists on origin.

### 5.2 Behavioral skills

These skills are mostly markdown rules. They call `interview-session-store` for persistence; they never write YAML directly.

#### 5.2.1 `interview-refinement`

Bounded ≤3-follow-up dialogue around one question.

- **Trigger description:** *"Use when an answer is short/vague (≤1 sentence, no specifics, no numbers when the tag suggests there should be), when the interviewee says 'let me think about that' or answers tangentially, or when the interviewee explicitly asks to elaborate."*
- **Contract:**
  - Hard cap: ≤3 follow-ups per question. After the 3rd, commit whatever was captured with `response_confidence: discussion-derived` and advance.
  - Either party can start the dialogue; agent proactively asks at most one targeted follow-up when an answer is thin.
  - Stay scoped to the current question. Adjacent topics → note in `flags.md`, return.
  - Follow-up exchanges go into `follow_ups[]`; the committed answer goes into `response_text` (the compiler reads `response_text`).
  - Bias-mitigation rules apply.
- **Helpers:** none. Persists via `interview-session-store.write_answer`.

#### 5.2.2 `interview-confidence-tagging`

Probes for tracked vs. estimated when answers contain numbers.

- **Trigger description:** *"Use when an answer contains a number, percentage, duration, count, ratio, or any quantitative claim — also when the question's tag includes [3d] (Baseline Metrics)."*
- **Contract:**
  - Standard probe: *"Is that a number you've seen reported on a dashboard or ticket, or your own estimate?"*
  - Map to `response_confidence`: `tracked` / `estimated` / `inferred`. If interviewee can't or won't classify, record `null` and add a row to `flags.md`. Never block the session.
  - For `[3d]`-tagged questions, the probe is **attempted** (not mandatory in a session-blocking sense). For other numeric answers, the probe is recommended; agent may defer if pacing is tight.
  - The probe must be a real exchange; do not synthesize a confidence value without asking.
- **Helpers:** `helpers/confidence/validate_confidence.py` (validates the recorded enum value).

#### 5.2.3 `interview-skip-handling`

Distinguishes three skip kinds + recognizes `human_only`.

- **Trigger description:** *"Use when the interviewee says any variant of 'I don't know,' 'I'd rather not answer,' 'that doesn't apply,' 'pass,' 'skip,' or when the next question is in the script's human_only_question_ids."*
- **Contract:**

| Phrase | `status` | `skip_reason` | Re-prompt? |
|---|---|---|---|
| "I don't know" / "not measured" | `skipped` | `not_measured` | Once, only for required-context |
| "I'd rather not answer" | `declined` | `declined` | Never. Note in `flags.md`. |
| "That doesn't apply" / "N/A" | `skipped` | `not_applicable` | No |
| (agent-driven, AI-fit) | `skipped` | `human_only` | Never. Increment `metadata.counts.human_only_gaps`. |

- **Helpers:** `helpers/skip/classify_skip.py` (returns one of `{not_measured, declined, not_applicable}`; the `human_only` case bypasses the classifier).

#### 5.2.4 `interview-bias-mitigation`

Methodology rules, always active.

- **Trigger description:** *"Loaded eagerly via the agent profile. Always active during interview interactions — not invoked per question."*
- **Contract (markdown rules; no helpers):**
  - **AI-fit questions only after target-state questions.** Script ordering encodes this; do not reorder.
  - **No leading questions** during refinement (*"So I imagine X is the problem, right?"* → refused).
  - **No solution-shaped suggestions** (*"Have you considered an AI tool for that?"* → refused).
  - **No anchoring with prior interviewees' answers.** One session at a time.
  - **No solutioning, ever.** The agent never recommends QA tooling, vendors, or approaches.
  - **Refuse advice requests from the interviewee.** When the interviewee asks the agent for recommendations or solutions (*"What tools should we use?"*, *"What would you recommend?"*), agent declines politely (something like *"That's exactly the kind of question your sponsor team should weigh in on — I'm here to capture your perspective, not shape it. I'll flag it for a human follow-up."*), notes the question in `flags.md`, and returns to the script. This is a hard rule, not a soft suggestion.

## 6. Custom agent profile

`.github/agents/interviewer.agent.md`:

```yaml
---
name: interviewer
description: Conducts QA discovery interviews following the persona scripts in interview/. Stateful, resumable, bias-aware.
tools:
  - filesystem  # read interview/, read+write responses/
  - terminal    # run python helpers, run git commands
skills:
  - interview-script-loader
  - interview-session-store
  - interview-finalize
  - interview-refinement
  - interview-confidence-tagging
  - interview-skip-handling
  - interview-bias-mitigation
---
```

The system-prompt body of the agent profile encodes:

- **Boot sequence** — greet, ask new vs. resume, capture access_mode (direct vs. facilitated), ask "what should I call you?" (optional, just for friendlier transcripts), parse script, create or load session.
- **Per-question loop** — read next question; ask it; receive answer; invoke refinement/confidence-tagging/skip-handling as triggered; refuse advice requests per bias-mitigation; persist; advance.
- **Navigation** — recognize "go back to question N" and invoke `revise_cursor` + `mark_revised`.
- **Wrap-up** — show counts summary; ask for any open feedback (→ `flags.md`); invoke `interview-finalize`; surface branch URL.

## 7. End-to-end flow

### 7.1 New session (happy path)

```
[interviewee starts agent]
       ↓
script-loader → reads interview/02-qa-lead-interview.md, returns 27 questions
       ↓
session-store.new_session() → writes responses/{session_id}/{session,metadata,answers}.yaml + resume-token.txt
       ↓
[per-question loop]
  agent asks Q
  ├─ answer is short → refinement (≤3 follow-ups)
  ├─ answer has a number → confidence-tagging probe
  ├─ answer is "skip" → skip-handling classifies + records
  ├─ interviewee asks for advice → bias-mitigation refuses + flags
  └─ session-store.write_answer() persists
       ↓
       session-store.advance_cursor()
       ↓
[end of script reached]
       ↓
finalize.generate_transcript()
finalize.update_metadata_counts()
session-store flips status: complete
finalize.git_branch_commit_push() → interview/{session_id}
       ↓
[branch URL surfaced; agent exits]
```

### 7.2 Resume

```
[interviewee provides resume_token]
       ↓
session-store.load_session(resume_token)
  ├─ check_writability → uncommitted? continue. committed? refuse.
  ├─ verify script_version matches interview/ files → if newer, lock to original
  └─ load cursor.current_question_id
       ↓
[per-question loop resumes from current_question_id]
  any pending or null-response follow-ups are re-prompted
```

## 8. Error handling and edge cases

### 8.1 Failure modes the agent surfaces explicitly

| Failure | Detection | Agent response |
|---|---|---|
| Helper script crashes / non-zero exit | Skill instruction wrapper catches stderr | Surface error; pause session; offer retry. State unchanged (writes are atomic and pre-helper). |
| YAML parse error | `load_session` validation | "I can't parse `session.yaml` for this interview. Share for repair, or start a new session." |
| Git push rejected | finalize helper exit code | Offer retry, bundle fallback, or manual instructions. Session stays `complete` locally. |
| Working tree dirty (unrelated) at finalize | `git status --porcelain` | Warn, list dirty files, ask: stash, separate commit, or abort. Never silently includes unrelated files. |
| Resume token not found | `load_session` lookup | "I couldn't find a session with that token here. Did you clone the right branch?" |
| Read-only session (committed) | `check_writability` | "This session has been finalized and committed. Start a new session to revise." |
| Disk full / permission error | helper exit code | Surface error, halt session. No retry. |

### 8.2 Edge cases that change behavior

- **Stale session resume.** `last_active_at > 14 days` → ask: *"This session is from {date}. Resume, or start fresh?"*
- **Back-nav to a `human_only` question.** Refuse with the same skip-handling rationale; navigation continues to the next visited question.
- **Empty response.** Treated as `status: pending`, not `skipped`. Refinement may engage; explicit "skip" hands off to skip-handling.
- **Mid-interview branch switch.** Detected at the next `advance_cursor` (working-tree state recorded each call). Agent surfaces a warning and asks whether to switch back or finalize on the current branch.
- **Interviewee runs git commands manually.** Agent doesn't prevent it; logs working-tree state at each `advance_cursor` so finalize can detect drift.
- **Multiple sessions for one person.** Each gets its own `session_id`. Pseudonym persists if they reuse it; resume tokens are unique per session.

## 9. Testing

| Layer | Tooling | Coverage |
|---|---|---|
| **Python helpers** | `pytest` with `tmp_path` for filesystem mocking | Each helper is small, pure I/O. Unit-test happy path + each documented failure mode. |
| **Helper output schemas** | `jsonschema` | Every helper that emits JSON has a schema; CI validates against fixtures. |
| **YAML file shapes** | `jsonschema` (against YAML loaded as dicts) | Validate `session.yaml` / `answers.yaml` / `metadata.yaml` against schemas. |
| **End-to-end integration** | `tests/integration/scripted_interview.py` test harness simulating an interviewee feeding canned responses | Happy path, skip, refinement, back-nav, finalize-with-bundle, finalize-with-git (against a local bare repo). |
| **Skills (markdown)** | Manual playtest + golden transcript tests | Validate by running a real interview and comparing `transcript.md` to a hand-checked golden. |

CI runs unit tests + schema validation on every push. Integration tests run nightly.

Dev dependencies: `pytest`, `pyyaml`, `jsonschema`. Runtime dependency: `pyyaml` only.

## 10. Bootstrapping (what gets created when this is implemented)

1. **Directories:** `.github/skills/{seven-skill-dirs}/`, `.github/agents/`, `helpers/{session,script,confidence,skip,finalize}/`, `responses/.gitkeep`, `schemas/`, `tests/{unit,integration,fixtures}/`.
2. **7 SKILL.md files** + 1 `interviewer.agent.md`.
3. **13 Python helpers** (6 session, 2 script, 1 confidence, 1 skip, 3 finalize). Each ~50–150 lines with tests.
4. **JSON schemas:** `session.schema.json`, `answers.schema.json`, `metadata.schema.json`, plus per-helper output schemas.
5. **Frontmatter added** to existing `interview/01-..05-*.md` files.
6. **`.github/skills/README.md`** — short orientation: skill list, how to invoke via `copilot --agent interviewer`, where to look for issues.
7. **`requirements.txt`** with `pyyaml` (only runtime dep).
8. **First playtest:** a developer runs the QA Engineer script as the interviewee, end-to-end, validates `transcript.md`.

## 11. Verification

End-to-end checks before declaring v1 complete:

- **Smoke test on each persona script.** Run a scripted-interviewee integration test through each of the five `interview/` scripts. Verify `answers.yaml` is well-formed, all required-context questions are recorded, all `human_only` IDs are skipped with `skip_reason: human_only`, all `[3d]` numeric answers have a `response_confidence` value or a `flags.md` row.
- **Resume test.** Start a session, kill the agent mid-question, resume from the token, complete the session. Assert `cursor.current_question_id` resumes correctly and any `pending` follow-ups are re-prompted.
- **Read-only refusal test.** Commit a session, then try to write to it. Assert `check_writability` refuses and the agent surfaces the correct message.
- **Back-nav test.** Navigate back to an earlier question, revise, finalize. Assert `revised_from` populated and `status: revised`.
- **Bias-mitigation refusal test.** As the interviewee, ask the agent *"What tools do you recommend?"*. Assert agent refuses, logs to `flags.md`, returns to the script.
- **Finalize-with-git test.** Against a local bare repo, finalize a complete session. Assert branch `interview/{session_id}` exists on origin with the expected commit.
- **Finalize-with-bundle fallback test.** Force git push to fail (no remote configured); assert a `.zip` bundle is produced and the agent surfaces it.

## 12. Open questions for implementation

These are intentionally deferred — they don't block this design but will need decisions during the writing-plans phase:

1. **`copilot --agent` flag exists in CLI; what's the equivalent invocation in Copilot Chat (VS Code)?** The agent profile location is documented; the user-facing trigger phrase needs to be confirmed against current Copilot Chat behavior.
2. **Conversational refinement trigger threshold.** "Short/vague" is currently informal. Implementation may want an explicit length-or-content heuristic (e.g., < N tokens, no concrete noun, etc.).
3. **Stale-session window.** Currently 14 days. Tunable.
4. **Test interviewee fixtures.** What canned responses should the integration tests use? Probably one set per persona script, hand-authored as fixtures.
