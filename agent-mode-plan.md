# Plan: Agent-Driven Interview Mode

**Status:** Plan only — no implementation, no agent prompt, no vendor selection.
**Goal:** Adapt the interview package so an LLM agent (any vendor, any framework) can conduct interviews and store responses to the local filesystem in a structured, machine-readable form. A separate deterministic step compiles the response store into the strategy brief.

---

## Constraint: LLM-agnostic

The package and its specs must not assume a specific LLM, model family, vendor, or agent framework. Any conforming agent must be able to produce response files that match the schema; any conforming compiler must be able to consume them. No vendor-specific serialization, no provider-specific message formats, no SDK-coupled fields.

This constraint applies to:
- Storage format (YAML / JSON only)
- Question metadata (plain frontmatter)
- The new spec docs introduced below
- The compilation step (deterministic transformation, not an LLM call)

---

## 1. Question taxonomy (the core change)

Every question is classified into exactly one category:

- **`required-routing`** — answers that determine which script branch or follow-up the agent uses next. Skipping breaks the interview.
- **`required-context`** — answers needed to make later responses interpretable. Skipping degrades synthesis but doesn't break the interview; agent should re-prompt once and then proceed with degraded context flagged in metadata.
- **`optional`** — interviewee can skip without consequence. Recorded as `status: skipped` and routed to TBD or human follow-up.

**First-pass classification** (refine in implementation):

| Script | required-routing | required-context | All other Qs |
|---|---|---|---|
| QA Engineer | (persona selected up-front in metadata) | Q2 (test surface area) | optional |
| QA Lead | (persona selected up-front in metadata) | Q1 (team structure) | optional |
| Developer | (persona selected up-front in metadata) | Q1 (product area + formal-QA frequency) | optional |
| Release Mgr | (persona selected up-front in metadata) | Q1 (release cadence) | optional |
| Product Owner | (persona selected up-front in metadata) | Q1 (product), Q2 (relationship with QA) | optional |

Persona selection happens before any script loads, so `required-routing` reduces to a single zero-th step. The script's first 1–2 context questions then become `required-context`.

---

## 2. Per-script file changes

Each existing script (`interview/01-…` through `interview/05-…`) gains:

- **Frontmatter block** declaring `persona`, `script_id`, `required_question_ids[]`, `context_question_ids[]`. Everything else is implicitly optional.
- **Per-question ID** (`qa-eng-q4`, `lead-q11`, etc.) — the existing numbered structure already gives us this; formalize the ID scheme.
- **Per-question metadata** stays inline as it is today (the `[3a]` `[3d]` tags) — already machine-readable, no change needed.
- **No content rewrites.** The questions themselves don't change in agent mode.

---

## 3. Overview file changes (`interview/00-interview-guide-overview.md`)

Add three subsections:

- **"Agent-driven mode"** — defines the taxonomy above, the required/optional rule, and the skip-handling contract (agent re-prompts once on `required-context` skip, then proceeds with degraded context flagged in metadata).
- **"Response storage"** — pointer to the storage spec (see §4).
- **"Mode parity"** — which methodology rules apply in both human and agent modes (bias-mitigation, AI-last ordering, tracked-vs-estimated probe), and which are mode-specific (shadowing is human-only; consistent probe enforcement is agent-only).

Existing methodology and synthesis rules don't need rewriting — they apply to both modes.

---

## 4. New file: response storage spec (`interview/06-agent-response-storage.md`)

Covers:

**Directory layout (recommended):**
```
responses/
  {interview_id}/
    session.yaml         # session state for resume support
    metadata.yaml        # persona, date, agent identifier, completion status
    answers.yaml         # structured Q/A records (machine-readable)
    transcript.md        # human-readable transcript with frontmatter
    flags.md             # things to surface for human follow-up
  {interview_id}.zip     # OPTIONAL portable bundle produced at finalize
```

The `responses/` directory lives at repo root (output, not source).

**Interview ID scheme:** `YYYYMMDD-{persona-slug}-{short-hash}` — sortable, human-readable, no PII.

### 4a. Session identity (resume support)

Two-part identity per interviewee:

- **`pseudonym`** — system-generated, of the form `participant-{4-hex}` (e.g. `participant-7c9a`). Avoids collisions; not interviewee-chosen. Persists across sessions for the same person and is used internally for divergence analysis ("Lead-1 said 4hr, IC-3 said 2 days"). Stripped from the compiled brief.
- **`resume_token`** — opaque, interviewee-friendly short string (e.g. `xkj4-9q2m`). Issued at session start, written visibly into the session directory and surfaced to the interviewee. On resume, the interviewee provides the token; the agent looks up the in-progress session.

