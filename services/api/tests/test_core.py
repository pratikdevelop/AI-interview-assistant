import io
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.analyzer import build_report, extract_requirements
from app.ingestion import extract_resume, ingest_zip


def test_extract_requirements_finds_common_skills():
    requirements = extract_requirements("We require React, TypeScript, PostgreSQL and REST APIs experience.")
    names = {item["name"] for item in requirements}
    assert {"React", "TypeScript", "PostgreSQL", "REST APIs"}.issubset(names)


def test_resume_txt_extraction():
    text = extract_resume("resume.txt", b"Software developer with React, Python and API experience." * 2)
    assert "Software developer" in text


def test_zip_ingestion_rejects_path_traversal_and_reads_source():
    memory = io.BytesIO()
    with zipfile.ZipFile(memory, "w") as zf:
        zf.writestr("../escape.py", "should not be read")
        zf.writestr("project/main.py", "from fastapi import FastAPI\napp = FastAPI()\n\n@app.get('/health')\ndef health():\n    return {'ok': True}\n")
    evidence, label = ingest_zip(memory.getvalue())
    assert evidence
    assert all(".." not in (item.relative_path or "") for item in evidence)
    assert "project/main.py" in {item.relative_path for item in evidence}


def test_report_does_not_call_missing_skill_proven():
    job = "Required experience with React, Docker and PostgreSQL."
    resume = "I built React interfaces for a dashboard application." * 2
    evidence = [{"id":"ev_100", "source_kind":"repository", "source_label":"repo", "relative_path":"src/App.tsx", "line_start":1, "line_end":4,
                "excerpt":"import React, { useState } from 'react';\nexport default function App(){ return <div /> }", "evidence_kind":"project_file"}]
    report = build_report(job, resume, evidence, "sample", 45, 7)
    mapping = {item["skill"]:item for item in report["evidence_matrix"]}
    assert mapping["React"]["status"] in {"demonstrated", "partial_evidence"}
    assert mapping["Docker"]["status"] == "not_demonstrated"
