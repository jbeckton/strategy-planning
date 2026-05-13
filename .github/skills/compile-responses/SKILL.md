---
name: compile-responses
description: Compiles filled participant interview forms from responses/ into draft content for each section of the strategy brief. Writes compiled-brief-sections.md at the repo root. Invoke explicitly — do not auto-trigger.
---

# compile-responses

Aggregates filled participant interview forms into draft content for each section of the strategy brief. Outputs a single `compiled-brief-sections.md` at the repo root that the author then transfers section-by-section into `qa-ai-automation-strategy-brief-template.md`.

## How to invoke

Invoke this skill explicitly:

```
@copilot /compile-responses
```

Do not auto-trigger this skill based on context. It runs only when the user explicitly calls it.

## What to do

### 1. Discover filled forms

List all files in `responses/`. Every file there is a filled participant return — read each one completely. If `responses/` is empty or does not exist, stop and tell the user: "No filled forms found in `responses/`. Add filled forms there and re-invoke."

Also read `qa-ai-automation-strategy-brief-template.md` to understand each section's expected format (prose, table, or bullet list).

### 2. Parse each form

For each filled form:

- Note the **persona** from the `script_id` frontmatter field (e.g. `qa-engineer`, `qa-lead`, `developer`, `release-manager`, `product-owner`).
- **Do not record or use the `participant_name` field anywhere in the output.** All compiled content is anonymized — attribute only to the persona role.
- For each question in the form, extract:
  - The section **tag(s)** embedded in backticks in the question heading — e.g. `` `[3c]` ``, `` `[6-R]` ``. A single question may carry multiple tags.
  - The full answer text from the **Your response:** block. Skip unanswered questions (answer is blank, `(skip)`, or the unchanged placeholder `_(write your answer here)_`).
  - For questions with a **Source of any number you give:** block, extract the source label: `Tracked`, `Estimated`, or `Not measured`.

### 3. Build a tag → answers map

Collect all extracted answers into a working map keyed by tag. A question with two tags contributes to both. Multiple respondents' answers for the same tag accumulate in a list tagged with their persona.

Tag reference:

| Tag | Brief section |
|-----|--------------|
| `[1]` | §1 Executive Summary |
| `[3a]` | §3a Process Journey |
| `[3b]` | §3b Personas Involved |
| `[3c]` | §3c Pain Points |
| `[3d]` | §3d Baseline Metrics |
| `[4a]` | §4a Target State Description |
| `[5]` | §5 Expected Value |
| `[6-A]` | §6 Assumptions |
| `[6-R]` | §6 Risks |
| `[6-D]` | §6 Dependencies |
| `[6-S]` | §6 Security & Data Governance |
| `[7]` | §7 Proposed Approach |
| `[8]` | §8 The Ask |

### 4. Apply synthesis rules

Apply these rules while drafting each section:

**Anonymization.** Never name a participant. Attribute observations to their persona role only (e.g. "QA engineers reported…", "The release manager described…"). When multiple respondents from the same persona agree, write "QA engineers (n=X) reported…".

**Confidence labeling — required for all numeric values.**
- Source = `Tracked`: use the value directly; append `[Tracked — <source cited by respondent>]`.
- Source = `Estimated` with multiple consistent respondents: write the range or median and append `[Estimated, n=X]`.
- Source = `Not measured`, or only one respondent gave a figure, or no numeric answer: write `TBD — needs instrumentation`.
- Never invent a number. Never promote an `Estimated` value to `Tracked`.

**Dissent and divergence.** When personas disagree on a fact (e.g. one persona says verification takes 4 hours; another says 30 minutes), surface both with persona labels and confidence in a **Note:** line under the relevant row. Do not average conflicting figures. Flag for author follow-up.

**Pain point clustering (§3c).** Group similar pain points from across all personas under a descriptive theme label. Synthesize into one representative description per cluster — do not list every respondent's quote verbatim. Note affected persona(s) and any quantified impact.

**Symmetric risks (§6-R).** Aim for roughly half the risk rows to describe failure modes of the *proposed change* (e.g. hallucinated tests, false confidence from automation, governance overhead, opportunity cost). Phrase failure-mode risks in neutral "new tooling" / "automated verification" language — do not name specific vendors or AI systems.

**§4b is off-limits.** Do not generate or infer AI Integration Points content. Leave §4b entirely to the author. Do not mention it in the output except in the author-input section at the end.

