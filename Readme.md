# ProofPath AI — Working MVP Scaffold

ProofPath AI maps job requirements to evidence in a resume and a public code repository. It produces a skill evidence report, a focused preparation plan and practice interview questions. It avoids opaque employability scores and distinguishes “not demonstrated in supplied materials” from “does not know”.

## What works in this first build
- Next.js + React + TypeScript web interface.
- FastAPI backend with SQLite persistence (chosen for low-friction local development; PostgreSQL remains the planned deployment target).
- PDF/DOCX/TXT resume extraction.
- Public GitHub repository ingestion or project ZIP upload, with file/path/size filters.
- Skill extraction and deterministic evidence mapping.
- Click-through evidence excerpts, gap plan and mock-interview practice feedback.
- Sample report mode for exploring UI without uploads.
- Optional Meta Model API enhancement for preparation plans and question wording. Core local analysis works without an API key.

## Run locally
Requirements: Python 3.11+ (3.12 recommended), Node.js 20+ and npm.

1. Open a terminal in this project folder.
2. Run `./run-local.sh` (it creates a Python virtual environment and installs dependencies).
3. Open `http://localhost:3000`.
4. The API docs are at `http://localhost:8000/docs` and health check at `http://localhost:8000/health`.

If you prefer to start services separately:

```bash
# Terminal 1 — API
cd services/api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 — web UI
cd apps/web
npm install
npm run dev
```

## Optional Meta Model API
The local rules engine works without keys. To optionally use Meta Model API to improve the preparation plan and interview question wording:

1. Obtain a key through the official Meta Model API developer flow.
2. Put the key in `services/api/.env` as `MODEL_API_KEY=...`.
3. Set `USE_META_MODEL=true` and (optionally) `META_MODEL_ID=muse-spark-1.3`.
4. Restart the API.

The integration uses `https://api.meta.ai/v1/chat/completions` with Bearer authentication and a configurable Muse model ID. Confirm current model access/limits in the [official Meta Model API docs](https://dev.meta.ai/docs/overview). Resume excerpts and the job description are sent to Meta when this optional feature is enabled. Do not enable it for documents you are not comfortable sharing with that provider.

## Docker Compose
Copy `services/api/.env.example` to `services/api/.env` first, then run:

```bash
docker compose up --build
```

Open `http://localhost:3000`. API docs: `http://localhost:8000/docs`.

## Tests
```bash
cd services/api
pip install -r requirements.txt
pip install pytest
PYTHONPATH=. pytest -q
```

## Current limitations — intentionally honest
- Skill extraction and evidence statuses currently use rules and heuristics; this is a working baseline, not a validated skill assessment.
- The analyzer may miss unusual wording or over-read incidental mentions. Always inspect cited source excerpts.
- Repository evidence indicates text/code references, not code ownership, runtime correctness or expert mastery.
- SQLite is used for a low-friction initial demo. PostgreSQL and a managed job queue can replace it after the end-to-end workflow stabilizes.
- Interview feedback is rubric-based heuristics and should be treated as practice guidance, not a definitive score.
- Public GitHub API can rate-limit unauthenticated requests; uploading a ZIP is the fallback.
- No private repository OAuth, accounts, production multi-tenancy, resume export or code execution.

## Security notes
Inputs are untrusted. The app only parses selected text files and never executes uploaded code. ZIP files are checked for path traversal and bounded by size/count limits. Public repository URLs are restricted to GitHub. For any public deployment, add authentication, per-user authorization, stricter request throttling, upload lifecycle deletion and a security review.

## Repo layout
```text
apps/web/            Next.js UI
services/api/app/    FastAPI routes, ingestion and analysis
services/api/tests/  Backend test suite
docs/                Original system design documentation
```
