# Feature Catalogue and Priorities

**P0:** required for hackathon MVP. **P1:** valuable if time permits. **P2:** post-hackathon.

## Workspace and inputs
- P0: single-user analysis workspace, privacy notice, pasted job description.
- P0: PDF/DOCX resume upload and validation.
- P0: one public GitHub URL or ZIP upload.
- P1: save and compare multiple analyses.
- P2: accounts, teams and collaboration.

## Job description intelligence
- P0: extract role, seniority cues, required/optional skills and responsibilities.
- P0: normalize common aliases such as JS/JavaScript.
- P0: allow user to edit extracted requirements.
- P1: explain why requirements matter.
- P2: browser extension and job-board integrations.

## Resume and repository understanding
- P0: extract resume skills and experience claims.
- P0: parse README, package manifests and selected source files.
- P0: safe archive extraction and file allowlist.
- P0: bounded evidence records with path and line range.
- P1: language-aware AST analysis for Python and JS/TS.
- P2: private repositories via least-privilege OAuth.

## Evidence mapping
- P0: map each requirement to resume/project evidence.
- P0: four status values and clear uncertainty.
- P0: validate all evidence IDs on the server.
- P0: store model/provider and prompt version metadata.
- P1: evaluate mapping quality against hand-labelled examples.
- P2: team review and annotations.

## Preparation plan
- P0: prioritize gaps using job importance and evidence status.
- P0: 3–7 tasks with effort estimates and measurable success criteria.
- P1: completion tracking and re-analysis.
- P2: spaced repetition and course integrations.

## Mock interview
- P0: generate 5–8 questions from the job and validated evidence.
- P0: one question per turn.
- P0: rubric for correctness, specificity, trade-offs, evidence alignment and communication.
- P1: follow-up questions and timed mode.
- P2: voice and live coding.

## Reports and operations
- P0: summary, evidence matrix, gaps, preparation plan and limitations.
- P0: clickable evidence drawer and clear loading/error states.
- P0: deletion and temporary-file cleanup.
- P0: tests for parsing, schema validation and unsafe input.
- P1: Markdown/PDF export, rate limiting, basic metrics.
- P2: billing and enterprise controls.

## Explicitly out of scope
Automated job applications, mass job-board scraping, private repo access, code execution, training a foundation model, and ranking candidates for employers.
