# Product Specification

## Problem and target user
Software developers applying for a role need to know which job requirements they can substantiate with their resume and projects, and what they should prepare next. Generic AI tools can repeat claims without showing evidence.

## Primary user story
“As a developer, I want to compare a job description with my resume and project repository, see evidence for each skill match, and get a practical preparation plan without exaggerating my experience.”

## Inputs
- Resume: text-based PDF or DOCX, with file size/page limits.
- Job description: pasted text for the reliable MVP path.
- Project source: public GitHub URL or ZIP upload.
- Optional: interview date, daily preparation time, target focus.

## Outputs
1. Job brief: role, seniority cues, required/optional skills, responsibilities.
2. Evidence matrix: requirement, status, rationale, source excerpt, file/path and line range.
3. Gap plan: prioritized practice tasks, estimated effort and completion checks.
4. Mock interview: question, answer, rubric feedback and grounded evidence.
5. Later: Markdown/PDF export.

## User flow
1. Create analysis and paste job description.
2. Upload resume.
3. Add public repository URL or ZIP.
4. Review extracted requirements and correct them.
5. Run evidence analysis.
6. Inspect evidence matrix and source excerpts.
7. Generate preparation plan.
8. Complete a project-specific mock interview.
9. Save or delete the analysis.

## Status vocabulary
- `demonstrated`: direct, validated supporting evidence exists.
- `partial_evidence`: relevant evidence exists but is incomplete.
- `not_demonstrated`: insufficient evidence was found in supplied materials.
- `needs_review`: ambiguity or extraction uncertainty needs human review.

## Acceptance criteria
- One analysis can run end-to-end without manual developer intervention.
- Parsing failures are clearly reported.
- Unsafe/oversized archives are rejected.
- Every demonstrated/partial mapping has a validated evidence pointer.
- Invalid model JSON is retried once or shown as an actionable error.
- Users can delete an analysis and its uploaded files.
- Tests use synthetic or public sample data.
