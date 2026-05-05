# Peer Review — QA AI Automation Planning Package

## 1. Top 3 Issues to Fix Before Proceeding

1. Remove the solution-leading AI framing from the brief and the closing questions in multiple interviews; the package currently reads like it is validating a chosen answer rather than discovering whether AI is the right answer.
2. Reconcile the package's metric standard; the overview tells the author to turn interview estimates into baselines, while the brief says untracked metrics must stay TBD, which makes section 5 non-falsifiable as written.
3. Add decision-grade content and sourcing for governance, change, and stop conditions; the brief asks for a funding decision without a credible way to surface pilot exit criteria, rollback logic, security/data governance, or opportunity cost.

## 2. Findings by File

### claude/qa-ai-automation-strategy-brief-template.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Critical | Missing | Sections 6-8 | The brief asks for a real funding decision without sections for pilot exit criteria, rollback or stop conditions, change management, or security/data governance handling. | Add those decision controls inside sections 6 and 7 rather than as new artifacts. |
| Major | Falsifiability | Section 5 | The qualitative value bullets cannot be traced to baseline metrics in 3d, so the template violates its own rule that every value claim must be measurable. | Either convert each qualitative claim into a measurable indicator or remove it from the core value section. |
| Major | Bias | Section 1 example; Section 4b | The executive-summary example and the dedicated AI Integration Points section push the author toward an AI-shaped conclusion before the problem is fully established. | Keep the target state solution-agnostic first and make section 4b explicitly justify whether AI is appropriate rather than assume it is. |

### claude/00-interview-guide-overview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Major | Inconsistency | Question Tagging Convention | The convention does not define tag 5 even though later scripts use it, which will break a section-based synthesis process. | Define tag 5 in the convention or remove it from the scripts. |
| Major | Ordering | Recommended Interview Sequence | Starting with the QA lead is defensible, but the overview does not constrain that first session to factual scoping, so it can anchor the rest of discovery around management narratives. | Explicitly restrict the first QA lead interview to structure, metrics, and candidate interviewees, then defer interpretation until after IC interviews. |

### claude/01-qa-engineer-interview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Major | Ordering | Section 5, Questions 17-25 | The verification deep dive allocates 15 minutes to nine detailed questions, which is not enough to get reliable process and quantification detail on the package's stated bottleneck. | Cut one or two lower-value prompts and protect more time for the verification walk-through. |
| Minor | Quantification | Questions 3, 7, 12, 16, 18-22 | The script asks for many numbers but rarely distinguishes tracked data from personal recall, which matters because the brief is supposed to separate real baselines from estimates. | Add a standard probe asking whether each number is tracked, estimated, or inferred. |

### claude/02-qa-lead-interview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Major | Quantification | Section 3, Questions 10-13 | The metrics block tries to collect current metrics, missing metrics, metric trustworthiness, and leadership-priority metrics in 12 minutes, which is too dense for dependable baseline capture. | Split tracked metrics from aspirational metrics and make confidence assessment a follow-up if time runs short. |
| Major | Bias | Section 6, Questions 22-24 | The sequence of unconstrained-budget visioning followed immediately by where AI fits primes the interviewee to solution in an AI direction instead of exposing constraints first. | Ask for the desired future state and constraints first, then leave AI suitability as an optional last question. |

### claude/03-developer-interview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Major | Bias | Question 2 | The question assumes a developer-written versus QA-written test split that may not exist and will distort answers on teams with different ownership models. | Ask for current test ownership boundaries without presupposing how responsibility is divided. |
| Major | Coverage | Header; Questions 17-21 | The script says it informs section 5, but it does not reliably extract measurable value outcomes or leadership-facing benefits. | Add one or two explicit value questions tied to delivery, rework, or release outcomes, or remove section 5 from the informed list. |

