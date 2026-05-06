# Interview-Script Coverage Audit

**Date:** 2026-05-06
**Scope:** Five persona scripts in [interview/](interview/) audited against [qa-ai-automation-strategy-brief-template.md](qa-ai-automation-strategy-brief-template.md), cross-referenced with [interview/00-interview-guide-overview.md](interview/00-interview-guide-overview.md) methodology and [CLAUDE.md](CLAUDE.md) repo conventions.

> **2026-05-06 update — scope shift after audit:** The audit was performed against the original scripts. After review, the project owner removed all AI-fit / AI-capability questions from the discovery instrument (participants have varying AI knowledge, so their answers are noise rather than signal). The brief's §4b AI Integration Points is now filled by the author/architect from external capability assessment, not by interview synthesis. Question numbers below reference the **pre-edit** scripts; renumbering after deletion is documented in the script files themselves. The audit's #1 critical gap (§4b journey-step probes missing) is now **by design** rather than a gap; see §3.1 below for the revised finding. The other three critical gaps (§3d confidence-probing, §3d defect escape rate, §6-R risk asymmetry) all stand and were independent of AI framing.

---

## 1. Executive Summary

The interview scripts excel at **current-state discovery**: §3a Process Journey, §3c Pain Points, §6-S Security & Data Governance, §6-A Assumptions, and §6-D Dependencies are well-covered with multi-persona triangulation. They **struggle with forward-looking sections**: §4b AI Integration Points has no journey-step probes, §6-R Risks is adoption-heavy and light on proposed-change failure modes, and §3d Confidence column will lean TBD / Estimated(n=1) because the *"tracked or estimated?"* probe is documented in interviewer notes but not embedded in the questions themselves. The brief is producible from the scripts as-written, but several sections (§4b, §3d defect escape rate, §1 problem-statement framing) will require either author speculation or post-IC follow-up sessions.

### Top three critical gaps (post-edit)

1. ~~**§4b AI Integration Points**~~ — **resolved by design.** Scripts no longer probe AI fit; §4b is author/architect-sourced. See §3.1 below.
2. ~~**§3d confidence-probing**~~ — **resolved at form layer.** The form generator now inserts a structured "Source of any number you give" block under every `[3d]`-tagged question, prompting participants to label their number as `Tracked` (with citation) / `Estimated` / `Not measured`. The compiler agent reads the structured field directly into §3d's Confidence column. Questions in source scripts unchanged. See §3.2 below.
3. ~~**§3d defect escape rate**~~ — **resolved.** Two new questions added: [QA Engineer Q26](interview/01-qa-engineer-interview.md) probes how many production defects came from features the team had already tested and signed off on (escape rate from the verifier's vantage point); [Release Manager Q12](interview/04-release-manager-interview.md) probes what fraction of post-deploy issues are QA-catchable defects vs. infra/third-party (escape rate from the deployer's vantage point). Triangulates against [QA Lead Q11](interview/02-qa-lead-interview.md). Both new questions are `[3d]`-tagged and get the form-level Source block automatically.
4. ~~**§6-R risk asymmetry**~~ — **largely resolved.** Three new failure-mode questions added: [QA Eng Q27](interview/01-qa-engineer-interview.md) (maintenance burden), [QA Lead Q32](interview/02-qa-lead-interview.md) (governance overhead timeline), [QA Lead Q35](interview/02-qa-lead-interview.md) (opportunity cost / competing investments). Ratio shifts to 3 adoption / 5 failure-mode (~37/63), reasonable balance. Vendor lock-in and skill atrophy remain unprobed by deliberate scope choice (lower decision-criticality for v0.1). See §3.4 below.

---

## 2. Section-by-Section Coverage

