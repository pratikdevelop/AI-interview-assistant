# API Contract (MVP)

Base path: `/api/v1`. Use FastAPI/Pydantic models and generate OpenAPI. IDs are opaque UUIDs.

## `GET /health`
```json
{"status":"ok","service":"proofpath-api","version":"0.1.0"}
```

## `POST /analyses`
Multipart fields: `job_description`, `resume_file`, and exactly one of `github_url` or `repository_zip`.

Response `202 Accepted`:
```json
{"analysis_id":"uuid","status":"processing","stage":"input_validation","poll_url":"/api/v1/analyses/uuid"}
```

## `GET /analyses/{analysis_id}`
Processing:
```json
{"analysis_id":"uuid","status":"processing","stage":"evidence_mapping","stage_message":"Comparing requirements with indexed project evidence"}
```

Completed response shape:
```json
{
  "analysis_id":"uuid",
  "status":"completed",
  "job_brief":{"role_title":"Full Stack Developer","requirements":[{"requirement_id":"req_1","name":"React","importance":"must_have"}]},
  "evidence_matrix":[{"requirement_id":"req_1","skill":"React","status":"demonstrated","rationale":"Found in resume and project source.","evidence_ids":["ev_14"],"confidence":"medium","limitations":[]}],
  "top_gaps":[],
  "preparation_plan":[],
  "limitations":["Analysis is limited to submitted materials."]
}
```

## Other endpoints
- `GET /analyses/{analysis_id}/evidence/{evidence_id}` — bounded excerpt and source metadata after ownership check.
- `POST /analyses/{analysis_id}/plan` — body: `{"daily_minutes":45,"days_available":7,"focus":"backend_interview"}`.
- `POST /analyses/{analysis_id}/interviews` — create session.
- `GET /interviews/{interview_id}` — current question/status.
- `POST /interviews/{interview_id}/answers` — body: `{"question_id":"q_1","answer_text":"..."}`.
- `DELETE /interviews/{interview_id}` — delete session.
- `DELETE /analyses/{analysis_id}` — block access and schedule deletion; return `204`.

## Error shape
```json
{"error":{"code":"UNSUPPORTED_FILE_TYPE","message":"Upload a text-based PDF or DOCX file.","trace_id":"opaque-id"}}
```

## API rules
Check ownership on every endpoint. Never return stack traces, provider keys or internal paths. Use 413 for size limits, 422 for validation, 404 for unavailable/not-owned resources, 429 for rate limits, 502/503 for provider failure. Server validates evidence references and status rules.