### claude/04-release-manager-interview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Critical | Bias | Question 17 | Asking for concerns about AI being part of the gate decision presupposes that AI is already a candidate gate mechanism. | Rephrase it to ask what role, if any, new automation or tooling should play in release decisions. |
| Major | Ordering | Sections 2-5 | The script is overstuffed for 30 minutes, with multiple walk-throughs, hypotheticals, and quantification requests that will force shallow answers or overruns. | Reduce it to a smaller core set and mark lower-priority prompts as optional. |

### claude/05-product-owner-interview.md

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Critical | Bias | Question 16 | Asking for concerns about AI in quality decisions presupposes that AI belongs in those decisions and shifts the interview from discovery to solution vetting. | Rephrase it to ask whether any new approach to QA decision support would raise concerns and why. |
| Major | Quantification | Question 9 | The question asks the product owner for a counterfactual percentage they are unlikely to know and frames "more rigorous QA" as the obvious answer. | Ask for representative escape patterns and business impact instead of a percentage attribution to QA rigor. |

## 3. Package Coherence Findings

| Severity | Category | Location | Issue | Recommendation |
| --- | --- | --- | --- | --- |
| Critical | Inconsistency | claude/qa-ai-automation-strategy-brief-template.md, Section 3d; claude/00-interview-guide-overview.md, Synthesis Approach step 2 | The brief says untracked metrics should remain TBD, while the overview tells the author to turn clustered interview estimates into baseline numbers, which guarantees fake precision in section 5. | Pick one rule and apply it consistently: either permit clearly labeled interview estimates or keep untracked metrics as TBD until instrumented. |
| Major | Coverage | claude/qa-ai-automation-strategy-brief-template.md, Sections 7-8; all interview scripts | The package provides no reliable discovery path for decision-maker, budget envelope, pilot-scope appetite, or acceptable stop conditions, so the proposed approach and ask will be largely author-invented. | Add targeted discovery for sponsor constraints or narrow those fields so they are explicitly author-supplied. |
| Major | Missing | All interview scripts | No security/compliance, finance, or platform/infrastructure persona is interviewed even though the brief needs governance, dependency, and funding-grade content. | Add those missing voices or explicitly mark those dimensions out of scope for v0.1. |
| Major | Inconsistency | claude/qa-ai-automation-strategy-brief-template.md, Section 3b; claude/01-qa-engineer-interview.md, Question 2; claude/02-qa-lead-interview.md, Questions 1-2; claude/03-developer-interview.md, Question 2 | The brief's Personas Involved table mixes process participants, org roles, and pain ownership, but the interviews do not collect that structure consistently enough to fill it cleanly. | Decide whether section 3b is about process personas or org roles, then retag and tighten questions to match. |
| Major | Coverage | claude/01-qa-engineer-interview.md, Questions 30-31; claude/02-qa-lead-interview.md, Questions 24-29; claude/04-release-manager-interview.md, Question 17; claude/05-product-owner-interview.md, Question 16 | The package probes today's pain deeply but probes failure modes of the proposed change only lightly and mostly as AI-risk closers, so the risk section will be one-sided. | Add explicit questions on adoption failure, false confidence, governance overhead, and opportunity cost rather than only current-state pain. |

## 4. What's Working

- The brief's process-journey and baseline-metrics tables are concrete enough to force evidence rather than vague narrative.
- The overview's instruction to synthesize by brief section instead of by interviewee is the right operating model.
- The QA engineer script correctly spends most of its attention on verification, which is the package's likeliest bottleneck.
- The overall persona set covers the core operational path from authoring through release, even if governance and finance voices are missing.

## 5. Open Questions for the Author

- Are interview-derived estimates acceptable as baseline numbers in this package, or do you want any untracked metric to remain TBD until instrumented?
- Is section 8 meant to be filled from discovery, from sponsor context you already know, or from a separate leadership conversation not represented here?
- Are you intentionally excluding security, compliance, and finance from v0.1, or were those personas omitted accidentally?
- Do you want section 3b to describe process participants across the release flow or internal QA team structure?
- Is build-versus-buy and opportunity-cost framing out of scope for this draft, or do you expect the finished brief to survive a CFO or CTO review without it?