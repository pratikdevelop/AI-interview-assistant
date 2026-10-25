from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .analyzer import build_report, maybe_enrich_with_meta
from .ingestion import MAX_ARCHIVE_BYTES, MAX_RESUME_BYTES, extract_resume, ingest_github, ingest_zip, evidence_to_dict

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("PROOFPATH_DATA_DIR", str(APP_DIR.parent / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "proofpath.sqlite3"

app = FastAPI(title="ProofPath AI API", version="0.1.0", description="Evidence-backed developer career copilot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(","),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS analyses (
          id TEXT PRIMARY KEY, status TEXT NOT NULL, stage TEXT, created_at TEXT NOT NULL,
          request_json TEXT NOT NULL, report_json TEXT, error_message TEXT
        )""")
        conn.commit()


init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "proofpath-api", "version": "0.1.0", "mode": "meta-enabled" if os.getenv("USE_META_MODEL", "false").lower() in {"1", "true", "yes"} and os.getenv("MODEL_API_KEY") else "local-rules"}


@app.get("/api/v1/demo")
def demo_report():
    """Returns a clearly labelled sample report without any uploads or API credentials."""
    sample_job = "Full Stack Developer. Requirements: React, TypeScript, Node.js, REST APIs, PostgreSQL, Docker, testing, and LLM/RAG experience."
    sample_resume = "Software developer with experience building React and TypeScript interfaces, Node.js APIs, Python AI prototypes, and PostgreSQL-backed applications."
    sample_evidence = [
        {"id":"ev_100", "source_kind":"repository", "source_label":"Demo repository", "relative_path":"src/App.tsx", "line_start":1, "line_end":22, "excerpt":"import React, { useState } from 'react';\nexport default function App() {\n const [query, setQuery] = useState('');\n return <main><input value={query} onChange={(e) => setQuery(e.target.value)} /></main>;\n}", "evidence_kind":"project_file"},
        {"id":"ev_110", "source_kind":"repository", "source_label":"Demo repository", "relative_path":"api/server.py", "line_start":1, "line_end":22, "excerpt":"from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}", "evidence_kind":"project_file"},
        {"id":"ev_120", "source_kind":"repository", "source_label":"Demo repository", "relative_path":"package.json", "line_start":1, "line_end":20, "excerpt":"{\"dependencies\": {\"react\": \"^19.0.0\", \"typescript\": \"^5.0.0\"}}", "evidence_kind":"project_file"},
    ]
    report = build_report(sample_job, sample_resume, sample_evidence, "Sample repository — synthetic demo data", 45, 7)
    report["analysis_mode"] = "demo"
    return {"analysis_id":"demo", "status":"completed", "created_at":datetime.now(timezone.utc).isoformat(), **report}


@app.post("/api/v1/analyses", status_code=201)
async def create_analysis(
    job_description: str = Form(..., min_length=30, max_length=20000),
    resume_file: UploadFile = File(...),
    github_url: Optional[str] = Form(None),
    repository_zip: Optional[UploadFile] = File(None),
    daily_minutes: int = Form(45, ge=15, le=240),
    days_available: int = Form(7, ge=1, le=30),
):
    if bool(github_url and github_url.strip()) == bool(repository_zip and repository_zip.filename):
        raise HTTPException(422, "Provide exactly one project source: a public GitHub URL or a repository ZIP.")
    try:
        resume_bytes = await resume_file.read(MAX_RESUME_BYTES + 1)
        resume_text = extract_resume(resume_file.filename or "resume.pdf", resume_bytes)
        if github_url and github_url.strip():
            evidence_obj, source_label = await ingest_github(github_url.strip())
        else:
            zip_bytes = await repository_zip.read(MAX_ARCHIVE_BYTES + 1)  # type: ignore[union-attr]
            evidence_obj, source_label = ingest_zip(zip_bytes)
        evidence = evidence_to_dict(evidence_obj)
        report = build_report(job_description, resume_text, evidence, source_label, daily_minutes, days_available)
        report = await maybe_enrich_with_meta(report, job_description, resume_text)
        analysis_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        request_summary = {"job_description": job_description[:20000], "resume_filename": (resume_file.filename or "resume")[:200], "repository_summary": source_label,
                           "daily_minutes":daily_minutes, "days_available":days_available}
        with get_db() as conn:
            conn.execute("INSERT INTO analyses (id,status,stage,created_at,request_json,report_json) VALUES (?,?,?,?,?,?)",
                         (analysis_id, "completed", "complete", created_at, json.dumps(request_summary), json.dumps(report)))
            conn.commit()
        return {"analysis_id":analysis_id, "status":"completed", "created_at":created_at, **report}
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        trace_id = str(uuid.uuid4())[:8]
        # Keep internal details out of the public response.
        print(f"[{trace_id}] analysis failed: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail=f"Analysis could not be completed. Try again or use a different repository source. Reference: {trace_id}") from exc


@app.get("/api/v1/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Analysis not found.")
    return {"analysis_id":row["id"], "status":row["status"], "stage":row["stage"], "created_at":row["created_at"], **json.loads(row["report_json"] or "{}")}


@app.delete("/api/v1/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: str):
    with get_db() as conn:
        cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(404, "Analysis not found.")
    return None


class InterviewAnswerRequest(BaseModel):
    analysis_id: str = Field(min_length=1, max_length=80)
    question_id: str = Field(min_length=1, max_length=40)
    answer_text: str = Field(min_length=1, max_length=12000)


@app.post("/api/v1/interviews/answer")
def evaluate_interview_answer(payload: InterviewAnswerRequest):
    if payload.analysis_id == "demo":
        report = demo_report()
    else:
        with get_db() as conn:
            row = conn.execute("SELECT report_json FROM analyses WHERE id = ?", (payload.analysis_id,)).fetchone()
        if not row:
            raise HTTPException(404, "Analysis not found.")
        report = json.loads(row["report_json"] or "{}")
    questions = report.get("interview_questions", [])
    question = next((q for q in questions if q.get("id") == payload.question_id), None)
    if not question:
        raise HTTPException(404, "Interview question not found for this analysis.")
    answer = payload.answer_text.strip()
    words = re.findall(r"\b[\w+#.-]+\b", answer)
    lower = answer.lower()
    has_example = any(token in lower for token in ["for example", "for instance", "in my project", "i built", "i implemented", "we used", "because"])
    has_tradeoff = any(token in lower for token in ["trade-off", "tradeoff", "trade off", "instead", "alternative", "limitation", "latency", "cost", "maintainability"])
    has_validation = any(token in lower for token in ["test", "verified", "monitor", "metric", "validated", "benchmark", "logs", "error rate"])
    scores = {
        "technical_specificity": min(5, 1 + len(words) // 35),
        "concrete_example": 4 if has_example else (2 if len(words) >= 45 else 1),
        "tradeoff_awareness": 4 if has_tradeoff else 2,
        "validation": 4 if has_validation else 2,
        "communication": 4 if 45 <= len(words) <= 220 else (3 if len(words) >= 20 else 1),
    }
    improvements = []
    if len(words) < 45:
        improvements.append("Add a little more detail: explain the situation, your specific action, and the result.")
    if not has_example:
        improvements.append("Anchor the answer in one concrete project example and clearly state your personal contribution.")
    if not has_tradeoff:
        improvements.append("Mention one design trade-off or alternative you considered, and why you chose this approach.")
    if not has_validation:
        improvements.append("Explain how you tested or validated the result (tests, logs, metrics, or a reproducible check).")
    if not improvements:
        improvements.append("Good structure. Tighten the answer by naming the impact and one lesson you would carry into the next project.")
    strengths = []
    if has_example: strengths.append("You included language that points to a concrete example or implementation.")
    if has_tradeoff: strengths.append("You discussed a trade-off or alternative rather than only describing the happy path.")
    if has_validation: strengths.append("You described a way to validate the solution.")
    if len(words) >= 45: strengths.append("The answer has enough detail to evaluate; keep it focused on your personal contribution.")
    return {"question_id": payload.question_id, "word_count": len(words), "scores": scores, "strengths": strengths or ["You have a starting point; add a concrete example to make the answer more persuasive."], "improvements": improvements, "note": "This is structured practice feedback, not an objective assessment of your ability."}


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND", "message": str(exc.detail) if hasattr(exc, "detail") else "Not found"}})
