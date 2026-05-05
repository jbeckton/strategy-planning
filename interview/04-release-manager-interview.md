# Interview Script — Release Manager

**Persona:** Owner of release cadence, gate decisions, and go/no-go calls
**Duration:** 30 minutes
**Brief sections informed:** 3a, 3c, 3d, 4a, 5, 6-R

---

## 1. Warm-up & Context (3 min)

1. What's the current release cadence — weekly, bi-weekly, monthly, on-demand?
2. How many releases have you shipped in the last quarter? How many were on time? `[3d]`

---

## 2. The QA Gate (10 min)

3. Walk me through what has to be true for you to greenlight a release. `[3a]`
4. What's the typical sequence of QA artifacts you wait on before approving? `[3a]`
5. How long, on average, does the QA gate add to your release timeline? `[3d]`
6. What % of releases get held at the QA gate beyond their planned window? `[3d]`
7. When QA flags an issue at the gate, how often is it a true blocker vs. something that gets waived? `[3c] [3d]`

---

## 3. Risk Signals and Trust (8 min)

8. How much confidence do you have in QA's pass/fail signal at the gate? `[3c]`
9. What signals do you look at beyond pass/fail — escape rate trends, flake rate, coverage? `[3a] [3d]`
10. _(Optional if time tight)_ When a release goes wrong post-deploy, how often was there an upstream signal that should have caught it? `[3c]`
11. What's the typical hotfix rate per release, and what's the most common root cause? Tracked or estimated? `[3d] [3c]`

---

## 4. Cadence and Pressure (5 min)

12. Where does release pressure most often conflict with QA thoroughness? `[3c]`
13. _(Optional)_ Have you ever shipped knowing QA wasn't fully complete? What forced that decision? `[3c]`
14. If the QA gate were 50% faster with the same defect catch rate, what would you do with the recovered time? `[5]`

---

## 5. Aspirational Future State (3 min)

15. What does a healthy release cadence look like from your seat? `[4a]`
16. Where would faster, more reliable QA signal change your job most? `[5]`
17. What role, if any, should new tooling or automation play in the gate decision — and what would you need to trust it? (Don't presuppose AI; if AI comes up, follow up on what specifically would and wouldn't be acceptable.) `[4b] [6-R]`

---

## 6. Wrap-up (1 min)

18. What did I not ask about that I should have?