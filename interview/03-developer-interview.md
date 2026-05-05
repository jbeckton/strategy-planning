# Interview Script — Developer

**Persona:** Software engineer whose work passes through QA before release
**Duration:** 30–45 minutes
**Brief sections informed:** 3a, 3b, 3c, 3d, 4a, 5, 6-R

---

## 1. Warm-up & Context (3 min)

1. What part of the product do you work on, and how often does your code go through formal QA?
2. Who currently owns which kinds of tests on your team — and where are the boundaries fuzzy or contested? (Don't presuppose a dev-vs-QA split — describe it as it actually is.) `[3a] [3b]`

---

## 2. The QA Interface (8 min)

3. Walk me through what happens after you mark a feature ready for QA. `[3a]`
4. How do you find out a test failed or a defect was found? Through what channel, and how quickly? `[3a] [3d]`
5. When you get a defect report, how often does it have enough context for you to reproduce it without asking follow-up questions? `[3c] [3d]`
6. How many round-trips does a typical defect take before it's resolved? `[3d]`

---

## 3. Feedback Loop (8 min)

7. From "code committed" to "QA result back in your hands," what's the typical elapsed time? `[3d]`
8. What's the longest you've waited recently, and what caused the delay? `[3c]`
9. How often does QA feedback arrive after you've already context-switched to other work? `[3c] [3d]`
10. Where does the delay between dev-complete and release feel most painful from your side? `[3c]`

---

## 4. Self-Service & Trust (5 min)

11. Can you run the QA test suite locally before handing off, or do you have to wait for the QA team to run it? `[3a] [3c]`
12. How much do you trust the existing automated QA suite — does a green run mean you're confident to ship? `[3c] [3d]`
13. When tests fail, do you trust the failure or assume flake first? `[3c] [3d]`

---

## 5. Defect Escapes (5 min)

14. Think of the last bug that escaped to production. Walk me through it — what tier missed it, and why? `[3c]`
15. How often does that pattern repeat? `[3d]`
16. Where would you have wanted more or different testing? `[4a]`

---

## 6. Aspirational Future State (5 min)

17. In an ideal world, what does the dev → QA → release loop look like for you? `[4a]`
18. If the QA loop got faster and more reliable, what would *change in your delivery output* — fewer rework cycles, more features per sprint, less context-switching? Try to quantify. `[5]`
19. _(After #17–18)_ Where do you see AI fitting in, if anywhere? `[4b]`
20. What part of QA's work do you think AI should **not** be doing? `[6-R]`

---

## 7. Wrap-up (2 min)

21. What did I not ask about that I should have?
22. From your team's perspective, what would make the strongest case to leadership for changing this? `[1] [8]`