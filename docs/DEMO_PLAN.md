# Demo Plan and Evaluation

## Story
A developer is applying for a Full Stack Engineer role. Their resume mentions React, Node.js and databases, but they want to know which requirements their project actually demonstrates and what to prepare next.

## Three-minute demo
1. 0:00–0:20 — Explain why generic AI career tools can make unsupported claims.
2. 0:20–0:45 — Submit synthetic resume, job description and sample repo.
3. 0:45–1:20 — Open a skill mapping and show real file/line evidence.
4. 1:20–1:45 — Show “not demonstrated in supplied materials” and explain the distinction.
5. 1:45–2:15 — Show a prioritized plan with effort and completion checks.
6. 2:15–2:45 — Answer one project-specific interview question and show grounded feedback.
7. 2:45–3:00 — Highlight traceability, safe repo analysis and no unsupported claims.

## Metrics
- Evidence citation validity: target 100%.
- Unsupported `demonstrated` mappings: target 0 in test set.
- Requirement extraction precision/recall on manually labelled examples.
- Parsing success on supported fixtures.
- Reviewer rating of plan actionability.
- Analysis latency and model cost.

## Test fixtures
Create synthetic MERN, Python/FastAPI and React job descriptions, resumes and safe sample repos. Include a negative control where a technology appears only in a dependency manifest, so the app does not overstate hands-on experience.

## Failure plan
- Model outage: use clearly labelled deterministic demo mode.
- GitHub outage: use local ZIP fixture.
- Resume parse failure: show actionable error and optionally allow pasted text.
- Invalid evidence pointer: block the mapping from `demonstrated`.
