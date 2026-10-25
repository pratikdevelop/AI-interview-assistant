# Ten-Day Build Roadmap

Use this as an aggressive solo-developer plan. Verify hackathon cutoff and exact model access in participant materials.

## Phase 0 — Foundation
- Freeze scope: one JD + resume + public repository/ZIP → evidence report.
- Confirm Meta model API access, endpoint, supported model and limits.
- Create repository, frontend/backend skeleton, environment template and README.
- Add deterministic mock model provider.

**Exit:** frontend reaches FastAPI; `GET /health` works.

## Day 1 — Intake
Build UI and API contract; parse PDF/DOCX and pasted JD; persist analysis metadata.
**Exit:** user can submit resume/JD and preview parsed content.

## Day 2 — Repository ingestion
Support public GitHub and ZIP; implement limits, safe extraction, secret filters and evidence records.
**Exit:** safe sample repository indexed with stable paths/line ranges.

## Day 3 — Requirements
Extract and normalize skills; allow user confirmation/editing.
**Exit:** requirements are stable and schema-valid.

## Day 4 — Evidence mapping
Retrieve evidence; add model provider adapter; validate structured output, evidence IDs and status rules.
**Exit:** report has traceable evidence and no invented evidence IDs.

## Day 5 — Report and plan
Build overview, matrix, evidence drawer, top gaps and time-boxed plan.
**Exit:** intake → evidence report → plan works end-to-end.

## Day 6 — Mock interview
Generate 5–8 grounded questions; collect answers; evaluate with rubric.
**Exit:** complete interview demo.

## Day 7 — Reliability
Add e2e tests, deletion, timeouts, retries, clear errors and demo mode.
**Exit:** sample demo works even if provider is offline.

## Day 8 — Polish and evaluation
Responsive UI; test a hand-labelled set; measure citation validity, false demonstrated claims, parsing success and latency.
**Exit:** core quality checks pass.

## Day 9 — Deploy and rehearse
Deploy, check secrets/storage, record backup video, document setup and demo.
**Exit:** fresh-browser demo works.

## Day 10 — Submission buffer
Fix only high-impact issues; verify submission requirements, model attribution and deadline; submit early.

## Definition of done
- End-to-end demo with public sample repo.
- Every demonstrated skill links to valid evidence.
- At least 15 tests cover parsing, security, schema and status rules.
- Provider failure is handled with a clear message/demo fallback.
- Setup, configuration, limitations, retention and demo steps are documented.
