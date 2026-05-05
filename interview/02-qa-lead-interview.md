# Interview Script — QA Lead / Manager

**Persona:** QA team lead, manager, or director with cross-team visibility
**Duration:** 60 minutes (script runs ~63; sections 6.aspirational and 7.failure-modes flow to the follow-up if time runs short)
**Brief sections informed:** 3a, 3b, 3c, 3d, 4a, 4b, 5, 6-A, 6-R, 6-D, 6-S, 7, 8

> **Interviewer note:** Treat the first Lead session as **scoping**, not interpretation. Capture facts, structure, metrics inventory, security/governance constraints, and candidate ICs. Defer "where's the real bottleneck" and "where does AI fit" to the optional follow-up after IC interviews — running interpretation here anchors the rest of discovery on management narrative.

---

## 1. Team Structure & Capacity (8 min)

1. How is the QA team structured today — by product, by surface area, by skill?
2. How many engineers, how many leads, where are the gaps? `[3b]`
3. What's the current backlog vs. capacity ratio? Are you hiring, frozen, or shrinking? `[3c] [6-D]`
4. What % of team time goes to net-new test development vs. maintenance vs. verification vs. exploratory? `[3d]`
5. What does onboarding a new QA engineer look like, and how long until they're productive? `[3d]`

---

## 2. Process Oversight (10 min)

6. From your vantage point, walk me through the end-to-end QA flow as it exists today — authoring, data, execution, verification, reporting. `[3a]`
7. Where do you most often see work pile up? `[3c]`
8. Which steps depend on a specific person being available? `[3c] [6-R]`
9. Where does work hand off between QA and other teams? Where do those handoffs break down? `[3a] [3c]`

---

## 3. Metrics — tracked first, aspirational second (12 min)

> This section directly populates §3d of the brief. **Keep tracked vs. aspirational separated** — the brief's Confidence column distinguishes Tracked from Estimated from TBD, and that distinction is set here.

### 3a. Tracked metrics (first 6 min — what actually exists today)

10. What metrics do you currently track for the QA team? Where do they live, who sees them? `[3d]`
11. For each of the following, is there a tracked number — and if so, where does it come from? `[3d]`
    - Avg. authoring time per scenario
    - Avg. verification time per run
    - Verification hours / sprint
    - Defect escape rate (post-release defects vs. caught in QA)
    - Hotfix rate per release
    - Release cycle time
    - % of releases blocked by QA at the gate
    - Flake rate / re-run rate

> Probe per item: *"Tracked, estimated, or not measured?"* Anything not tracked stays TBD in §3d unless an IC cluster establishes a defensible estimate.

### 3b. Trust and aspirational (next 6 min — only if time allows; otherwise defer to follow-up)

12. Of the metrics you do have, which do you trust? Which do you suspect are wrong or stale? `[3d]`
13. What metrics do you wish you had but don't? `[3d] [3c]`
14. What metric, if it improved, would leadership most clearly recognize as a win? `[5]`

---

## 4. Bottleneck Visibility (8 min)

15. When other teams say "QA is slow," what do they specifically mean — and is it accurate? `[3c]`
16. What's the most common reason a release gets delayed at the QA gate? `[3c] [3d]`
17. Where does your team get blamed for things that aren't actually QA's fault? `[3c]`
18. Where does your team genuinely under-deliver, in your honest assessment? `[3c]`

---

## 5. Cross-Team Friction (5 min)

19. How well do specs/requirements arriving at QA support effective testing? `[3c] [6-A]`
20. How tight is the feedback loop between QA findings and dev fixes? `[3a] [3c]`
21. Where does Product/Release pressure conflict with QA quality goals? `[3c]`

---

## 6. Future State (10 min)

22. If you had unconstrained budget and authority for two quarters, what would you change about how this team operates? `[4a]`
23. What would "good" look like from a leadership-visible metric perspective? `[5]`
24. _(After #22–23, before any solution framing)_ What constraints would any change to this team have to respect — security, compliance, vendor approvals, change windows, team appetite, headcount caps? `[6-A] [6-S] [6-D]`
25. _(After #24)_ Where do you see AI fitting in — and where do you think it's a bad fit? `[4b] [6-R]`
26. What capabilities do you assume will need to be true for AI integration to work — accuracy, latency, explainability, integration with existing tools? `[6-A]`

---

## 7. Risks, Dependencies, Governance (8 min)

27. What are the political or organizational risks of this kind of change for the QA team? `[6-R]`
28. What would you need from leadership, other teams, or vendors for this to succeed? `[6-D]`
29. Who, outside the QA team, has veto power or will need to be convinced? `[6-D] [8]`
30. What's the team's appetite for change right now — burned out, energized, somewhere in between? `[6-R]`

### Security & data governance (mandatory — these constraints often dictate what's even possible)

31. What's the data classification of your test artifacts — test scripts, fixtures, recorded sessions, defect attachments? Anything regulated, PII, or customer-derived? `[6-S]`
32. If a tool needed to read your test code or test data to do its job, who would have to approve that — InfoSec, Legal, Privacy, Platform/Infra? Is there an existing approved-tooling list it would have to fit within? `[6-S] [8]`
33. Have prior tooling initiatives been blocked or scoped down by governance review? What was the constraint? `[6-S] [6-R]`

### Failure-mode questions (probe the proposed change, not just current pain)

34. If we adopted an AI-assisted approach and it produced confident but wrong results — hallucinated tests, false-pass verifications — how would you expect that to surface, and how long before you caught it? `[6-R]`
35. What does "this initiative failed and we pulled it back" look like — what would you need to see to call it? `[6-R] [7]`

---

## 8. Wrap-up (2 min)

36. Which of your QA engineers should I prioritize interviewing, and why?
37. What did I not ask about that I should have?

---

## Follow-up Session (recommended, +30 min after IC interviews)

- Review aggregated IC findings
- **Reconcile metric divergence** between Lead and IC reports (don't average — investigate the gap)
- Validate or correct baseline metrics; promote estimated metrics to tracked only if real instrumentation exists
- Pressure-test draft target state and AI integration points (this is where interpretation belongs — not the first session)
- Catch any aspirational metrics or failure-mode questions deferred from §3.b / §7 above
- Confirm the explicit ask for §8 of the brief