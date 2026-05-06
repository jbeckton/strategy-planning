# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository nature

Documentation-and-skill planning repo for a QA AI automation strategy discovery effort. The repo holds the interview scripts, the strategy brief template, and one Copilot Agent Skill that generates fillable forms from those scripts. **There is no application code, no build, no test runner, no package manager.** Do not propose a build/lint/test command.

The work product is a synthesized strategy brief. Workflow: the sponsor invokes [interview-form-generate](.github/skills/interview-form-generate/SKILL.md) to produce a fillable markdown form per persona; sends each form to participants; collects filled returns into [forms/](forms/); a separate (future) compiler agent reads the filled forms and drafts the brief from the template.

## Layout

- [interview/](interview/) — five persona scripts ([01-qa-engineer](interview/01-qa-engineer-interview.md), [02-qa-lead](interview/02-qa-lead-interview.md), [03-developer](interview/03-developer-interview.md), [04-release-manager](interview/04-release-manager-interview.md), [05-product-owner](interview/05-product-owner-interview.md)) plus [00-interview-guide-overview.md](interview/00-interview-guide-overview.md) which defines methodology, sequence, and the question-tagging convention. **Do not modify these files** — the form generator reads them as source of truth.
- [qa-ai-automation-strategy-brief-template.md](qa-ai-automation-strategy-brief-template.md) — synthesis target. Filled-form responses aggregate into it by section tag.
- [.github/skills/interview-form-generate/SKILL.md](.github/skills/interview-form-generate/SKILL.md) — pure-prompt Copilot Agent Skill. Reads a persona script, writes a fillable form to [forms/](forms/). No helper scripts, no `npm`/`pip` install.
- [async-forms-spec.md](async-forms-spec.md) — design rationale for the skill.
- [forms/](forms/) — output dir. Templates: `forms/<script_id>.md`. Filled returns: `forms/<script_id>-<participant-slug>.md`.
- [peer-reviews/](peer-reviews/) — ephemeral working folder; not part of the package.
- [SCRATCH.md](SCRATCH.md) — working notes; not authoritative.

## Conventions that matter when editing

Drawn from [interview/00-interview-guide-overview.md](interview/00-interview-guide-overview.md) and the brief template:

- **Section tags on questions** — every interview question is tagged with the brief section it feeds: `[1]`, `[3a]`, `[3b]`, `[3c]`, `[3d]`, `[4a]`, `[4b]`, `[5]`, `[6-A]`, `[6-R]`, `[6-D]`, `[6-S]`, `[7]`, `[8]`. Preserve tags verbatim on any edit; they drive both the form output and the future compiler agent. Untagged questions are warm-ups.
- **Confidence taxonomy** — every number in the brief carries `Tracked` / `Estimated (n=X)` / `TBD — needs instrumentation`. Never invent a number; never promote an estimate to "tracked."
- **Solution-agnostic framing** — the brief and scripts must not name vendors, tools, or specific AI capabilities. The brief is a decision document, not a sales pitch.
- **AI questions go last** — script ordering encodes a bias-mitigation rule (target-state before AI-fit). Do not reorder, and do not insert AI-shaped probes earlier in any script.
- **No leading questions, no solutioning during discovery** — applies in the script wording.
- **Symmetric risks** — roughly half of `[6-R]` should describe failure modes of the proposed change, not only current-state pain.
- **`[6-S]` Security & Data Governance** is sourced from the QA Lead script; flag as empty if the Lead skipped it.

## Out of scope

- Modifying the source `interview/*.md` scripts (no frontmatter additions, no renumbering, no tag edits). The form generator reads them; it does not modify them.
- Adding helpers / scripts / npm install to support the skill. The skill is pure-prompt by design — Copilot does the markdown transformation directly.
- A parser skill that converts filled forms back to JSON. Not needed; the future compiler agent reads filled markdown forms as context directly.
- Adding vendor, build-vs-buy, or budget-tradeoff questions to any script. These were deliberately removed.
- Treating [peer-reviews/](peer-reviews/) as input or output of the package.
- Recommending a low-code agent platform (Copilot Studio, Power Virtual Agents, Microsoft 365 Agent Builder) — evaluated and rejected.