Pseudonym is generated; resume token is the human-friendly handle. The interviewee never has to remember a chosen name.

### 4b. Session state file (`session.yaml`)

Required artifact in every per-interview directory. Shape:

```yaml
session_id: 20260505-qa-eng-xkj4
pseudonym: participant-7c9a
resume_token: xkj4-9q2m
script_id: qa-engineer
script_version: 0.2.0
agent_identifier: <opaque, e.g. "agent-v1">
started_at: 2026-05-05T14:00:00Z
last_active_at: 2026-05-05T14:32:00Z
status: in_progress | complete | abandoned
next_question_id: qa-eng-q12
required_context_satisfied: true
notes: null
```

This gives the agent everything it needs to resume: which question to ask next, which required-context questions are still outstanding, whether the session is locked to a specific script version.

### 4c. Per-question record shape

One entry per question in `answers.yaml`:
```yaml
- question_id: qa-eng-q7
  tags: [3d]
  script_version: 0.2.0
  prompt_text: "How long did it take from..."
  status: answered | skipped | declined | timeout | pending
  response_text: "..."
  response_confidence: tracked | estimated | inferred | null
  follow_ups:
    - prompt: "Is that tracked or estimated?"
      response: "Estimated"          # null if asked but not yet answered
  skip_reason: null | "interviewee declined" | "not applicable" | ...
  timestamp: 2026-05-05T14:32:00Z
```

The `response_confidence` field feeds the brief's §3d Confidence column directly.

`script_version` on every record so answers cannot be silently mixed across script revisions.

`status: pending` covers questions the agent asked but the interviewee left mid-answer. On resume, pending entries are re-prompted. Same for follow-ups whose `response: null`.

### 4d. Script versioning

Each interview script declares a `script_version` in its frontmatter (semver-ish, e.g. `0.2.0`). On resume, if the current script version is newer than the session's:

- **Recommended (v1):** lock the session to its original script version. Simpler, no half-mixed sessions, no schema drift inside one interview.
- Alternative: surface the diff to the interviewee and let them opt in to the new version. Defer.

Compiler tolerates multiple `script_version` values across sessions; flags any version-aware aggregation in `compilation-warnings.md`.

### 4e. Concurrency

Single-writer rule: a session has one writer at a time. A second instance opening the same session must read-only or refuse. Realistic risk is low (one interviewee, one machine, async) but the spec must state the rule so implementations don't ignore it.

### 4f. Finalize / package step (decouples capture from transport)

When `status: complete` (or interviewee wraps up early), the agent produces a single portable artifact: `responses/{interview_id}.zip` containing the full session directory. Transport then becomes the interviewee's choice:

- `git commit` (if they have it)
- email attachment
- Slack DM
- drop into a shared OneDrive / SharePoint folder
- web upload to a collection point

Decouples capture from transport. The downstream compiler consumes the same file shape regardless of how it arrived. **This affordance lets the deployment surface stay open** — VS Code, CLI, web, or hybrid — without changing the storage spec.

### 4g. LLM-agnostic constraint

At the top of the spec doc:
> _This spec is LLM-agnostic. Any conforming agent — regardless of provider, model, or framework — must be able to produce response files that match this schema._

---

## 5. New file: brief compilation spec (`interview/07-brief-compilation.md`)

Describes the deterministic mapping from response store → brief template. Not the compiler itself — the spec the compiler implements.

- For each brief section tag (`[3a]`, `[3d]`, etc.), aggregate matching responses across all interview IDs.
- For `[3d]`, group by metric, compute Confidence as: any `tracked` → `Tracked`; otherwise cluster `estimated` and tag `Estimated (n=X)`; otherwise `TBD`.
- For qualitative §5 entries, require a citation back to a `[3c]` response — uncited entries dropped (this enforces the falsifiability rule already in the brief template).
- For §6-S (Security & Data Governance), route the Lead's responses; flag empty if Lead skipped.
- Surface a `compilation-warnings.md` listing every skipped `required-context` question, every metric divergence between Lead and IC clusters, and every §5 qualitative entry that lost its citation.

**Compilation must be deterministic and LLM-free.** Same input → same output. This protects the audit trail and keeps a second LLM out of the loop.

---

## 6. Access modes (how interviewees reach the agent)

The agent architecture is uniform across all interviewees — same code, same skills, same response schema. Only **who is at the keyboard** varies. Three modes:

### 6a. Direct mode