| Section | What it needs | Which scripts feed it | Verdict | Notes |
|---|---|---|---|---|
| **§1 Executive Summary** | Problem + direction + quantified outcome + ask | Dev Q22, PO Q19 (strongest case to leadership); Lead has none | ◌ Author-synthesized | Template says "write last." But no Lead question elicits a quotable problem-statement framing — author reconstructs from §3c clusters. |
| **§2 Problem Statement** | One paragraph, measurable, solution-agnostic | QA Eng Q9/Q24/Q26; Lead Q7/Q15/Q16/Q18; Dev Q8/Q10; Release Mgr Q5/Q6/Q12; PO Q3/Q4/Q6 | ✅ Covered | Multi-persona triangulation gives the author rich material to synthesize. |
| **§3a Process Journey** | Step-by-step flow, owner, duration, tooling | QA Eng Q4/Q6/Q10/Q14/Q15/Q17/Q23; Lead Q6/Q9; Dev Q2/Q3/Q4; Release Mgr Q3/Q4; PO Q11/Q12 | ✅ Covered | No standalone "tooling inventory" question — author extracts tooling from narrative. Acceptable. |
| **§3b Personas Involved** | Persona × role × primary pain | QA Eng Q2; Lead Q1/Q2; Dev Q1/Q2; PO Q2 (Release Mgr implicit) | ⚠ Partial | No question explicitly maps persona → primary process pain. Pain table populated by author synthesis from §3c. |
| **§3c Pain Points** | Pain × persona × quantified impact × frequency | All 5 scripts; QA Eng strongest (Q5, Q9, Q11, Q13, Q15, Q16, Q21, Q22, Q24, Q26, Q28); Lead extensive (Q3, Q7, Q8, Q9, Q15–Q21); Dev Q5–Q15; Release Mgr Q6/Q7/Q12; PO Q3/Q4/Q6/Q7/Q8/Q9/Q10 | ✅ Covered (extensive) | Strongest section in the discovery instrument. Quantification probes present in Q16, Q21, Q22, Release Mgr Q6, PO Q3/Q6/Q9 — but no embedded confidence probe (see §3d below). |
| **§3d Baseline Metrics** | 8 specific metrics × confidence (Tracked / Estimated / TBD) | QA Eng Q3/Q7/Q8/Q12/Q16/Q18/Q19/Q21/Q22; Lead Q4/Q11; Release Mgr Q1/Q2/Q5/Q6/Q11; PO Q3/Q5/Q6 | ⚠ Partial | Questions exist for most metrics, but **only Release Mgr Q11 has the inline confidence probe**. Confidence column will lean TBD / Estimated(n=1). See §3d matrix in appendix. |
| **§4a Target State** | "Good" operating model, testable against §3d | QA Eng Q27/Q29; Lead Q22/Q23; Dev Q17/Q18; Release Mgr Q15; PO Q14 | ✅ Covered | Every persona has an aspirational probe. No question explicitly links target state back to specific §3d metric improvements — author infers the causal link. |
| **§4b AI Integration Points** | AI capability × maturity × expected effect, per 5 journey steps | QA Eng Q30/Q31; Lead Q25/Q26; Dev Q19/Q20; Release Mgr Q17; PO Q16/Q17 | ❌ **Gap** | Generic "where should AI fit?" — not journey-step probes. 3 of 5 journey steps untouched. Maturity not assessed. See §4b deep dive and matrix below. |
| **§4c Updated Process Journey** | Mirror §3a, post-implementation, annotate changes | None directly | ◌ Author-synthesized | Built from §4a + §4b by the author. No interview validation probe — that's post-draft work. |
| **§5 Expected Value (quant)** | Outcome × baseline (from §3d) × target × time | Lead Q14/Q23; Dev Q18 (quantification probe present); Release Mgr Q14 (quantification probe present); PO Q15 | ⚠ Partial | Quant probe explicit only in Dev Q18 and Release Mgr Q14. QA Eng, Lead, PO not asked to quantify. No question links outcome → specific §3d metric. |
| **§5 Expected Value (qual)** | Outcome × evidence (3c pain or 3d metric) × why it matters | QA Eng Q27; Dev Q18; Release Mgr Q16; PO Q14/Q16 | ⚠ Partial | Qualitative material rich; evidence linkage left to author. |
| **§6-A Assumptions** | What must be true for plan to succeed | Lead Q19/Q24/Q26 | ✅ Covered | Lead Q24 and Q26 directly probe constraints and AI-specific assumptions. Other personas not asked — minor gap (Dev/PO might surface different assumptions). |
| **§6-R Risks** | Adoption + proposed-change failure modes (~50/50) | Adoption: QA Eng Q25/Q31, Lead Q27/Q30, Dev Q20, PO Q16. Failure-mode: Lead Q34/Q35, PO Q17 | ⚠ **Asymmetric** | 6 adoption vs. 3 failure-mode. Missing entirely: maintenance burden, opportunity cost, vendor lock-in, governance overhead, skill atrophy. False-confidence probe never asked of QA Eng. See deep dive. |
| **§6 Stop Conditions** | Pre-committed triggers × thresholds × actions | Lead Q35 only | ⚠ Weak | Single-source. No metric-specific stop-condition probes (e.g., "at what defect-escape threshold would you halt?"). |
| **§6-S Security & Data Governance** | Data classification, PII, vendor data-handling, sign-offs, approved-tooling envelope | Lead Q31/Q32/Q33 | ✅ Covered | All 5 dimensions touched. Vendor data-handling probed via "who signs off?" but not via "what's our policy on sending test data to third-party AI?" — see significant gaps. |
| **§6-D Dependencies** | Dependency × owner × required by | Lead Q3/Q28/Q29; others implicit | ✅ Covered | Lead Q28/Q29 directly probe. Dev/Release Mgr/PO not asked "what would we need from you for this to work?" — minor gap. |
| **§7 Proposed Approach** | Phasing × scope × duration × success criteria | Lead Q22/Q35; Dev Q18; Release Mgr Q14; aspirational answers across scripts | ⚠ Partial | No question probes pilot scope, Phase 1 success metric, or realistic phase duration. Author infers phasing from pain prioritization. |
| **§7 Opportunity Cost** | Do-nothing trajectory + next-best alternative | Lead Q3/Q7 (sustainability inferred); PO Q3/Q6 (growth implies worsening) | ❌ **Gap** | No question asks "if we don't do this, where are we in 2 quarters?" or "what alternatives are being considered?" Strategic context must come from outside interviews. |
| **§8 The Ask** | Funding, headcount, scope, deadline, decision-makers | Lead Q3/Q28/Q29/Q32 | ◌ Author-sourced | Template line 203 says §8 fills from sponsor context, not interviews. Lead Q29 surfaces decision-makers; Q32 surfaces sign-off functions — useful inputs, not a substitute for sponsor conversation. |