**§6-S sourcing.** Security & Data Governance content must come exclusively from the QA Lead form. If no QA Lead form is present in `responses/` or the respondent left §6-S questions blank, write: `[Source: QA Lead interview — not completed or not returned. Flag for follow-up.]`

### 5. Write compiled-brief-sections.md

Write `compiled-brief-sections.md` at the repo root. Structure it as follows — one section per tag, in brief order.

For each section, write:
1. A `##` heading naming the section and its tag.
2. Synthesized content in the format the brief template expects (mirror the template's structure: prose, table rows, or bullet list as appropriate).
3. A **Gaps & flags** line listing: any tags with zero responses, any numeric fields that remain TBD, any dissent flagged for author follow-up.

---

## §1 — Executive Summary `[1]`

_2–4 bullet points capturing the business problem as articulated by respondents. Solution-agnostic. No vendor names._

**Gaps & flags:** …

---

## §3a — Process Journey `[3a]`

_Narrative description of the end-to-end QA flow as described across personas. Where respondents named steps, owners, or durations, render as a table:_

| Step | Owner (persona) | Avg. Duration | Confidence | Notes |
|------|----------------|--------------|------------|-------|

**Gaps & flags:** …

---

## §3b — Personas Involved `[3b]`

| Persona | Role in Process | Primary Pain |
|---------|----------------|-------------|

**Gaps & flags:** …

---

## §3c — Pain Points `[3c]`

| Pain Point Theme | Affected Personas | Quantified Impact | Confidence | Frequency |
|-----------------|------------------|------------------|------------|-----------|

**Gaps & flags:** …

---

## §3d — Baseline Metrics `[3d]`

| Metric | Value | Confidence | Source | Notes |
|--------|-------|------------|--------|-------|

_Apply Tracked / Estimated (n=X) / TBD on every row._

**Gaps & flags:** …

---

## §4a — Target State Description `[4a]`

_Prose. How do respondents describe an improved future state? What would "good" look like? Synthesize across personas without solutioning or naming AI._

**Gaps & flags:** …

---

## §5 — Expected Value `[5]`

**Quantitative**

| Outcome | Baseline ref | Target | Confidence |
|---------|-------------|--------|------------|

**Qualitative**

| Outcome | Evidence source | Why it matters |
|---------|----------------|----------------|

_Every row must trace to a §3c pain or §3d metric. Drop unsupported entries._

**Gaps & flags:** …

---

## §6-A — Assumptions `[6-A]`

_Bullet list of what must be true for the approach to work, as implied or stated by respondents._

**Gaps & flags:** …

---

## §6-R — Risks `[6-R]`

| Risk | Category | Likelihood | Impact | Mitigation |
|------|----------|------------|--------|------------|

_~50% of rows should be failure modes of the proposed change._

**Gaps & flags:** …

---

## §6-D — Dependencies `[6-D]`

| Dependency | Owner (persona role) | Required By |
|------------|---------------------|------------|

**Gaps & flags:** …

---

## §6-S — Security & Data Governance `[6-S]`

_Sourced exclusively from the QA Lead form. Prose and any table rows mentioned by that respondent. If not available, write the flag message._

**Gaps & flags:** …

---

## §7 — Proposed Approach `[7]`

_Phase table if respondents described phasing or timing preferences. Otherwise, bullet points capturing constraints, appetite, and sequencing preferences expressed across personas._

**Gaps & flags:** …

---

## §8 — The Ask `[8]`

_What do respondents say is needed? What approvals, headcount, or commitments were surfaced?_

**Gaps & flags:** …

---

## Sections requiring author input (not interview-sourced)

- **§2 Problem Statement** — author synthesizes from §3c/§3d content above into one solution-agnostic paragraph.
- **§4b AI Integration Points** — author/architect from external AI tooling assessment. Not generated here.
- **§4c Updated Process Journey** — author annotates §3a after solution design is complete.
- **Appendices** — author discretion.

### 6. Report completion

Tell the user: "Compiled `compiled-brief-sections.md` from X forms across Y personas. See **Gaps & flags** under each section for missing data and items needing author follow-up."

## What this skill does NOT do

- Modify `qa-ai-automation-strategy-brief-template.md` — the author transfers content manually.
- Modify any file in `responses/`.
- Generate §4b AI Integration Points content — that section is filled by the author/architect from external AI tooling assessment, not from interview synthesis.
- Name or identify any participant — all output is attributed to persona role only.
- Promote estimated numbers to tracked status.
- Average conflicting figures from different respondents — divergence is surfaced and flagged.
