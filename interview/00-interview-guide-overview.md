# QA AI Automation — Interview Guide Overview

Companion to `qa-ai-automation-strategy-brief-template.md`. Each script in this set produces inputs for specific sections of the brief.

---

## Personas to Interview

| #   | Persona           | Recommended Count | Duration  | Priority                                         |
| --- | ----------------- | ----------------- | --------- | ------------------------------------------------ |
| 1   | QA Engineer (IC)  | 3–5               | 45–60 min | **Critical** — primary source for current state  |
| 2   | QA Lead / Manager | 1–2               | 60 min    | **Critical** — capacity, metrics, aggregate view |
| 3   | Developer         | 2–3               | 30–45 min | High — upstream consumer of QA output            |
| 4   | Release Manager   | 1                 | 30 min    | Medium — downstream impact, release cadence      |
| 5   | Product Owner     | 1–2               | 30 min    | Medium — business impact, escape consequences    |

Aim for breadth on QA Engineer interviews — different test surface areas (UI, API, integration, performance) will surface different pain.

---

## Recommended Interview Sequence

1. **QA Lead first** — establishes scope, team structure, what metrics already exist, and which ICs to prioritize. **Treat this session as scoping, not interpretation.** Capture facts, structure, candidate interviewees, security/governance constraints. Defer "what's the real bottleneck" and "where does AI fit" to the follow-up after IC interviews — otherwise the rest of discovery anchors on management narrative.
2. **QA Engineers next** — deepest current-state detail. Run these before forming hypotheses.
3. **Developers, Release Manager, Product Owner** — can run in parallel after QA interviews; their input is calibration, not foundation.
4. **QA Lead follow-up** (recommended, 30 min) — review aggregated findings, validate baseline numbers, pressure-test target state and AI fit. This is where interpretation happens.

---

## Methodology Notes

**Do:**
- Ask for concrete recent examples. "Walk me through the last test you authored" beats "How do you author tests?"
- Get numbers: time, frequency, percentages. Even rough estimates anchor synthesis.
- **Always tag every number** as `tracked` (instrumented data they cited), `estimated` (their personal recall/gut), or `inferred` (you computed it from other answers). The brief's §3d Confidence column depends on this distinction. A standard probe: *"Is that a number you've seen reported, or an estimate?"*
- Probe with "and then what happens?" to surface hidden steps.
- Distinguish *typical* from *worst case*; both matter for the brief.

**Avoid:**
- Leading with AI. Current-state discovery must be unbiased. AI questions come at the end.
- Solutioning during the interview. Note ideas; don't validate them.
- Yes/no questions during discovery. Use open-ended prompts.
- Anchoring with your own assumptions ("So I imagine verification is the big problem, right?").

---

## Logistics

- **Recording:** Record with consent. Transcripts make synthesis dramatically faster.
- **Consent framing:** "This is for a planning exercise. Findings are aggregated; nothing is attributed to individuals in the final brief."
- **Note-taking:** Capture verbatim quotes for pain points — these become artifact text in the brief and during leadership Q&A.
- **Pre-read:** Send the interviewee a 2–3 sentence purpose statement 24h ahead. Do not send the full questions — pre-rehearsed answers lose signal.

---

## Question Tagging Convention

Each question in the scripts is tagged with the brief section it feeds:

- `[1]` Executive Summary / leadership framing
- `[3a]` Process Journey
- `[3b]` Personas
- `[3c]` Pain Points
- `[3d]` Baseline Metrics
- `[4a]` Target State
- `[4b]` AI Integration Points
- `[5]` Expected Value (quantitative or qualitative)
- `[6-A]` Assumptions
- `[6-R]` Risks (including proposed-change failure modes, not just current-state pain)
- `[6-D]` Dependencies
- `[6-S]` Security & Data Governance constraints
- `[7]` Proposed Approach / phasing / build-vs-buy signal
- `[8]` The Ask (sponsor / decision-maker context)

Untagged questions are warm-ups or context-builders.

---

## Synthesis Approach

After interviews complete:

1. **Aggregate by brief section, not by interviewee.** Pull every `[3c]` response from every interview into one document. Cluster.
2. **Quantify where possible — but label every number.** If three of five QA engineers say verification takes ~2 days, that becomes a §3d row with **Confidence = Estimated (n=3)** and the cluster range/median in Notes. Tracked numbers (cited from a dashboard, ticket, or report) become **Confidence = Tracked**. Anything that's neither tracked nor reliably clustered stays **TBD — needs instrumentation**. Do not invent a number. Do not promote an estimate to "tracked" because it's the only number you have.
3. **Reconcile divergence in the Lead follow-up.** When ICs and the Lead disagree on the same metric (e.g. ICs say verification is 2 days, Lead says 4 hours), do not average — surface both numbers in the §3d Notes column with the Confidence column flagged accordingly, then use the optional Lead follow-up session to investigate the gap. A wide gap is itself a finding (instrumentation problem, perception gap, or scope mismatch).
4. **Flag dissent.** When personas disagree on the same pain (e.g. devs say "QA is slow," QA says "specs are unclear"), surface this in the brief — leadership will ask.
5. **Distinguish reported from observed.** If you can shadow a QA engineer for half a day post-interview, do it. Self-reported time estimates skew low for routine tasks and high for painful ones.
6. **Synthesize §6 Risks symmetrically.** Half the risks should describe failure modes of the *proposed change* (false confidence, hallucinated tests, governance overhead, vendor lock-in, opportunity cost), not just adoption friction. The interview scripts include explicit prompts for this — do not let current-state pain crowd them out.