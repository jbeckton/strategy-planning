# Async Interview Forms — Spec

**Status:** v0.2 (minimal — pure-prompt single skill).
**Date:** 2026-05-06.
**Supersedes:** v0.1 (had two skills + helpers); the prior interview-agent design under `docs/superpowers/specs/`.

## 1. Context

One-shot tool to collect input from ~10 colleagues for the QA AI automation strategy brief. Sponsor (the user) generates one markdown form per persona, sends it to participants, collects filled returns, and feeds the filled forms directly to a compiler agent that drafts the brief.

**No scripts, no helpers, no `npm install`, no agent runtime, no parser.** The single deliverable is one Copilot Agent Skill — a SKILL.md file containing prompt-style instructions that Copilot follows to generate forms.

## 2. Workflow

```
[1] Sponsor invokes interview-form-generate (in Copilot Chat or CLI)
       ↓
forms/qa-engineer.md         (template; one per persona, 5 total)
forms/qa-lead.md
forms/developer.md
forms/release-manager.md
forms/product-owner.md
       ↓
[2] Sponsor emails each form to the right participants
       ↓
[3] Participant fills frontmatter (their name, role, completed_at) + responses
       ↓
[4] Participant returns the file
       ↓
[5] Sponsor saves return as forms/<script_id>-<participant-slug>.md
       ↓
[6] (separately) Sponsor invokes the compiler agent, which reads forms/*.md as
    context and drafts qa-ai-automation-strategy-brief.md
```

## 3. Constraints

- **Do not modify the source `interview/01-..05-*.md` scripts.** They map questions to brief sections via inline tags (`[3a]`, `[3d]`, etc.). Those tags are load-bearing for the compiler agent and must be preserved verbatim from source to form.
- **No frontmatter additions to the source scripts.** The form generator derives `script_id` from the filename and `persona` from the H1 at runtime.
- **Forms preserve question wording, numbering (1..N continuous across sections), section headings, and tags.** Reformatting question text, renumbering, or dropping tags would break the compiler agent's section mapping.

## 4. Form template shape

Each generated form has YAML frontmatter (with placeholders the participant replaces) and a body of grouped questions with response blocks:

```markdown
---
script_id: qa-engineer
persona: QA Engineer (Individual Contributor)
participant_name: <fill in your name>
participant_role: <fill in your role / team>
completed_at: <fill in YYYY-MM-DD when done>
---

# Interview: QA Engineer (Individual Contributor)

## Instructions

- Answer each question in the **Your response:** block under it.
- To skip, leave the response blank or write `(skip)`.
- Concrete examples ("the last test I wrote", "Tuesday's release", "about 4 hours")
  are far more useful than generalities.
- When done: fill the frontmatter at the top, save, and send back.

---

## Warm-up & Context

### Q1. How long have you been on the QA team, and what was your role before?

**Your response:**

> _(write your answer here)_

### Q2. What kind of testing do you primarily own — UI, API, integration, performance, exploratory? `[3b]`

**Your response:**

> _(write your answer here)_

### Q3. On a typical day this past week, roughly what % of your time went to authoring vs. execution vs. verification vs. everything else? `[3d]`

**Your response:**

> _(write your answer here)_

## Test Authoring

### Q4. Walk me through the most recent test or test suite you authored, start to finish. `[3a]`

**Your response:**

> _(write your answer here)_

...
```

## 5. File layout

```
.
├── interview/                                   # existing — unchanged source of truth
├── .github/skills/
│   └── interview-form-generate/SKILL.md         # the only new file
├── forms/
│   └── .gitkeep                                 # output dir; populated by the skill
├── async-forms-spec.md                          # this spec
└── ...                                          # existing files (interview/, agent-mode-plan.md, etc.)
```

That's it. No `helpers/`, no `tests/`, no `package.json`, no `responses/`, no `schemas/`.

## 6. The skill

`.github/skills/interview-form-generate/SKILL.md` contains the full instructions Copilot follows to do the transformation. It covers:

- When to invoke (sponsor asks "generate the QA Engineer form" / "make all five forms" / etc.).
- How to derive `script_id` from the filename.
- How to derive `persona` from the H1.
- How to walk the source body for sections, questions, tags.
- The exact form template to produce.
- What NOT to do (don't modify source, don't drop tags, don't skip questions).

The SKILL.md is the authoritative description of behavior. This spec is just the design rationale.

## 7. Filled-form filename convention

When a participant returns the filled form, the sponsor saves it as:

```
forms/<script_id>-<participant-slug>.md
```

Where `<participant-slug>` is the participant's name lowercased with spaces → hyphens. Example: `forms/qa-engineer-jane-smith.md`. The compiler agent globs `forms/*.md` and reads them as context.

## 8. Out of scope (explicitly)

- **Parser skill.** Not needed — the compiler agent reads filled forms (markdown) as context directly.
- **Helpers / scripts.** Pure-prompt skill is sufficient; the transformation is mechanical text manipulation that Copilot does reliably.
- **The compiler agent itself.** Separate work; will read `forms/*.md` and the brief template, output the filled brief.
- **Sending or collecting forms.** The sponsor handles email/Slack/share manually.
- **Privacy/consent flows.** Internal-org tool, ~10 colleagues; participant identity goes in frontmatter without ceremony.
- **Question metadata changes to source scripts.** They stay exactly as authored.

## 9. Verification

After implementing the SKILL.md, the sponsor:

1. Runs the skill against `interview/01-qa-engineer-interview.md`.
2. Inspects `forms/qa-engineer.md`:
   - Every question from the source is present, in original numbering.
   - Tags appear inline at the end of each question.
   - Section headings preserved (without the `(N min)` suffixes from source).
   - Frontmatter has the three placeholders (`participant_name`, `participant_role`, `completed_at`).
3. Repeats for the other four scripts.
4. Sends the forms out and waits.
5. When a return comes back, drops it into `forms/<script_id>-<slug>.md` and feeds it (with the others) to the compiler agent.

## 10. Implementation effort

One SKILL.md file, ~100 lines of prompt-style instructions and a worked example. Tens of minutes, not hours.