---

## 3. Critical Gaps — Deep Dive

### 3.1 §4b AI Integration Points — by design, not a gap (post-edit)

**Status:** Resolved by scope decision on 2026-05-06. The original audit flagged this as the #1 critical gap on the assumption that interviews would feed §4b. That assumption was wrong: participants have varying levels of AI knowledge, so probing them on AI fit produces noise rather than signal. The brief's §4b is now filled by the author/architect from external AI tooling assessment, not from interview synthesis. All AI-fit and AI-capability questions were removed from the scripts (see commit history). The original analysis is preserved below for context.

---

The template's §4b table requires AI capability + maturity + expected effect for **5 specific journey steps**: test authoring, test data management, run orchestration, result verification, defect triage. The original scripts asked AI questions in a different shape entirely:

- [QA Eng Q30](interview/01-qa-engineer-interview.md): *"Have you used AI-assisted tooling for QA work? What worked, what didn't?"* — tooling-experience question
- [QA Eng Q31](interview/01-qa-engineer-interview.md): *"What part of your job should AI **not** be doing, and why?"* — boundary question
- [QA Lead Q25](interview/02-qa-lead-interview.md#L79): *"Where do you see AI fitting in — and where do you think it's a bad fit?"* — generic fit question
- [QA Lead Q26](interview/02-qa-lead-interview.md#L80): *"What capabilities do you assume will need to be true for AI integration to work?"* — feeds §6-A, not §4b
- [Dev Q19/Q20](interview/03-developer-interview.md): symmetric to QA Eng Q30/Q31
- [PO Q16/Q17](interview/05-product-owner-interview.md): risk-perception, not journey-step fit

**Coverage by journey step (matrix in appendix):**

| Journey step | AI-specific probe? | Maturity probe? |
|---|---|---|
| Test authoring | ⚠ Indirect (inferred from pain Q9 + general AI fit) | ❌ |
| Test data management | ❌ None | ❌ |
| Run orchestration | ❌ None | ❌ |
| Result verification | ⚠ Indirect (inferred from pain Q24) | ❌ |
| Defect triage | ❌ None | ❌ |

**Implication:** The §4b table cannot be populated credibly from the scripts alone. The author will either invent capability mappings or run targeted post-IC follow-ups. Capability maturity (Established / Emerging / Experimental) is not asked of any persona.

### 3.2 §3d Confidence-probing — addressed at form layer (post-edit)

**Status:** Resolved on 2026-05-06. The form generator skill ([interview-form-generate](.github/skills/interview-form-generate/SKILL.md)) now detects `[3d]`-tagged questions and inserts a structured prompt under each response:

```markdown
**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

> _(your source here)_
```

Participants can't skip past the prompt without seeing it; the compiler agent reads the labeled value directly into §3d's Confidence column. Source scripts are unchanged — capture happens at the form-template layer, not in question wording. The original analysis below is preserved for context.

---


The methodology at [interview/00-interview-guide-overview.md line 35](interview/00-interview-guide-overview.md#L35) requires a standard probe after every numeric answer: *"Is that a number you've seen reported, or an estimate?"* The brief's §3d Confidence column (Tracked / Estimated(n=X) / TBD) depends on this distinction.

The probe **lives in interviewer-side notes**, not in the question text:
- [QA Engineer line 92](interview/01-qa-engineer-interview.md#L92): *"Tracked vs. estimated: 'Is that number something you've seen reported on a dashboard or ticket, or is it your own estimate?' (Apply after every numeric answer — Q3, Q7, Q8, Q12, Q16, Q18–22.)"* — interviewer note, not embedded in the questions
- [QA Lead line 47](interview/02-qa-lead-interview.md#L47): *"Probe per item: 'Tracked, estimated, or not measured?'"* — note above Q11, not in the question itself

**Only one numeric question embeds the probe inline:**
- [Release Mgr Q11](interview/04-release-manager-interview.md#L31): *"...most common root cause? **Tracked or estimated?**"*

**Inventory — numeric questions across all scripts:**

| Question | Metric probed | Inline probe? |
|---|---|---|
| QA Eng Q3 | Time allocation across activities | ❌ |
| QA Eng Q7 | Authoring time per scenario | ❌ |
| QA Eng Q8 | Rework rate after review | ❌ |
| QA Eng Q12 | Data-issue failure rate | ❌ |
| QA Eng Q16 | Flake / re-run rate | ❌ |
| QA Eng Q18 | Verification time per run | ❌ |
| QA Eng Q19 | Verification runs per week | ❌ |
| QA Eng Q21 | False-positive frequency | ❌ |
| QA Eng Q22 | False-negative frequency | ❌ |
| Lead Q4 | Team time allocation | ❌ |
| Lead Q11 (8 metrics) | All §3d metrics | ⚠ Probe in note above question, not inline |
| Dev Q4 | Feedback-loop latency | ❌ |
| Dev Q6 | Defect round-trip count | ❌ |
| Dev Q7 | Commit-to-QA-result time | ❌ |
| Dev Q15 | Escape-pattern frequency | ❌ |
| Release Mgr Q2 | Releases on time | ❌ |
| Release Mgr Q5 | QA-gate duration | ❌ |
| Release Mgr Q6 | % releases held | ❌ |
| **Release Mgr Q11** | Hotfix rate, root cause | ✅ |
| PO Q3 | Feature delays | ❌ |
| PO Q6 | Capacity-driven descope | ❌ |

**19 of 20 numeric questions lack the inline probe.** An interviewer following the script literally — without internalizing the side notes — will collect numbers without confidence tags. The brief's §3d Confidence column will then be reconstructed from notes after the fact, with predictably lossy results.

### 3.3 §3d Defect escape rate — addressed (post-edit)

**Status:** Resolved on 2026-05-06. Two questions added to triangulate the rate against [QA Lead Q11](interview/02-qa-lead-interview.md):
- [QA Engineer Q26](interview/01-qa-engineer-interview.md): *"In the past quarter, roughly how many production defects came from features your team had already tested and signed off on? Of those, were the relevant tests passing — meaning the suite ran green and missed it — or were the defects in areas your tests didn't cover?"* — verifier's view, separates test-failure escape from coverage-gap escape.
- [Release Manager Q12](interview/04-release-manager-interview.md): *"Of customer-facing issues that surface in the first week or two post-deploy, what fraction would you consider QA-catchable defects — bugs in tested-and-verified surface area — vs. infrastructure issues, third-party regressions, or out-of-scope problems?"* — deployer's view, separates QA-catchable from non-catchable.

Both `[3d]`-tagged, both get the structured Source block in the form. Original analysis below preserved for context.

---


- **No QA Eng question directly asks** "what's our defect escape rate?" — [Q21–Q22](interview/01-qa-engineer-interview.md) probe false-positives and false-negatives, but those are not the same metric. False-negative = test passed when it shouldn't have; defect escape rate = bug reached production. Different gates.
- [QA Lead Q11](interview/02-qa-lead-interview.md#L37) lists "Defect escape rate" as one of 8 sub-items, but is the sole direct probe. No IC corroboration.
- [Release Mgr Q10](interview/04-release-manager-interview.md): *"When a release goes wrong post-deploy, was there an upstream signal we missed?"* — anecdotal, not a rate.
- [Release Mgr Q11](interview/04-release-manager-interview.md#L31) probes hotfix rate (related but distinct: hotfix = deployed fix; escape = uncaught defect).
- [PO Q7/Q9](interview/05-product-owner-interview.md) probe customer escalation examples — anecdotal.

**Implication:** §3d's defect escape rate row will be Estimated(n=1) at best, TBD likely. This is a high-visibility metric for leadership; weak baseline here invites pushback.

### 3.4 §6-R risk asymmetry — largely resolved (post-edit)

**Status:** Largely resolved on 2026-05-06. Three failure-mode questions added (maintenance burden, governance overhead, opportunity cost). Vendor lock-in and skill atrophy remain unprobed by deliberate scope choice — lower decision-criticality for v0.1. The original analysis is preserved below for context.

CLAUDE.md says *"roughly half of `[6-R]` should describe failure modes of the proposed change, not only current-state pain."* Counting `[6-R]`-tagged questions across all scripts (post-edit, all three rounds):

**Adoption / current-state friction (3):**
- [QA Eng Q25](interview/01-qa-engineer-interview.md): delegation-worry — "what would you be worried about delegating?"
- [QA Lead Q25](interview/02-qa-lead-interview.md): political/organizational risks
- [QA Lead Q28](interview/02-qa-lead-interview.md): team appetite for change

**Proposed-change failure modes (5):**
- [QA Eng Q27](interview/01-qa-engineer-interview.md) *(new)*: maintenance burden — would automated test maintenance be heavier or lighter as code evolves?
- [QA Lead Q32](interview/02-qa-lead-interview.md) *(new)*: governance overhead — InfoSec/Legal review timeline eroding operational benefit
- [QA Lead Q33](interview/02-qa-lead-interview.md): confident-but-wrong tooling output (existing, reframed from AI-naming)
- [QA Lead Q34](interview/02-qa-lead-interview.md): "what does failure look like" (existing) — stop-condition framing
- [QA Lead Q35](interview/02-qa-lead-interview.md) *(new)*: opportunity cost — what other QA investments compete for the same capacity?
- [PO Q16](interview/05-product-owner-interview.md): confident-but-wrong quality signals (existing, neutrally framed)

(Note: 6 entries above — PO Q16 also counts as failure-mode. Total proposed-change probes = 6 if you include PO; 5 across the QA-team scripts.)

**Ratio (post-edit, including PO Q16): ~3 adoption / 6 failure-mode = ~33/67.** Still slightly heavier on failure-mode side after the round-3 additions, but acceptable: leadership review is far more demanding on failure-mode coverage than on adoption coverage, and adoption risk material can come from prose answers across §3c questions even without dedicated `[6-R]` probes.

**Remaining failure-mode probes deliberately out of scope (v0.1):**
- **Vendor lock-in** — strategic risk; flagged in audit but lower decision-criticality at the discovery stage. Surface in author/architect synthesis or §6 Dependencies if it bites.
- **Skill atrophy** — softer, longer-term concern. Author can synthesize from §3c "engaging part of job" and §4a aspirational answers if relevant.

**Pre-edit baseline (for historical reference):**
- Original (with AI-fit questions): 6 adoption vs. 3 failure-mode = 67/33
- After AI-fit removal: 3 adoption vs. 2 failure-mode = 60/40
- After round-3 failure-mode additions: 3 adoption vs. 5–6 failure-mode = ~37/63 (or ~33/67 counting PO Q16)

**Specific failure-mode probes that are entirely missing:**
- **Maintenance burden** — Are AI-assisted tests harder to keep in sync as code changes?
- **Opportunity cost** — What else could we do with this investment, and why does this beat that?
- **Vendor lock-in** — How hard would it be to switch vendors or revert to non-AI verification?
- **Governance overhead** — Will InfoSec / Legal review of AI tooling slow rollout enough to erode the win?
- **Skill atrophy** — Will QA engineers' manual-verification skills decay if AI handles 80% of verification?
- **False-confidence at the IC layer** — [QA Lead Q34](interview/02-qa-lead-interview.md#L99) asks the Lead this question, but the IC closest to verification is never asked the equivalent. The Lead's answer will be theoretical; the IC's would be specific.

---

## 4. Significant Gaps

- **§3b Personas — no persona-to-pain mapping.** Pain (§3c) and persona (§3b) surfaced separately. No question of the form "what's *your* primary bottleneck in the QA process?" The §3b Primary-Pain column is reconstructed by author synthesis from scattered §3c answers.
- **§4b Capability maturity not assessed.** Template asks Established / Emerging / Experimental per AI capability. No question elicits an interviewee's read on what's real vs. aspirational. Author must categorize from external knowledge or leave blank.
- **§4c Updated Process Journey — no validation probe.** Acceptable: this is post-draft validation work, typically done in the Lead follow-up. Flag only if the follow-up gets skipped.
- **§5 Expected Value — quantification not enforced.** Quantification probe explicit only in [Dev Q18](interview/03-developer-interview.md) (*"try to quantify"*) and [Release Mgr Q14](interview/04-release-manager-interview.md). QA Eng, QA Lead, and PO are not asked to quantify expected improvements in their domains. No question links outcome → specific §3d metric ("if we cut verification from 2 days to 4 hours, what would that enable?").
- **§6 Stop Conditions — single-source.** Only [QA Lead Q35](interview/02-qa-lead-interview.md#L100) probes failure definition. No metric-specific stop-condition probes (e.g., "at what defect-escape threshold would you call it?", "how long would you wait before go/no-go?").
- **§6-S Vendor data-handling — implicit only.** [Lead Q32](interview/02-qa-lead-interview.md#L94) asks who must approve, but doesn't ask "what's the org's policy on sending test code/data to third-party AI services?" — data residency, training-on-customer-data posture, masking readiness. Author infers from sign-off precedent.
- **§7 Opportunity Cost — not probed.** No question asks do-nothing trajectory ("if we don't invest, where are the metrics in 2 quarters?") or next-best alternative ("what else could we do with this capacity?"). Strategic context must come from outside the interview set.

---

## 5. Process Issues

- **AI-question placement in QA Lead script.** [Q25–Q26](interview/02-qa-lead-interview.md#L79-L80) (AI fit, AI capabilities) sit at minute ~45–50 of the first 60-minute session. The [interviewer note at line 7](interview/02-qa-lead-interview.md#L7) says: *"Defer 'where's the real bottleneck' and 'where does AI fit' to the optional follow-up after IC interviews — running interpretation here anchors the rest of discovery on management narrative."* The script partially handles the conflict via a "defer if time runs short" mechanism on §6 aspirational and §7 failure-modes, but does not cleanly enforce "AI questions only in follow-up." The contradiction between line 7 and Q25–Q26 is resolvable two ways: remove Q25–Q26 from the first session entirely, or rewrite the line-7 note to acknowledge that Q25–Q26 are intentionally in the first session.
- **[Release Mgr Q17](interview/04-release-manager-interview.md) persona mismatch.** Tagged `[4b]`, but Release Mgr is a downstream consumer of QA results, not a design stakeholder for AI integration. The question is closer to "what would you need to trust new tooling output?" — a `[6-R]` trust-as-risk question. QA Eng and QA Lead are the relevant personas for §4b design.
- **[PO Q3 and Q6](interview/05-product-owner-interview.md) tagged `[3d]` but probe perception, not instrumented data.** *"Were features delayed and was QA the cause?"* and *"Did you descope due to QA capacity?"* are valuable §3c business-impact framing, but Product Owner doesn't track per-team delay attribution as a metric. These shouldn't populate §3d Baseline Metrics rows directly; if the brief author treats them as `[3d]` data, the resulting numbers will be perception clusters, not metrics.
- **Single-source metrics weaken §3d.** Authoring time is asked only of QA Eng (no Lead corroboration of the per-scenario number — [Lead Q11](interview/02-qa-lead-interview.md#L37) lists it but at team-aggregate level). Defect escape rate is asked only of Lead (no IC corroboration). Per the [methodology](interview/00-interview-guide-overview.md#L84), n=1 estimates are weak for v0.1 baseline.

---

## 6. Strengths (preserve in any future revision)

- **§3a Process Journey** — heavy multi-persona coverage: QA Eng walks through authoring/data/execution/verification, Lead provides end-to-end view, Dev describes hand-off mechanics, Release Mgr describes gate artifacts, PO describes signal consumption. Author can triangulate without invention.
- **§3c Pain Points** — broadest section; every persona contributes. Quantification probes present in flake (QA Eng Q16), false-positive/negative (Q21–Q22), % releases held (Release Mgr Q6), and PO escalation patterns.
- **§6-S Security & Data Governance** — all 5 dimensions covered in [QA Lead Q31–Q33](interview/02-qa-lead-interview.md#L93-L95) per CLAUDE.md convention. Data classification, PII probing, sign-off functions, approved-tooling envelope, and governance precedent all asked.
- **§6-A Assumptions** — directly probed in [QA Lead Q24 and Q26](interview/02-qa-lead-interview.md#L78-L80). Q24 covers organizational/compliance constraints; Q26 covers AI-specific capability assumptions.
- **§6-D Dependencies** — directly probed in [QA Lead Q28–Q29](interview/02-qa-lead-interview.md#L87-L88). Q28 surfaces enabling resources; Q29 surfaces decision-makers.
- **AI-questions placement** — correctly at end-of-script for QA Engineer, Developer, Release Manager, and Product Owner. The bias-mitigation rule holds for 4 of 5 scripts; QA Lead is the exception.

---

## 7. Implications for the Brief

- **§4b will be the hardest section to populate credibly.** The scripts produce general AI-fit sentiment, not journey-step-specific capability assessments. The author will need to either run targeted post-IC follow-ups (probably with QA Eng and QA Lead) or label §4b entries as "TBD — needs targeted discovery" rather than fabricating capability mappings.
- **§3d Confidence column will lean TBD / Estimated(n=1).** Without inline confidence probes, even tracked numbers may be transcribed without their tracking source. Leadership review will likely challenge specific baseline numbers; the brief author should anticipate questions like "where did the 2-day verification number come from — a dashboard or a guess?" and have an answer.
- **§6-R will read as adoption-heavy.** Without explicit failure-mode synthesis from minimal source material (only [Lead Q34/Q35](interview/02-qa-lead-interview.md#L99-L100) and [PO Q17](interview/05-product-owner-interview.md)), the risk table will skew toward "team doesn't like change" and miss the proposed-change failure modes leadership will most want to interrogate (hallucinated tests, false confidence, vendor lock-in, opportunity cost).
- **§1 problem-statement framing will lack a quotable Lead sentence.** No Lead question asks "in one sentence, what is the bottleneck and what does a good fix look like?" The author reconstructs §1 from §3c clusters; this works but produces a less defensible single-sentence framing for the executive summary.
- **§7 Opportunity Cost will require sponsor-side input.** The interview set doesn't probe do-nothing trajectory or alternative investments. The author can ground the do-nothing trajectory in §3d trends, but the next-best-alternative line needs to come from sponsor conversation outside the interviews.

---

## Appendix A — §3d Baseline-Metric Coverage Matrix

For each of the 8 metrics, who probes it and is the inline confidence probe present?

| Metric | Probed by | Inline confidence probe? | Likely confidence outcome |
|---|---|---|---|
| 1. Authoring time per scenario | QA Eng Q7; Lead Q11 | ❌ both | Estimated(n=1 to n=2), low confidence |
| 2. Verification time per run | QA Eng Q18; Lead Q11 | ❌ both | Estimated, possible IC/Lead divergence |
| 3. Verification hours / sprint | QA Eng Q19 (derivable); Lead Q4 (team-level %); Lead Q11 | ❌ all | Derived; confidence weak |
| 4. Defect escape rate | **Post-edit:** QA Eng Q26 (verifier view), Release Mgr Q12 (deployer view), QA Lead Q11 (Lead view) — three independent IC vantage points; PO Q7/Q9 = anecdotal | ✅ via form-level Source block | Estimated(n=3) likely; promotable to Tracked if any source cites a dashboard |
| 5. Hotfix rate per release | Release Mgr Q11; Lead Q11 | ✅ Release Mgr Q11 / ❌ Lead Q11 | Tracked-or-Estimated, medium confidence |
| 6. Release cycle time | Release Mgr Q1/Q2 (cadence inferred); Lead Q11; PO Q5 (QA portion only) | ❌ all | Indirect; possibly TBD |
| 7. QA-blocked release % | Release Mgr Q6 (direct); Lead Q11 | ❌ both | Estimated, two-source |
| 8. Flake / re-run rate | QA Eng Q16; Lead Q11; QA Eng Q21 (proxy) | ❌ all | Estimated(n=2), no tracking source |

---

## Appendix B — §4b AI-Fit Coverage Matrix

For each of the 5 journey steps in the brief template, which scripts probe AI fit?

| Journey step | QA Eng | Lead | Dev | Release Mgr | PO | Coverage |
|---|---|---|---|---|---|---|
| **Test authoring** | Q30/Q31 (generic) | Q25 (generic) | Q19 (generic) | — | — | ⚠ Indirect |
| **Test data management** | — | — | — | — | — | ❌ None |
| **Run orchestration** | — | — | — | Q17 (tooling-trust, not design) | — | ❌ None |
| **Result verification** | Q24 (pain, AI fit inferred); Q25 (delegation worry) | — | — | — | — | ⚠ Indirect |
| **Defect triage** | — | — | — | — | — | ❌ None |

**Maturity assessment (Established / Emerging / Experimental):** never asked of any persona for any step.

---

## Appendix C — Mistagged or Persona-Mismatched Questions

| Question | Current tag(s) | Issue | Suggested handling |
|---|---|---|---|
| [Release Mgr Q17](interview/04-release-manager-interview.md) | `[4b]` | Release Mgr is downstream consumer, not design stakeholder for AI integration | Treat as `[6-R]` trust-as-risk; do not feed §4b directly |
| [PO Q3](interview/05-product-owner-interview.md) | `[3c] [3d]` | Asks perception ("was QA the cause?"), not instrumented data | Feed §3c only; do not populate §3d row |
| [PO Q6](interview/05-product-owner-interview.md) | `[3c] [3d]` | Asks perception (descope-due-to-QA), not metric | Feed §3c only; do not populate §3d row |
| [PO Q9](interview/05-product-owner-interview.md) | `[3c] [3d]` | Asks for 2–3 examples, not a rate (script even says "don't try to estimate %") | Feed §3c only; do not populate §3d row |

---

## Appendix D — What Would "Fully Covered" Look Like?

If you choose to revise the scripts further, the highest-leverage additions (in priority order, **post-edit status noted**):

1. ~~Embed the confidence probe inline in every numeric question~~ — **resolved at form layer.** The form generator now inserts a structured "Source" block under every `[3d]`-tagged question; source scripts unchanged.
2. ~~Add 5 journey-step AI-fit probes~~ — **no longer applicable.** §4b is author/architect-sourced; AI-fit interview probes were deliberately removed.
3. **Add 5 proposed-change failure-mode probes** to balance §6-R, all phrased in neutral "new tooling" / "automated verification" language: maintenance burden (QA Eng), opportunity cost (Lead or PO), vendor lock-in (Lead), governance overhead (Lead), skill atrophy (QA Eng). **Status: 3 of 5 added** — [QA Eng Q27](interview/01-qa-engineer-interview.md) (maintenance), [QA Lead Q32](interview/02-qa-lead-interview.md) (governance overhead), [QA Lead Q35](interview/02-qa-lead-interview.md) (opportunity cost). Vendor lock-in and skill atrophy deliberately deferred — lower decision-criticality at v0.1.
4. ~~Add a defect-escape-rate question~~ — **resolved.** [QA Engineer Q26](interview/01-qa-engineer-interview.md) and [Release Manager Q12](interview/04-release-manager-interview.md) added.
5. ~~Add an opportunity-cost probe to QA Lead~~ — **resolved** by [QA Lead Q35](interview/02-qa-lead-interview.md) ("what other QA investments compete with this one for the same capacity"). The do-nothing-trajectory variant ("where are these metrics in 2 quarters if we don't invest?") is still unprobed but lower priority — author can ground that in §3d trends.
6. ~~Resolve QA Lead AI-question placement~~ — **resolved by removal.** Q25–Q26 (AI fit, AI capabilities) were deleted; the "defer 'where does AI fit' to follow-up" note in line 7 was updated accordingly.
7. **Re-tag [PO Q3/Q6/Q9](interview/05-product-owner-interview.md)** to remove `[3d]` (perception, not metric). **Status: not done.**
8. ~~Re-tag Release Mgr Q17~~ — **resolved by removal.** The question was deleted in the AI-fit cleanup.

Item 7 (PO Q3/Q6/Q9 `[3d]` mistag) is the remaining quality improvement.
