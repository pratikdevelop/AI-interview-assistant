# Data Model

PostgreSQL stores structured records. Raw uploads live in private temporary/object storage; DB stores opaque key, checksum, content type, size and expiry.

## `analyses`
`id`, `owner_key`, `status`, `stage`, `stage_message`, `error_code`, `job_description_text`, timestamps, `pipeline_version`, `prompt_version`.

## `uploads`
`id`, `analysis_id`, `kind` (`resume`, `repository_zip`), `storage_key`, sanitized filename, content type, size, SHA-256, expiry and deletion timestamps.

## `requirements`
`id`, `analysis_id`, normalized skill, display name, type (`must_have`, `nice_to_have`, `responsibility`, `inferred_topic`), importance, source text, optional source offset, user-confirmed flag.

## `evidence_records`
`id`, `analysis_id`, source kind (`resume`, `repository`, `job_description`), source label, relative path, optional line range/page, bounded excerpt, content hash, extractor and version.

## `skill_mappings`
`id`, `analysis_id`, `requirement_id`, status, rationale, confidence, limitations JSON, created timestamp.

## `mapping_evidence`
Join table: `mapping_id`, `evidence_id`, composite primary key.

## `plan_steps`
`id`, `analysis_id`, position, title, reason, task, duration, success criteria JSON, status.

## `interview_sessions` / `interview_turns`
Sessions track analysis, status and rubric version. Turns track question, answer, feedback JSON, evidence IDs and position.

## `model_runs`
Store analysis, stage, provider/model ID, prompt version, status, duration, token counts, error code and timestamp. Do not store full prompts or resume text in routine logs.

## Constraints and retention
Index analyses by `(owner_key, created_at DESC)`, requirements by `(analysis_id, normalized_skill)`, and use foreign keys with predictable deletion. Add explicit retention defaults, upload TTL and deletion cleanup before public launch.
