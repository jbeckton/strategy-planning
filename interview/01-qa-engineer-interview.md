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
6. What tools and frameworks did you use? Where did you hit friction? `[3a] [3c]`
7. How long did it take from "I have the requirement" to "the test is checked in and running"? `[3d]`
8. What % of your authored tests need rework after first review or first run? `[3d] [3c]`
9. What's the most frustrating part of authoring? `[3c]`

---

## 3. Test Data Management (8 min)

10. How do you get test data — fixtures, generated, copied from prod, manual setup? `[3a]`
11. Walk me through a recent case where data setup blocked you. What did it take to unblock? `[3c]`
12. Roughly what fraction of test failures turn out to be data issues rather than real defects? `[3d] [3c]`
13. Is there test data you wish existed but doesn't? `[3c]`

---

## 4. Test Run Orchestration (5 min)

14. Who triggers test runs — you, CI, release manager, all of the above? `[3a] [3b]`
15. When a run fails partway through, what happens? `[3a] [3c]`
16. How often do you re-run flaky tests? Roughly what % of failures are flake vs. real? `[3d] [3c]`

---

## 5. Verification — the deep dive (15 min)

> Spend the most time here. This is the section most likely to dominate the brief.

17. After a full test run finishes, walk me through exactly what you do to determine pass/fail. `[3a]`
18. How long does verification of one full run take you, end to end? `[3d]`
19. How many runs/week do you verify? `[3d]`
20. What signals do you look at — logs, screenshots, video, diffs, console output, network, all of these? `[3a]`
21. What does a "false positive" look like — a test that fails but shouldn't count? How often? `[3c] [3d]`
22. What does a "false negative" look like — a test that passes but missed a real issue? How often? `[3c] [3d]`
23. When you find a real defect during verification, what's the next step, and how long does that take? `[3a]`
24. What's the most tedious part of verification? The most error-prone? `[3c]`
25. If you had to delegate verification to someone unfamiliar, what's the part you'd be most worried about them getting wrong? `[3c] [6-R]`

---

## 6. Pain Point Prioritization (5 min)

26. If you could remove one task from your week permanently, what would it be and why? `[3c]`
27. What part of your job do you find genuinely engaging — what would you want to keep doing? `[5]` `[4a]`
28. Where do you feel like a bottleneck for the team? Where does the team feel like a bottleneck for you? `[3c]`

---

## 7. Future State — keep open-ended, no leading on AI (5 min)

29. Imagine your job two years from now in an ideal world. What's different? `[4a]`
30. _(Only after #29)_ Have you used any AI-assisted tooling — Copilot, ChatGPT, Cursor — for QA work? What worked, what didn't? `[4b] [6-R]`
31. What part of your job do you think AI **should not** be doing, and why? `[6-R]`

---

## 8. Wrap-up (2 min)

32. Who else on the team should I talk to, and why?
33. What did I not ask about that I should have?
34. Anything you want me to keep confidential vs. anything you want surfaced to leadership?

---

## Interviewer Probes (use as needed)

- "Can you give me a specific recent example?"
- "And then what happens?"
- "How long did that step take, roughly?"
- "How often does that happen — daily, weekly, occasionally?"
- "What would have to be true for that to go faster?"
- **Tracked vs. estimated:** "Is that number something you've seen reported on a dashboard or ticket, or is it your own estimate?" (Apply after every numeric answer — Q3, Q7, Q8, Q12, Q16, Q18–22. The brief's §3d Confidence column depends on this distinction.)