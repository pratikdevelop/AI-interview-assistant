# Security, Privacy and Responsible AI

## Threat model
Resumes, job descriptions, ZIP archives, repository URLs, repository text and model output are untrusted. Repository text may contain prompt injection; treat it as data, never instructions.

## Upload controls
- Validate file signature and MIME, not extension alone.
- Bound bytes, pages, expanded archive size, file count, per-file size, decoded characters and processing time.
- Reject encrypted/unreadable files clearly.
- Reject ZIP path traversal, absolute paths, symlinks and unsafe nested archives.
- Exclude `.env*`, private keys, credentials, binaries, dependency folders, build outputs and generated files.
- Never execute source code, install dependencies, or run scripts from uploads.
- Store uploads outside web root; clean up on expiry and deletion.

## GitHub and SSRF controls
- Allow only expected HTTPS GitHub hosts and endpoints.
- Reject URL credentials, unexpected ports, IP-literal hosts and encoded-host tricks.
- Validate every redirect or disable redirects.
- Limit response size, download time, redirect count and repository file count.
- Do not fetch arbitrary links, submodules or external assets by default.

## AI and evidence integrity
- Separate trusted system instructions from untrusted document content.
- Request structured output with evidence IDs, not invented file paths.
- Validate schema, IDs, excerpt matching and output length server-side.
- A `demonstrated` mapping requires at least one validated evidence record.
- If support is weak, use `partial_evidence`, `not_demonstrated` or `needs_review`.
- Separate source facts from model inferences and recommendations.

## Privacy
- Explain which text is sent to the model provider.
- Send minimal relevant excerpts rather than entire repositories where practical.
- Keep provider keys server-side; never log resume text, tokens or interview answers.
- Provide deletion and clear retention for temporary uploads.
- Before public launch add authentication, ownership checks, rate limits, abuse controls and a privacy policy.

## Fairness
This is a career preparation tool, not an employer screening system. “Not demonstrated” is not proof the user lacks a skill. Avoid opaque employability scores and fabricated resume metrics.

## Tests
Cover path traversal, ZIP bombs, prompt injection, invented evidence IDs, malformed model output, oversized responses and unauthorized record access.