Interviewee has the toolchain (clone the repo, or runs a packaged distribution). Agent runs on their machine, writes responses to their local `responses/` directory, finalize step produces a portable bundle they send back.

- **Best signal.** Adaptive probing, conversational refinement, resume — all work natively.
- **Audience:** dev-tier interviewees (likely QA Engineers, Developers, possibly Lead).
- **Implementation cost:** minimal beyond the agent itself.

### 6b. Facilitated mode

Interviewee does not have the toolchain. A dev (analyst or embedded engineer) runs the agent on their behalf during a live session — voice/video call, screen share optional. Interviewee speaks; facilitator transcribes by relaying answers into the agent. Agent's skills (probing, refinement, confidence-tagging) apply normally. Storage is local on the facilitator's machine.

- **Loses async** — interviewee and facilitator must schedule. Resume still works (next session reloads by token).
- **Keeps signal high** — all agent skills apply.
- **Audience:** non-dev interviewees (likely Release Manager, Product Owner, some Leads).
- **Implementation cost:** zero new infrastructure.

### 6c. Async questionnaire fallback

Markdown form per persona, fillable offline, returned as a file. A separate ingestion step parses the filled form into the response schema. **No agent involvement** on the interviewee's side — none of the skills apply.

- **Lowest fidelity.** No probing, no refinement, no confidence tagging. Compiler flags every record as `confidence: estimated` at best, `inferred` for many.
- **Audience:** rare — anyone who can't make a live session and can't run the agent.
- **Implementation cost:** trivial — generated from the same script files.

### 6d. Mode metadata

Each session records its access mode in `metadata.yaml`:

```yaml
access_mode: direct | facilitated | async_questionnaire
facilitator_pseudonym: null | participant-3a8f
```

The compiler uses this when surfacing fidelity warnings. Async questionnaire data is not weighted equally to direct/facilitated data when computing `[3d]` Confidence aggregates.

---

## 7. Agent skills (capability list)

The agent is a code-based agent that lives in this repo, not a low-code platform. Its capabilities are expressed as composable named skills. Each skill has a clear input, output, and contract — independent of LLM provider or agent framework.

### 7a. Session lifecycle skill

Start, persist, resume, finalize. Covers:
- Issuing a new resume token and `participant-{4-hex}` pseudonym at session start.
- Writing `session.yaml` after every state change (next question advanced, follow-up captured, status flipped).
- Resuming from a token: load session state, identify `next_question_id`, re-prompt any `pending` questions or null-response follow-ups.
- Finalize: mark `status: complete`, package the session directory into the portable bundle (§4f).

### 7b. Conversational refinement skill

The reason AI is worth using for this at all. Engages in **bounded multi-turn dialogue** around an individual question to help the interviewee develop a richer answer, then returns to the structured flow once an answer is committed.

Behavior:
- **Either party can start the dialogue.** Interviewee says "let me think about that" or starts answering tangentially → agent engages. Or agent detects a thin/vague answer → agent asks one targeted follow-up.
- **Agent stays scoped to the current question.** No drifting into adjacent topics; if the interviewee raises one, agent notes it for `flags.md` and returns.
- **Bounded.** Soft cap on rounds (e.g., 3–4 turns) per question. If no committed answer surfaces, the agent records what was captured, tags the response `discussion-derived`, and moves on.
- **Bias-aware.** All bias-mitigation rules apply during refinement. Agent does not lead, anchor on AI-shaped answers, or suggest solutions.
- **Storage.** Dialogue turns go into the question's `follow_ups` array. The committed answer goes into `response_text`. The compiler reads `response_text`; the dialogue is preserved for transcript and audit.

This is the spec-driven-dev "discuss-then-return" pattern (similar to what Superpowers / BMAD do for development tasks), narrowed to producing better strategy-brief content.

### 7c. Confidence-tagging skill

After every numeric answer (questions tagged `[3d]`, or any answer containing a number/percentage/duration), prompt:

> "Is that a number you've seen reported on a dashboard or ticket, or is it your own estimate?"

Records `response_confidence: tracked | estimated | inferred | null` per the storage spec. This is the single most important skill for §3d Confidence column accuracy.

### 7d. Skip-handling skill

Distinguish three skip kinds at the language level:
- **"I don't know"** → record `status: skipped`, `skip_reason: "not measured"`. For required-context questions: re-prompt once before proceeding with degraded context.
- **"I don't want to answer"** → record `status: declined`, `skip_reason: "interviewee declined"`. Never re-prompt. Note in `flags.md`.
- **"That doesn't apply"** → record `status: skipped`, `skip_reason: "not applicable"`. No re-prompt.

