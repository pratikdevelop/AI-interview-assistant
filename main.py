from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json
import os
import re
import httpx
import asyncio
from pathlib import Path
import io

app = FastAPI(title="AI Interview Prep API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Serve frontend static files
# ─────────────────────────────────────────────
FRONTEND_DIR = Path(__file__).parent / "frontend"

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/", response_class=FileResponse, include_in_schema=False)
def serve_landing():
    """Serve landing page at root URL."""
    return FileResponse(FRONTEND_DIR / "landing.html")

@app.get("/app", response_class=FileResponse, include_in_schema=False)
def serve_app():
    """Serve the interview app."""
    return FileResponse(FRONTEND_DIR / "index.html")

# Note: The root() endpoint below is removed to avoid conflict with serve_landing()
# API info is available at /api endpoint instead

# ─────────────────────────────────────────────
# Load question bank
# ─────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "data" / "questions.json"
with open(DATA_PATH) as f:
    QUESTIONS_DB = json.load(f)

VALID_ROLES = list(QUESTIONS_DB.keys())

# ─────────────────────────────────────────────
# Docker Model Runner config
#
# Docker Model Runner exposes an OpenAI-compatible API.
# Default base URL:  http://localhost:12434/engines/v1
# Default model:     ai/llama3.2
#
# Override via environment variables if needed:
#   LLM_BASE_URL=http://localhost:12434/engines/v1
#   LLM_MODEL=ai/llama3.2
#
# If you're running Ollama instead:
#   LLM_BASE_URL=http://localhost:11434/v1
#   LLM_MODEL=llama3.2
# ─────────────────────────────────────────────
# Uses the same env vars as your other apps:
#   DOCKER_MODEL_URL=http://localhost:12434
#   DOCKER_MODEL=ai/llama3.2
# /engines/v1 path is appended automatically.
_base        = os.getenv("DOCKER_MODEL_URL", "http://localhost:12434").rstrip("/")
LLM_BASE_URL = f"{_base}/engines/v1"
LLM_MODEL    = os.getenv("DOCKER_MODEL", "ai/llama3.2")

# ─────────────────────────────────────────────
# Evaluation prompt
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior technical interviewer at a top tech company. 
You give honest, constructive feedback to help candidates improve.
You ALWAYS respond with valid JSON only — no markdown, no extra text, no backticks."""

USER_PROMPT = """Evaluate this interview answer.

Question: {question}

Candidate's Answer: {answer}

Respond with this exact JSON structure:
{{
  "strengths": ["strength 1", "strength 2"],
  "missing_points": ["missing point 1", "missing point 2"],
  "score": 7,
  "summary": "2-3 sentence overall assessment.",
  "ideal_answer_hint": "Brief pointer on what a 9-10 answer would include."
}}

Scoring guide:
1-3 → Major gaps, doesn't demonstrate understanding
4-6 → Partial understanding, missing key concepts  
7-8 → Good answer, covers most important points
9-10 → Excellent, complete, demonstrates deep understanding"""


# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────
class EvaluateRequest(BaseModel):
    question: str
    answer: str
    role: str = "general"


class EvaluateResponse(BaseModel):
    strengths: list[str]
    missing_points: list[str]
    score: int
    summary: str
    ideal_answer_hint: str


class HealthResponse(BaseModel):
    status: str
    model: str
    llm_url: str
    llm_reachable: bool


# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
@app.get("/api")
def api_info():
    """API information endpoint."""
    return {
        "message": "AI Interview Prep API is running 🚀",
        "model": LLM_MODEL,
        "llm_url": LLM_BASE_URL,
        "docs": "/docs",
    }

# Root endpoint removed - landing page served by serve_landing() above


@app.get("/health", response_model=HealthResponse)
async def health():
    """Check if the local LLM is reachable."""
    reachable = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{LLM_BASE_URL}/models")
            reachable = r.status_code == 200
    except Exception:
        pass

    return HealthResponse(
        status="ok" if reachable else "llm_unreachable",
        model=LLM_MODEL,
        llm_url=LLM_BASE_URL,
        llm_reachable=reachable,
    )


@app.get("/roles")
def get_roles():
    """Get all available interview roles/categories."""
    role_info = {
        "javascript":    {"id": "javascript",    "label": "JavaScript",    "description": "Core JS, async, closures, DOM",           "icon": "🟨"},
        "react":         {"id": "react",         "label": "React",         "description": "Hooks, state, performance, patterns",      "icon": "⚛️"},
        "typescript":    {"id": "typescript",    "label": "TypeScript",    "description": "Types, generics, utility types",           "icon": "🔷"},
        "python":        {"id": "python",        "label": "Python",        "description": "Core Python, OOP, concurrency",            "icon": "🐍"},
        "backend":       {"id": "backend",       "label": "Backend",       "description": "Node.js, FastAPI, REST, APIs",             "icon": "⚙️"},
        "sql":           {"id": "sql",           "label": "SQL",           "description": "Queries, joins, indexing, design",         "icon": "🗃️"},
        "dsa":           {"id": "dsa",           "label": "DSA",           "description": "Data structures & algorithms",             "icon": "🧠"},
        "system_design": {"id": "system_design", "label": "System Design", "description": "Scalable systems, architecture",          "icon": "🏗️"},
        "css":           {"id": "css",           "label": "CSS",           "description": "Layout, flexbox, grid, animations",        "icon": "🎨"},
        "git":           {"id": "git",           "label": "Git",           "description": "Branching, rebasing, workflows",          "icon": "🌿"},
        "devops":        {"id": "devops",        "label": "DevOps",        "description": "Docker, CI/CD, Kubernetes, cloud",        "icon": "🚀"},
        "networking":    {"id": "networking",    "label": "Networking",    "description": "HTTP, TCP/IP, DNS, protocols",             "icon": "🌐"},
        "os":            {"id": "os",            "label": "OS Concepts",   "description": "Processes, memory, scheduling",            "icon": "💻"},
        "behavioral":    {"id": "behavioral",    "label": "Behavioral",    "description": "HR & soft skills interview prep",         "icon": "🤝"},
    }
    for key in role_info:
        role_info[key]["question_count"] = len(QUESTIONS_DB.get(key, []))
    return {"roles": list(role_info.values())}


@app.get("/questions")
def get_questions(role: str, difficulty: str = None):
    """Get questions for a specific role, optionally filtered by difficulty."""
    if role not in QUESTIONS_DB:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role}' not found. Available: {VALID_ROLES}"
        )
    questions = QUESTIONS_DB[role]
    if difficulty:
        questions = [q for q in questions if q.get("difficulty") == difficulty]
    return {"role": role, "total": len(questions), "questions": questions}


@app.get("/questions/mixed")
def get_mixed_questions(count: int = 10, difficulty: str = None):
    """Get a mixed set of questions from all domains."""
    all_questions = []
    
    # Collect questions from all roles
    for role, questions in QUESTIONS_DB.items():
        for q in questions:
            # Add role info to question
            q_with_role = q.copy()
            q_with_role["role"] = role
            q_with_role["role_label"] = role.replace('_', ' ').title()
            all_questions.append(q_with_role)
    
    # Filter by difficulty if specified
    if difficulty:
        all_questions = [q for q in all_questions if q.get("difficulty") == difficulty]
    
    # Shuffle and limit
    import random
    random.shuffle(all_questions)
    selected_questions = all_questions[:count]
    
    return {
        "role": "mixed",
        "total": len(selected_questions),
        "questions": selected_questions,
        "domains_covered": list(set(q["role"] for q in selected_questions))
    }


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_answer(request: EvaluateRequest):
    """
    Evaluate a candidate's answer using the local Llama 3.2 model
    via Docker Model Runner's OpenAI-compatible /chat/completions endpoint.
    Includes automatic retry logic for robustness.
    """
    if not request.answer.strip():
        raise HTTPException(status_code=400, detail="Answer cannot be empty.")
    if len(request.answer.strip()) < 10:
        raise HTTPException(status_code=400, detail="Answer is too short. Please provide a more detailed response.")

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": USER_PROMPT.format(
            question=request.question,
            answer=request.answer,
        )},
    ]

    # Retry logic - try up to 3 times
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{LLM_BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json"},
                    json={
                        "model": LLM_MODEL,
                        "messages": messages,
                        "temperature": 0.2 + (attempt * 0.1),  # Gradually increase randomness
                        "max_tokens": 1200,
                    },
                )
        except httpx.ConnectError:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=503,
                    detail=(
                        f"Cannot reach local model at {LLM_BASE_URL}. "
                        "Make sure Docker Model Runner is running: "
                        "'docker model run ai/llama3.2'"
                    ),
                )
            await asyncio.sleep(1)  # Wait before retry
            continue
        except httpx.TimeoutException:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=504,
                    detail="Model took too long to respond after multiple attempts. Try a shorter answer or restart the model."
                )
            await asyncio.sleep(1)
            continue

        if response.status_code != 200:
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=502,
                    detail=f"Model returned HTTP {response.status_code}: {response.text[:200]}"
                )
            await asyncio.sleep(1)
            continue

        # Extract text from OpenAI-compatible response
        try:
            raw_content = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            if attempt == max_retries - 1:
                raise HTTPException(status_code=502, detail="Unexpected response format from model.")
            await asyncio.sleep(1)
            continue

        # Try to parse the response
        try:
            return _parse_llm_response(raw_content)
        except HTTPException as e:
            # If it's a JSON parsing error, retry
            if "valid JSON" in str(e.detail) and attempt < max_retries - 1:
                await asyncio.sleep(1.5)  # Slightly longer wait
                continue
            else:
                # Re-raise if it's the last attempt or not a JSON error
                raise

    # This should never be reached due to the loop logic, but just in case
    raise HTTPException(status_code=502, detail="Maximum retry attempts exceeded.")



# ─────────────────────────────────────────────
# Resume Review
# ─────────────────────────────────────────────
class ResumeRequest(BaseModel):
    resume: str
    job_description: str


class SessionSaveRequest(BaseModel):
    role: str
    questions: List[dict]
    answers: List[dict]
    scores: List[int]
    completed_at: Optional[str] = None


class SessionResponse(BaseModel):
    id: str
    role: str
    total_questions: int
    avg_score: float
    best_score: int
    completed_at: str


class HintRequest(BaseModel):
    question: str
    role: str


class CodeExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    test_cases: Optional[List[dict]] = None

RESUME_PROMPT = """You are a senior technical interviewer. A candidate has shared their resume and a job description.
Generate exactly 8 highly relevant interview questions tailored to this specific candidate and role.
Mix technical and behavioral questions based on the resume skills and job requirements.

Resume:
{resume}

Job Description:
{job_description}

Respond with this exact JSON only (no markdown, no extra text):
{{
  "questions": [
    {{"id": "r1", "question": "...", "difficulty": "easy|medium|hard", "topic": "..."}},
    {{"id": "r2", "question": "...", "difficulty": "easy|medium|hard", "topic": "..."}}
  ]
}}

Generate exactly 8 questions. Make them specific to the resume and JD, not generic."""


@app.post("/resume-review")
async def resume_review(request: ResumeRequest):
    """Generate tailored interview questions from resume + job description."""
    if len(request.resume.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume is too short.")
    if len(request.job_description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Job description is too short.")

    prompt = RESUME_PROMPT.format(
        resume=request.resume[:3000],
        job_description=request.job_description[:1500],
    )

    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": "You respond only with valid JSON. No markdown, no extra text."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.4,
                    "max_tokens": 1500,
                },
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Cannot reach local model at {LLM_BASE_URL}.")
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Model timed out generating questions.")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Model error: {response.status_code}")

    raw = response.json()["choices"][0]["message"]["content"]
    clean = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
    json_match = re.search(r"\{.*\}", clean, re.DOTALL)
    if not json_match:
        raise HTTPException(status_code=502, detail="Model did not return valid JSON.")

    try:
        result = json.loads(json_match.group())
        questions = result.get("questions", [])
        # Ensure IDs are unique
        for i, q in enumerate(questions):
            q["id"] = f"resume_{i+1}"
        return {"questions": questions, "total": len(questions)}
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Failed to parse questions JSON.")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
def _parse_llm_response(content: str) -> EvaluateResponse:
    """
    Parse the LLM's JSON response with robust error handling.
    Handles various edge cases and malformed outputs.
    """
    # Multiple cleaning passes
    clean = content.strip()
    
    # Remove markdown code fences
    clean = re.sub(r"```(?:json)?\s*", "", clean, flags=re.IGNORECASE).strip()
    clean = clean.replace("```", "").strip()
    
    # Remove any leading/trailing text that's not JSON
    # Find the first { and last }
    first_brace = clean.find('{')
    last_brace = clean.rfind('}')
    
    if first_brace == -1 or last_brace == -1 or first_brace > last_brace:
        # Try to extract JSON-like content
        lines = clean.split('\n')
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if not in_json and ('{' in line or line.startswith('{')):
                in_json = True
                
            if in_json:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count <= 0 and len(json_lines) > 1:
                    break
        
        if json_lines:
            clean = ' '.join(json_lines)
        else:
            raise HTTPException(
                status_code=502,
                detail="Model did not return recognizable JSON structure. Response: " + clean[:200]
            )
    else:
        clean = clean[first_brace:last_brace + 1]
    
    # Fix common JSON issues
    # Remove trailing commas before } or ]
    clean = re.sub(r",\s*([}\]])", r"\1", clean)
    # Fix unquoted keys (simple cases)
    clean = re.sub(r'([^"\s\{\,]+)(\s*:)', r'"\1"\2', clean)
    # Remove any control characters
    clean = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', clean)
    
    try:
        result = json.loads(clean)
    except json.JSONDecodeError as e:
        # Try one more aggressive cleanup
        try:
            # Remove any remaining problematic characters
            clean = re.sub(r'([^\x20-\x7E\n\r\t])', '', clean)
            # Try to find and extract JSON object
            json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", clean)
            if json_match:
                result = json.loads(json_match.group())
            else:
                raise e
        except (json.JSONDecodeError, ValueError):
            raise HTTPException(
                status_code=502,
                detail=f"Failed to parse model JSON after cleanup. Original error: {str(e)[:100]}... Response snippet: {clean[:200]}"
            )

    # Validate and sanitize the response
    return EvaluateResponse(
        strengths=_ensure_list(result.get("strengths", ["General response provided"])),
        missing_points=_ensure_list(result.get("missing_points", ["More specific technical details"])),
        score=max(1, min(10, int(float(str(result.get("score", 5)).split()[0]) if str(result.get("score", 5)).replace('.', '').isdigit() else 5))),
        summary=str(result.get("summary", "Response received but format was irregular.")).strip() or "No clear summary provided.",
        ideal_answer_hint=str(result.get("ideal_answer_hint", "Include more specific examples and technical details.")).strip(),
    )


def _ensure_list(value) -> list[str]:
    """Ensure value is a list of strings, handling edge cases from LLM output."""
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []


# ─────────────────────────────────────────────
# Session Persistence
# ─────────────────────────────────────────────
SESSIONS_DIR = Path(__file__).parent / "data" / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/sessions")
def save_session(request: SessionSaveRequest):
    """Save a completed interview session."""
    session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Calculate stats
    avg_score = sum(request.scores) / len(request.scores) if request.scores else 0
    best_score = max(request.scores) if request.scores else 0
    
    session_data = {
        "id": session_id,
        "role": request.role,
        "total_questions": len(request.questions),
        "questions": request.questions,
        "answers": request.answers,
        "scores": request.scores,
        "avg_score": round(avg_score, 1),
        "best_score": best_score,
        "completed_at": request.completed_at or datetime.now().isoformat(),
    }
    
    session_file = SESSIONS_DIR / f"{session_id}.json"
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)
    
    return {"id": session_id, "status": "saved"}


@app.get("/sessions", response_model=List[SessionResponse])
def get_sessions():
    """Get all saved sessions."""
    sessions = []
    for session_file in sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True):
        try:
            with open(session_file) as f:
                data = json.load(f)
            sessions.append(SessionResponse(
                id=data["id"],
                role=data["role"],
                total_questions=data["total_questions"],
                avg_score=data["avg_score"],
                best_score=data["best_score"],
                completed_at=data["completed_at"]
            ))
        except Exception:
            continue
    return sessions


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Get a specific session by ID."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(session_file) as f:
        return json.load(f)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a session."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    session_file.unlink()
    return {"status": "deleted"}


# ─────────────────────────────────────────────
# Interview Tips & Hints
# ─────────────────────────────────────────────
HINT_PROMPT = """You are a helpful interview coach. The candidate is about to answer this interview question.
Provide 2-3 quick tips or things to consider when answering. Be concise and encouraging.

Question: {question}
Role: {role}

Respond with this exact JSON structure:
{{
  "tips": ["tip 1", "tip 2", "tip 3"],
  "approach": "One sentence on how to structure the answer"
}}"""


@app.post("/hint")
async def get_hint(request: HintRequest):
    """Get tips/hints for a question before answering."""
    messages = [
        {"role": "system", "content": "You are a helpful interview coach. Respond with valid JSON only."},
        {"role": "user", "content": HINT_PROMPT.format(
            question=request.question,
            role=request.role
        )},
    ]
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers={"Content-Type": "application/json"},
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.4,
                    "max_tokens": 512,
                },
            )
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Cannot reach local model")
    
    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Model error")
    
    try:
        raw_content = response.json()["choices"][0]["message"]["content"]
        clean = re.sub(r"```(?:json)?\s*", "", raw_content).replace("```", "").strip()
        json_match = re.search(r"\{.*\}", clean, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            return result
    except Exception:
        pass
    
    # Fallback response
    return {
        "tips": ["Take a moment to organize your thoughts", "Use specific examples when possible"],
        "approach": "Start with a clear definition, then provide examples"
    }


# ─────────────────────────────────────────────
# Code Execution (Sandbox)
# ─────────────────────────────────────────────
@app.post("/execute-code")
async def execute_code(request: CodeExecuteRequest):
    """Execute Python code in a sandboxed environment."""
    if request.language != "python":
        raise HTTPException(status_code=400, detail="Only Python is supported currently")
    
    # Security: Limit code execution time and restrict imports
    restricted_imports = ['os', 'sys', 'subprocess', 'importlib', 'eval', 'exec', 'open', 'file']
    
    for restricted in restricted_imports:
        if restricted in request.code:
            return {
                "success": False,
                "output": "",
                "error": f"Security: '{restricted}' is not allowed in sandboxed code"
            }
    
    # Create a temporary file to execute
    import tempfile
    import subprocess
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        # Wrap code with timeout
        wrapped_code = f"""
import signal
import sys

def timeout_handler(signum, frame):
    print("\\n[Error: Code execution timed out after 5 seconds]")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(5)

try:
{chr(10).join('    ' + line for line in request.code.split(chr(10)))}
except Exception as e:
    print(f"\\n[Error: {{e}}]")
"""
        f.write(wrapped_code)
        temp_file = f.name
    
    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        output = result.stdout
        error = result.stderr
        
        # Clean up the temp file
        os.unlink(temp_file)
        
        return {
            "success": result.returncode == 0 and not error,
            "output": output,
            "error": error if error else None
        }
    except subprocess.TimeoutExpired:
        os.unlink(temp_file)
        return {
            "success": False,
            "output": "",
            "error": "Code execution timed out (10 seconds max)"
        }
    except Exception as e:
        if os.path.exists(temp_file):
            os.unlink(temp_file)
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }


# ─────────────────────────────────────────────
# Export Session as Markdown
# ─────────────────────────────────────────────
@app.get("/sessions/{session_id}/export")
def export_session(session_id: str):
    """Export a session as Markdown."""
    session_file = SESSIONS_DIR / f"{session_id}.json"
    if not session_file.exists():
        raise HTTPException(status_code=404, detail="Session not found")
    
    with open(session_file) as f:
        data = json.load(f)
    
    # Generate markdown
    md_content = f"""# Interview Session Report

**Role:** {data['role'].title()}  
**Date:** {data['completed_at']}  
**Average Score:** {data['avg_score']}/10  
**Best Score:** {data['best_score']}/10  

---

## Questions & Answers

"""
    
    for i, (q, a, s) in enumerate(zip(data['questions'], data['answers'], data['scores'])):
        md_content += f"""### Question {i+1}

**Q:** {q.get('question', 'N/A')}

**Your Answer:**
{a.get('answer', 'No answer provided')}

**Score:** {s}/10

---

"""
    
    # Return as downloadable file
    return StreamingResponse(
        io.StringIO(md_content),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=session_{session_id}.md"}
    )