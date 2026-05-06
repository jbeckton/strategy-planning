# QA AI Automation — Discovery Inputs

Interview scripts, response forms, and strategy brief template for a QA AI automation discovery effort. A Copilot Agent Skill generates fillable markdown forms from the scripts; participants return their filled forms; a future compiler agent drafts the brief from the returns.

## Generating forms (sponsor)

The [`interview-form-generate`](.github/skills/interview-form-generate/SKILL.md) skill turns a persona script into a fillable markdown form. Copilot loads the skill automatically because it lives in `.github/skills/`.

**In VS Code with Copilot Chat:** open this repo, open Copilot Chat, and ask:

> Use the interview-form-generate skill to make the QA Engineer form.

Or, all at once:

> Generate forms for all five personas.

**In Copilot CLI** (from the repo root):

```
copilot --prompt "Generate the QA Engineer form."
```

Output lands in `forms/<script_id>.md` (e.g. `forms/qa-engineer.md`). Eyeball each generated form against its source script:

- Every numbered question is present, with the same number.
- Every inline tag (`[3a]`, `[3d]`, etc.) is preserved.
- No interviewer-guidance quote blocks (`> Spend the most time here...`) remain.
- Section headings have no `(N min)` suffixes.

Send each form to the relevant participants by whatever channel works (email, Slack, shared drive).

## Filling out a form (participant)

1. Open the form you received (e.g. `forms/qa-engineer.md`).
2. Fill in the frontmatter at the top — your name, role/team, and the date you finish.
3. Under each question, replace the `> _(write your answer here)_` placeholder with your response. To skip a question, leave the placeholder as-is or write `(skip)`.
4. Save the file with your name appended: `forms/<script_id>-<your-name>.md` — e.g. `forms/qa-engineer-jane-smith.md`.
5. Send the file back to the sponsor.

## Drafting the brief (later)

A separate compiler agent — not yet built — will read all filled `forms/*.md` and the [strategy brief template](qa-ai-automation-strategy-brief-template.md) to produce the filled brief. The compiler uses each question's inline section tag (`[3a]`, `[3d]`, etc.) to route answers to the right section of the brief.

## Layout

| Path | What it's for |
|---|---|
| [interview/](interview/) | Five persona scripts + methodology overview. Do not edit — the skill reads them as source of truth. |
| [qa-ai-automation-strategy-brief-template.md](qa-ai-automation-strategy-brief-template.md) | Synthesis target the compiler agent will fill in. |
| [.github/skills/interview-form-generate/SKILL.md](.github/skills/interview-form-generate/SKILL.md) | The form-generation skill (pure-prompt; no scripts, no `npm install`). |
| [forms/](forms/) | Generated form templates and filled returns. |
| [async-forms-spec.md](async-forms-spec.md) | Design rationale for the skill. |
| [CLAUDE.md](CLAUDE.md) | Conventions for AI editors working in this repo. |

## Conventions

- **Don't modify `interview/*.md`** — the form generator reads them as source of truth.
- **Preserve inline tags verbatim** (`[3a]`, `[3d]`, etc.) — they drive the compiler's section mapping.
- **Solution-agnostic framing** — the brief is a decision document, not a sales pitch. Don't add vendor / build-vs-buy / budget questions to scripts.

See [CLAUDE.md](CLAUDE.md) for the fuller conventions guide.