### 7e. Bias-mitigation skill

Enforce the methodology rules (overview §Methodology Notes) consistently:
- AI-related questions only after target-state questions (script ordering already encodes this; agent must not reorder).
- No leading questions during conversational refinement ("So I imagine X is the problem, right?" — refused).
- No solution-shaped suggestions during refinement ("Have you considered an AI tool for that?" — refused).
- No anchoring with prior interviewees' answers (one session at a time; cross-session synthesis is the compiler's job).

### 7f. Skills out of scope (explicitly)

- **Brainstorming skill** — explicitly not in scope. The conversational refinement skill is bounded; it does not open-ended ideate.
- **Cross-session divergence detection** — happens at compile time, not interview time. The agent never sees other interviewees' answers.
- **Solution proposal** — the agent never recommends QA tooling or approaches. Discovery only.

---

## 8. What does NOT change

- **Brief template** (`qa-ai-automation-strategy-brief-template.md`) — already structured for synthesis. Confidence column, Stop Conditions, Opportunity Cost, §6-S — all mode-agnostic.
- **Question content** — the wording works for both human and agent modes. Any change to question wording bumps `script_version`; in-progress sessions stay locked to their original version per §4d.
- **Tagging convention** — already machine-readable.
- **Bias-mitigation rules** — enforced by the agent (§7e) rather than the human; the rules themselves don't change.
- **Hybrid-mode viability** — the storage layout supports merging agent-collected and human-collected responses for the same interviewee. Adopting agent mode does not preclude a human conducting the AI-fit / governance / political sections.

---

## 9. Open decisions before implementation

1. **Storage format: YAML vs. JSON.** Recommendation: YAML for machine records + sibling markdown transcript. JSON acceptable if downstream tooling prefers it.
2. **Interview ID scheme** — date+persona+hash, UUID, or sequential? Recommendation: date+slug+hash (most ergonomic for human inspection).
3. **`responses/` in version control or gitignored?** Outputs typically gitignored unless used as evidence/audit.
4. **Are AI-fit questions** (IC Q30, Lead Q25, Dev Q19, RM Q17, PO Q16–17) **agent-asked or marked human-only?** Recommendation: mark `human_only: true` and have the compiler flag them as gaps if no human follow-up exists. Addresses AI-asking-about-AI bias.
5. **Consent and retention.** What does the agent tell the interviewee about who sees the stored responses, retention, retraction? Policy question, not a code question — the agent's preamble must answer truthfully.
6. **Real-name collection — yes or no?** The pseudonym scheme (§4a) does not require real names. Decision: collect names with consent (richer follow-up), or never (privacy-first). If collected, decide where the pseudonym→identity map lives and who has access.
7. **Resume token delivery.** How does the interviewee receive the token at session start — on screen only, emailed, written into the session directory the agent surfaces a link to? Affects what happens if the interviewee closes the session without saving the token.
8. **Script-version mismatch on resume.** Recommendation: lock the session to its original script version (§4d). Confirm before implementation.
9. **Supported transport channels at finalize.** Which of {git commit, email, Slack, shared drive, web upload} are supported / documented for the interviewee to send the bundle back? At least one must be available to non-git users.
10. **Interaction surface** — text-only chat, voice, web form? Implementation-time decision; the package supports any.
11. **Conversational refinement round cap** — what's the soft cap before the agent commits a `discussion-derived` answer and moves on? 3 rounds, 4, dynamic? Affects interview length.

---

## 10. Estimated scope of file changes when we implement

- 5 interview script files: add frontmatter, add question IDs (mechanical).
- 1 overview file: ~3 new subsections.
- 2 new docs: `interview/06-agent-response-storage.md`, `interview/07-brief-compilation.md`.
- 0 brief template changes.
- Agent codebase + skill modules — separate scope, not enumerated here.

---

## 11. Out of scope (explicitly)

- Agent code or agent system prompt.
- Vendor / model / framework selection (the in-house build will choose its inference provider at implementation time).
- Low-code agent platforms (Copilot Studio, Power Virtual Agents, etc.) — explicitly evaluated and rejected because they make the §7b conversational refinement and §7a cross-session resume skills materially harder.
- Agent execution environment (CLI / VS Code extension / hosted web / hybrid). The finalize/package step in §4f is designed so this stays open.
- The interaction surface (text / voice / web).
- Authentication beyond the resume token. (No SSO, no accounts. The token is the auth.)
- The compiler implementation (only the spec it must satisfy).
- The peer-reviews folder (ephemeral; not part of the agent or its inputs).
