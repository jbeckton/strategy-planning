---
name: interview-form-generate
description: Use when the user asks to generate a markdown interview form from a persona script under interview/ for participants to fill in offline. Reads interview/<file>.md and produces forms/<script_id>.md with all questions and a "Your response:" block under each. Does not modify the source script.
---

# interview-form-generate

Generates a fillable markdown form from a persona interview script. Preserves question wording, numbering, section headings, and inline tag annotations (`[3a]`, `[3d]`, etc.) — the compiler agent that drafts the strategy brief uses those tags to map answers to brief sections.

## When to use

The user asks something like:

- "Generate the QA Engineer form."
- "Make the form from `interview/02-qa-lead-interview.md`."
- "Create all five forms."

If the user names a persona without specifying a path, find the matching script under `interview/` (the filename pattern is `NN-<persona-slug>-interview.md`).

## What to do

For each requested persona script, perform these five steps in order.

### 1. Read the source

Read `interview/<file>.md`. Do not modify it.

### 2. Derive metadata

- **`script_id`** — strip the leading `NN-` and the trailing `-interview.md` from the filename.
  - `01-qa-engineer-interview.md` → `qa-engineer`
  - `02-qa-lead-interview.md` → `qa-lead`
  - `05-product-owner-interview.md` → `product-owner`
- **`persona`** — extract from the first H1 line, which has the form `# Interview Script — <Persona>`. Take the part after the em-dash, trimmed.
  - `# Interview Script — QA Engineer (Individual Contributor)` → `QA Engineer (Individual Contributor)`

### 3. Walk the source body

Things you'll encounter in the source:

- **Section headings** look like `## 1. Warm-up & Context (5 min)`. For the form, strip the leading `N. ` and the trailing `(N min)` to get `## Warm-up & Context`.
- **Numbered questions** look like:
  - `1. How long have you been on the QA team, and what was your role before?`
  - `2. What kind of testing do you primarily own — UI, API, integration, performance, exploratory? `[3b]``
  - `6. What tools and frameworks did you use? Where did you hit friction? `[3a] [3c]``

  Question numbers continue across sections (1..N over the whole file). Tags can be in one or more backticked groups, each containing one or more `[...]` markers. Preserve the tags **verbatim** at the end of the question text.
- **Quote blocks** like `> Spend the most time here. This is the section most likely to dominate the brief.` are interviewer guidance for the human-led version. **Skip them** in the form output.
- **Persona-level metadata block** at the top (lines starting with `**Persona:**`, `**Duration:**`, `**Brief sections informed:**`). Skip these.
- **Horizontal rules** (`---`) between sections in the source — omit from the form.

### 4. Write the form

Create `forms/` if it doesn't exist. Write to `forms/<script_id>.md` using this exact template:

````markdown
---
script_id: <script_id>
persona: <persona>
participant_name: <fill in your name>
participant_role: <fill in your role / team>
completed_at: <fill in YYYY-MM-DD when done>
---

# Interview: <persona>

## Instructions

- Answer each question in the **Your response:** block under it.
- To skip a question, leave the response blank or write `(skip)`.
- Concrete examples ("the last test I wrote", "Tuesday's release", "about 4 hours") are far more useful than generalities.
- When you're done: fill in the frontmatter at the top, save the file, and send it back.

---

## <section heading 1>

### Q1. <question text> `[tag1]` `[tag2]`

**Your response:**

> _(write your answer here)_

### Q2. <question text>

**Your response:**

> _(write your answer here)_

## <section heading 2>

### Q5. <question text> `[tag]`

**Your response:**

> _(write your answer here)_
````

Notes on the template:

- The `### Q<n>.` heading uses the source question's original number.
- Tags appear after the question text, formatted exactly as in the source (each `[...]` in its own backticked group, separated by spaces).
- The "Your response:" block is exactly two lines: `**Your response:**`, blank line, `> _(write your answer here)_`.

### 5. Verify

Before reporting done, scan the generated form against the source:

- Every numbered question from the source is present in the form, with the same number.
- Every tag from the source is present in the form (none dropped, none added).
- No interviewer-guidance quote blocks appear in the form.
- Section headings appear without the `(N min)` time markers.
- The persona-level metadata block from the source top is not in the form.

If anything is off, regenerate.

## Filename convention for filled forms

When the participant returns the filled form, save it as `forms/<script_id>-<participant-slug>.md`. The `<participant-slug>` is the participant's name lowercased with spaces and punctuation → hyphens.

- `Jane Smith` → `forms/qa-engineer-jane-smith.md`
- `Pat O'Brien` → `forms/qa-engineer-pat-obrien.md`

The compiler agent reads `forms/*.md` (excluding the bare-template files like `forms/qa-engineer.md`) to draft the strategy brief.

## What this skill does NOT do

- Modify the source `interview/*.md` files.
- Send forms anywhere — the sponsor emails or shares them manually.
- Parse filled forms back to JSON or any structured form — not needed; the compiler agent reads filled markdown directly.
- Generate forms for personas without a corresponding `interview/*.md` script.
- Add machine-readable question IDs (e.g., `qa-engineer-q1`) to the form — derivable by the compiler from `script_id` + question number; cluttering the form is unnecessary.

## Worked example

Source `interview/01-qa-engineer-interview.md` (excerpt):

```markdown
# Interview Script — QA Engineer (Individual Contributor)

**Persona:** QA Engineer authoring/executing tests day-to-day
**Duration:** 45–60 minutes
**Brief sections informed:** 3a, 3b, 3c, 3d, 4a, 4b (final block only), 6-R

---

## 1. Warm-up & Context (5 min)

1. How long have you been on the QA team, and what was your role before?
2. What kind of testing do you primarily own — UI, API, integration, performance, exploratory? `[3b]`
3. On a typical day this past week, roughly what % of your time went to authoring vs. execution vs. verification vs. everything else? `[3d]`

---

## 2. Test Authoring (10 min)

4. Walk me through the most recent test or test suite you authored, start to finish. `[3a]`
5. Where did the requirements or acceptance criteria come from? How clear were they? `[3c]`
```

Skill produces `forms/qa-engineer.md`:

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
- To skip a question, leave the response blank or write `(skip)`.
- Concrete examples ("the last test I wrote", "Tuesday's release", "about 4 hours") are far more useful than generalities.
- When you're done: fill in the frontmatter at the top, save the file, and send it back.

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

### Q5. Where did the requirements or acceptance criteria come from? How clear were they? `[3c]`

**Your response:**

> _(write your answer here)_
```
