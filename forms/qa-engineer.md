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
- Please do not modify the format of this document or the questions.
- You may use markdown in your response as long as it does not include the same markdown used to delineate sections of this form, such as headings (`###`).
- Concrete examples ("the last test I wrote", "Tuesday's release", "about 4 hours") are far more useful than generalities.
- For questions with a **Source of any number you give** prompt — that's any question about counts, durations, percentages, or rates — please label your number as `Tracked` (cite the dashboard, ticket, or report it came from), `Estimated` (your recall or gut), or `Not measured`. Rough estimates are welcome; we just need to know it's an estimate so the brief reports it accurately.
- When you're done: fill in the frontmatter at the top, save the file, and send it back.

---

## Warm-up & Context

### Q1. How long have you been on the QA team, and what was your role before?

**Your response:**

_(write your answer here)_

### Q2. What kind of testing do you primarily own — UI, API, integration, performance, exploratory? `[3b]`

**Your response:**

_(write your answer here)_

### Q3. On a typical day this past week, roughly what % of your time went to authoring vs. execution vs. verification vs. everything else? `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

## Test Authoring

### Q4. Walk me through the most recent test or test suite you authored, start to finish. `[3a]`

**Your response:**

_(write your answer here)_

### Q5. Where did the requirements or acceptance criteria come from? How clear were they? `[3c]`

**Your response:**

_(write your answer here)_

### Q6. What tools and frameworks did you use? Where did you hit friction? `[3a]` `[3c]`

**Your response:**

_(write your answer here)_

### Q7. How long did it take from "I have the requirement" to "the test is checked in and running"? `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q8. What % of your authored tests need rework after first review or first run? `[3d]` `[3c]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q9. What's the most frustrating part of authoring? `[3c]`

**Your response:**

_(write your answer here)_

## Test Data Management

### Q10. How do you get test data — fixtures, generated, copied from prod, manual setup? `[3a]`

**Your response:**

_(write your answer here)_

### Q11. Walk me through a recent case where data setup blocked you. What did it take to unblock? `[3c]`

**Your response:**

_(write your answer here)_

### Q12. Roughly what fraction of test failures turn out to be data issues rather than real defects? `[3d]` `[3c]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q13. Is there test data you wish existed but doesn't? `[3c]`

**Your response:**

_(write your answer here)_

## Test Run Orchestration

### Q14. Who triggers test runs — you, CI, release manager, all of the above? `[3a]` `[3b]`

**Your response:**

_(write your answer here)_

### Q15. When a run fails partway through, what happens? `[3a]` `[3c]`

**Your response:**

_(write your answer here)_

### Q16. How often do you re-run flaky tests? Roughly what % of failures are flake vs. real? `[3d]` `[3c]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

## Verification — the deep dive

### Q17. After a full test run finishes, walk me through exactly what you do to determine pass/fail. `[3a]`

**Your response:**

_(write your answer here)_

### Q18. How long does verification of one full run take you, end to end? `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q19. How many runs/week do you verify? `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q20. What signals do you look at — logs, screenshots, video, diffs, console output, network, all of these? `[3a]`

**Your response:**

_(write your answer here)_

### Q21. What does a "false positive" look like — a test that fails but shouldn't count? How often? `[3c]` `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q22. What does a "false negative" look like — a test that passes but missed a real issue? How often? `[3c]` `[3d]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q23. When you find a real defect during verification, what's the next step, and how long does that take? `[3a]`

**Your response:**

_(write your answer here)_

### Q24. What's the most tedious part of verification? The most error-prone? `[3c]`

**Your response:**

_(write your answer here)_

### Q25. If you had to delegate verification to someone unfamiliar, what's the part you'd be most worried about them getting wrong? `[3c]` `[6-R]`

**Your response:**

_(write your answer here)_

### Q26. In the past quarter, roughly how many production defects came from features your team had already tested and signed off on? Of those, were the relevant tests passing — meaning the suite ran green and missed it — or were the defects in areas your tests didn't cover? `[3d]` `[3c]`

**Your response:**

_(write your answer here)_

**Source of any number you give:** `Tracked` (cite dashboard/ticket/report) / `Estimated` (your recall) / `Not measured`

_(your source here)_

### Q27. If a significant portion of your test suite were generated or maintained by automated tooling, what would maintaining it look like as the codebase evolves — easier, harder, or about the same as today, and why? `[6-R]`

**Your response:**

_(write your answer here)_

## Pain Point Prioritization

### Q28. If you could remove one task from your week permanently, what would it be and why? `[3c]`

**Your response:**

_(write your answer here)_

### Q29. What part of your job do you find genuinely engaging — what would you want to keep doing? `[5]` `[4a]`

**Your response:**

_(write your answer here)_

### Q30. Where do you feel like a bottleneck for the team? Where does the team feel like a bottleneck for you? `[3c]`

**Your response:**

_(write your answer here)_

## Future State — keep open-ended

### Q31. Imagine your job two years from now in an ideal world. What's different? `[4a]`

**Your response:**

_(write your answer here)_

## Wrap-up

### Q32. Who else on the team should I talk to, and why?

**Your response:**

_(write your answer here)_

### Q33. What did I not ask about that I should have?

**Your response:**

_(write your answer here)_

### Q34. Anything you want me to keep confidential vs. anything you want surfaced to leadership?

**Your response:**

_(write your answer here)_
