"use client";

import { ChangeEvent, FormEvent, useMemo, useState } from "react";

type Evidence = {
  id: string;
  source_kind: string;
  source_label: string;
  relative_path?: string | null;
  line_start?: number | null;
  line_end?: number | null;
  excerpt: string;
  evidence_kind?: string;
};
type Mapping = {
  requirement_id: string;
  skill: string;
  status:
    | "demonstrated"
    | "partial_evidence"
    | "not_demonstrated"
    | "needs_review";
  rationale: string;
  evidence_ids: string[];
  confidence: string;
  importance: string;
  limitations: string[];
};
type PlanStep = {
  order: number;
  title: string;
  duration_minutes: number;
  reason: string;
  task: string;
  success_criteria: string[];
};
type Question = {
  id: string;
  skill: string;
  question: string;
  rubric: string[];
};
type Report = {
  analysis_id: string;
  status: string;
  created_at?: string;
  job_brief: {
    role_title: string;
    requirements: {
      requirement_id: string;
      name: string;
      importance: string;
      source_text: string;
    }[];
  };
  evidence_matrix: Mapping[];
  top_gaps: {
    skill: string;
    status: string;
    importance: string;
    reason: string;
  }[];
  preparation_plan: PlanStep[];
  evidence: Evidence[];
  repository_summary: string;
  limitations: string[];
  interview_questions: Question[];
  analysis_mode: string;
  model_note?: string;
};
type AnswerFeedback = {
  word_count: number;
  scores: Record<string, number>;
  strengths: string[];
  improvements: string[];
  note: string;
};

const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/$/, "");
const API = `${API_BASE}/api/v1`;

function Icon({ name }: { name: string }) {
  const glyphs: Record<string, string> = {
    spark: "✦",
    shield: "◈",
    file: "▤",
    target: "◎",
    clock: "◷",
    arrow: "↗",
    check: "✓",
    code: "‹›",
    brain: "◉",
    github: "⌘",
  };
  return (
    <span className="iconGlyph" aria-hidden="true">
      {glyphs[name] || "•"}
    </span>
  );
}

function StatusPill({ status }: { status: Mapping["status"] }) {
  const labels: Record<string, string> = {
    demonstrated: "Evidence found",
    partial_evidence: "Partial evidence",
    not_demonstrated: "Not demonstrated",
    needs_review: "Needs review",
  };
  return (
    <span className={`statusPill ${status.replaceAll("_", "-")}`}>
      <span className="statusDot" />
      {labels[status] || status}
    </span>
  );
}

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const [resume, setResume] = useState<File | null>(null);
  const [sourceMode, setSourceMode] = useState<"github" | "zip">("github");
  const [githubUrl, setGithubUrl] = useState("");
  const [repositoryZip, setRepositoryZip] = useState<File | null>(null);
  const [dailyMinutes, setDailyMinutes] = useState(45);
  const [daysAvailable, setDaysAvailable] = useState(7);
  const [report, setReport] = useState<Report | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedEvidence, setSelectedEvidence] = useState<Evidence | null>(
    null,
  );
  const [activeQuestion, setActiveQuestion] = useState(0);
  const [answerText, setAnswerText] = useState("");
  const [answerLoading, setAnswerLoading] = useState(false);
  const [feedback, setFeedback] = useState<AnswerFeedback | null>(null);
  const [activeTab, setActiveTab] = useState<"report" | "plan" | "interview">(
    "report",
  );

  const evidenceById = useMemo(
    () => new Map((report?.evidence || []).map((item) => [item.id, item])),
    [report],
  );
  const stats = useMemo(() => {
    const mappings = report?.evidence_matrix || [];
    return {
      requirements: mappings.length,
      grounded: mappings.filter((m) => m.status === "demonstrated").length,
      partial: mappings.filter((m) => m.status === "partial_evidence").length,
      gaps: mappings.filter(
        (m) => m.status === "not_demonstrated" || m.status === "needs_review",
      ).length,
    };
  }, [report]);

  function onFileChange(
    e: ChangeEvent<HTMLInputElement>,
    type: "resume" | "zip",
  ) {
    const file = e.target.files?.[0] || null;
    if (type === "resume") setResume(file);
    else setRepositoryZip(file);
  }

  async function runAnalysis(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError("");
    setReport(null);
    setFeedback(null);
    setLoading(true);
    if (!resume) {
      setError("Please add a PDF, DOCX, or TXT resume.");
      setLoading(false);
      return;
    }
    if (sourceMode === "github" && !githubUrl.trim()) {
      setError("Enter a public GitHub repository URL.");
      setLoading(false);
      return;
    }
    if (sourceMode === "zip" && !repositoryZip) {
      setError("Choose a project ZIP file.");
      setLoading(false);
      return;
    }
    try {
      const body = new FormData();
      body.append("job_description", jobDescription);
      body.append("resume_file", resume);
      body.append("daily_minutes", String(dailyMinutes));
      body.append("days_available", String(daysAvailable));
      if (sourceMode === "github") body.append("github_url", githubUrl.trim());
      else if (repositoryZip) body.append("repository_zip", repositoryZip);
      const response = await fetch(`${API}/analyses`, { method: "POST", body });
      const data = await response.json();
      if (!response.ok)
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Analysis could not be completed. Check the inputs and try again.",
        );
      setReport(data as Report);
      setActiveTab("report");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not connect to the API. Start the backend and try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  async function loadDemo() {
    setLoading(true);
    setError("");
    setFeedback(null);
    try {
      const response = await fetch(`${API}/demo`);
      if (!response.ok) throw new Error("Demo endpoint returned an error.");
      setReport((await response.json()) as Report);
      setActiveTab("report");
    } catch {
      // The sample path remains usable when the backend has not been started yet.
      setReport(makeBrowserDemo());
      setActiveTab("report");
    } finally {
      setLoading(false);
    }
  }

  async function submitAnswer(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!report || !answerText.trim()) return;
    setAnswerLoading(true);
    setError("");
    setFeedback(null);
    try {
      const response = await fetch(`${API}/interviews/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          analysis_id: report.analysis_id,
          question_id: report.interview_questions[activeQuestion]?.id,
          answer_text: answerText,
        }),
      });
      const data = await response.json();
      if (!response.ok)
        throw new Error(data.detail || "Unable to evaluate this answer.");
      setFeedback(data as AnswerFeedback);
    } catch (err) {
      // Local fallback feedback lets the interview UI be explored even without the API.
      const words = answerText.trim().split(/\s+/).length;
      setFeedback({
        word_count: words,
        scores: {
          technical_specificity: Math.min(5, 1 + Math.floor(words / 35)),
          concrete_example: /project|implemented|built|example/i.test(
            answerText,
          )
            ? 4
            : 2,
          tradeoff_awareness: /trade.?off|alternative|limitation|cost/i.test(
            answerText,
          )
            ? 4
            : 2,
          validation: /test|validated|metric|logs/i.test(answerText) ? 4 : 2,
          communication: words > 45 ? 4 : 2,
        },
        strengths:
          words > 45
            ? ["You provided enough detail to review."]
            : ["You have a starting point to expand."],
        improvements: [
          "Add one concrete project example.",
          "Explain one trade-off and how you validated the result.",
        ],
        note: "Local fallback practice feedback; start the API for full evaluation.",
      });
      setError(
        err instanceof Error
          ? `${err.message} Showing local practice feedback instead.`
          : "Showing local practice feedback instead.",
      );
    } finally {
      setAnswerLoading(false);
    }
  }

  function startNextQuestion() {
    if (!report) return;
    setActiveQuestion(
      (current) => (current + 1) % report.interview_questions.length,
    );
    setAnswerText("");
    setFeedback(null);
  }

  function exportReport() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `proofpath-report-${report.analysis_id.slice(0, 8)}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="appShell">
      <header className="topbar">
        <a className="brand" href="#top" aria-label="ProofPath AI home">
          <span className="brandMark">
            <Icon name="spark" />
          </span>
          <span>
            proofpath<span className="brandAI">.ai</span>
          </span>
        </a>
        <nav className="topNav">
          <a href="#how-it-works">How it works</a>
          <a href="#workspace">Workspace</a>
          <span className="privacyTag">
            <Icon name="shield" /> Evidence-first AI
          </span>
        </nav>
        <button
          className="button button-ghost button-small"
          onClick={loadDemo}
          disabled={loading}
        >
          Explore demo <Icon name="arrow" />
        </button>
      </header>

      <section className="hero" id="top">
        <div className="heroCopy">
          <div className="eyebrow">
            <span className="eyebrowDot" /> YOUR WORK, MADE VISIBLE
          </div>
          <h1>
            Career confidence,
            <br />
            <span>built on evidence.</span>
          </h1>
          <p className="heroText">
            Connect what a job asks for to what your resume and code actually
            show. Find meaningful gaps. Prepare with a plan that knows your
            work.
          </p>
          <div className="heroActions">
            <a href="#workspace" className="button button-primary">
              Analyze my fit <span>↘</span>
            </a>
            <button
              onClick={loadDemo}
              className="button button-secondary"
              disabled={loading}
            >
              See a sample report <Icon name="arrow" />
            </button>
          </div>
          <div className="trustLine">
            <span>
              <Icon name="check" /> Traceable evidence
            </span>
            <span>
              <Icon name="check" /> No invented credentials
            </span>
            <span>
              <Icon name="check" /> Actionable next steps
            </span>
          </div>
        </div>
        <div
          className="heroVisual"
          aria-label="Illustration of the ProofPath evidence report"
        >
          <div className="visualGlow" />
          <div className="previewCard previewMain">
            <div className="previewHead">
              <span className="tinyLabel">SKILL EVIDENCE REPORT</span>
              <span className="liveBadge">
                <span /> READY TO REVIEW
              </span>
            </div>
            <h3>Full Stack Engineer</h3>
            <p className="mutedText">
              Match your skills to the role requirements.
            </p>
            <div className="previewMetricRow">
              <div>
                <strong>12</strong>
                <span>Requirements</span>
              </div>
              <div>
                <strong className="greenText">07</strong>
                <span>Evidence found</span>
              </div>
              <div>
                <strong className="amberText">03</strong>
                <span>To strengthen</span>
              </div>
            </div>
            <div className="miniSkill">
              <div className="miniSkillTop">
                <span>React</span>
                <span className="miniGood">● Evidence found</span>
              </div>
              <div className="miniTrack">
                <i style={{ width: "92%" }} />
              </div>
              <small>src/components/Dashboard.tsx · Lines 8–28</small>
            </div>
            <div className="miniSkill">
              <div className="miniSkillTop">
                <span>REST APIs</span>
                <span className="miniPartial">● Partial evidence</span>
              </div>
              <div className="miniTrack">
                <i className="trackAmber" style={{ width: "58%" }} />
              </div>
              <small>api/routes.py · Lines 14–32</small>
            </div>
            <div className="miniSkill">
              <div className="miniSkillTop">
                <span>Docker</span>
                <span className="miniGap">● Not demonstrated</span>
              </div>
              <div className="miniTrack">
                <i className="trackGray" style={{ width: "22%" }} />
              </div>
              <small>Try a containerization practice task</small>
            </div>
          </div>
          <div className="floatingNote">
            <span className="noteIcon">
              <Icon name="target" />
            </span>
            <span>
              <b>A useful next step</b>
              <small>Practice one API endpoint</small>
            </span>
            <span className="noteArrow">↗</span>
          </div>
          <div className="floatingCode">
            <span className="codeOrb">
              <Icon name="code" />
            </span>
            <span>
              <b>Proof, not promises.</b>
              <small>Your project is the evidence.</small>
            </span>
          </div>
        </div>
      </section>

      <section className="featureStrip" id="how-it-works">
        <div className="featureItem">
          <span className="featureNumber">01</span>
          <span className="featureIcon">
            <Icon name="file" />
          </span>
          <div>
            <b>Understand the role</b>
            <p>Turn a job post into clear requirements.</p>
          </div>
        </div>
        <div className="featureItem">
          <span className="featureNumber">02</span>
          <span className="featureIcon">
            <Icon name="code" />
          </span>
          <div>
            <b>Connect the evidence</b>
            <p>Inspect resume claims and project files.</p>
          </div>
        </div>
        <div className="featureItem">
          <span className="featureNumber">03</span>
          <span className="featureIcon">
            <Icon name="target" />
          </span>
          <div>
            <b>Prepare with intent</b>
            <p>Build a plan and practice real questions.</p>
          </div>
        </div>
      </section>

      <section className="workspaceSection" id="workspace">
        <div className="sectionIntro">
          <div>
            <div className="eyebrow">YOUR CAREER WORKSPACE</div>
            <h2>
              Make your next move
              <br />
              <span>with clarity.</span>
            </h2>
          </div>
          <p>
            Start with one role, one resume, and one project. Your first
            evidence report is just a few steps away.
          </p>
        </div>
        <div className="workspaceGrid">
          <aside className="intakePanel panel">
            <div className="panelHeader">
              <span className="panelStep">01</span>
              <div>
                <h3>Set up your analysis</h3>
                <p>Share the role and the work you want to show.</p>
              </div>
            </div>
            <form onSubmit={runAnalysis} className="intakeForm">
              <label htmlFor="jobDescription">
                Job description <span className="required">*</span>
              </label>
              <textarea
                id="jobDescription"
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                minLength={30}
                maxLength={20000}
                required
                placeholder="Paste the job description here…\n\nInclude the role requirements, tech stack, and responsibilities for the most useful analysis."
                rows={7}
              />
              <div className="fieldHint">
                Include at least 30 characters. You can edit the report
                afterward.
              </div>
              <label>
                Resume <span className="required">*</span>
              </label>
              <label
                className={`uploadZone ${resume ? "hasFile" : ""}`}
                htmlFor="resumeFile"
              >
                <span className="uploadIcon">
                  <Icon name="file" />
                </span>
                <span className="uploadCopy">
                  <b>{resume ? resume.name : "Choose your resume"}</b>
                  <small>
                    {resume
                      ? `${(resume.size / 1024).toFixed(0)} KB · Selected`
                      : "PDF, DOCX or TXT · Up to 8 MB"}
                  </small>
                </span>
                <span className="chooseText">Browse</span>
                <input
                  id="resumeFile"
                  type="file"
                  accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
                  onChange={(e) => onFileChange(e, "resume")}
                />
              </label>
              <div className="sourceLabel">
                <label>
                  Project source <span className="required">*</span>
                </label>
                <span className="sourceHelper">Choose one</span>
              </div>
              <div className="segmented">
                <button
                  type="button"
                  onClick={() => setSourceMode("github")}
                  className={sourceMode === "github" ? "selected" : ""}
                >
                  <Icon name="github" /> Public GitHub
                </button>
                <button
                  type="button"
                  onClick={() => setSourceMode("zip")}
                  className={sourceMode === "zip" ? "selected" : ""}
                >
                  <Icon name="file" /> Upload ZIP
                </button>
              </div>
              {sourceMode === "github" ? (
                <div className="inputWithIcon">
                  <Icon name="github" />
                  <input
                    aria-label="Public GitHub repository URL"
                    type="url"
                    placeholder="https://github.com/you/project"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    required={sourceMode === "github"}
                  />
                </div>
              ) : (
                <label
                  className={`uploadZone uploadSmall ${repositoryZip ? "hasFile" : ""}`}
                  htmlFor="repoZip"
                >
                  <span className="uploadIcon">
                    <Icon name="file" />
                  </span>
                  <span className="uploadCopy">
                    <b>
                      {repositoryZip
                        ? repositoryZip.name
                        : "Choose project ZIP"}
                    </b>
                    <small>
                      {repositoryZip
                        ? `${(repositoryZip.size / 1024 / 1024).toFixed(2)} MB · Selected`
                        : "Source code and README files · Up to 20 MB"}
                    </small>
                  </span>
                  <span className="chooseText">Browse</span>
                  <input
                    id="repoZip"
                    type="file"
                    accept=".zip,application/zip,application/x-zip-compressed"
                    onChange={(e) => onFileChange(e, "zip")}
                  />
                </label>
              )}
              <div className="timeBudget">
                <div>
                  <label htmlFor="dailyMinutes">Prep time per day</label>
                  <select
                    id="dailyMinutes"
                    value={dailyMinutes}
                    onChange={(e) => setDailyMinutes(Number(e.target.value))}
                  >
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>1 hour</option>
                    <option value={90}>1.5 hours</option>
                    <option value={120}>2 hours</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="daysAvailable">Days available</label>
                  <select
                    id="daysAvailable"
                    value={daysAvailable}
                    onChange={(e) => setDaysAvailable(Number(e.target.value))}
                  >
                    <option value={1}>1 day</option>
                    <option value={3}>3 days</option>
                    <option value={5}>5 days</option>
                    <option value={7}>7 days</option>
                    <option value={14}>14 days</option>
                    <option value={30}>30 days</option>
                  </select>
                </div>
              </div>
              {error && (
                <div className="errorBox" role="alert">
                  {error}
                </div>
              )}
              <button
                className="button button-primary submitButton"
                type="submit"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner" /> Analyzing your evidence…
                  </>
                ) : (
                  <>
                    Build my evidence report <span>↗</span>
                  </>
                )}
              </button>
              <p className="privacyNote">
                <Icon name="shield" /> Uploads are analyzed for this report. Do
                not upload secrets, credentials, or files you do not have
                permission to share.
              </p>
            </form>
          </aside>

          <section className="resultsPanel panel">
            {!report ? (
              <div className="emptyResults">
                <div className="emptyGraphic">
                  <div className="emptyFile">
                    <Icon name="file" />
                  </div>
                  <div className="emptyCheck">✓</div>
                  <div className="emptySpark">✦</div>
                </div>
                <span className="eyebrow">REPORT PREVIEW</span>
                <h3>
                  Your evidence report
                  <br />
                  will live here.
                </h3>
                <p>
                  Submit your details or explore the sample report to see how
                  requirements become grounded matches and next steps.
                </p>
                <button
                  className="button button-secondary"
                  onClick={loadDemo}
                  disabled={loading}
                >
                  Load sample report <Icon name="arrow" />
                </button>
                <div className="emptyBottom">
                  <span>
                    <Icon name="shield" /> Source-linked
                  </span>
                  <span>
                    <Icon name="target" /> Actionable
                  </span>
                  <span>
                    <Icon name="spark" /> Evidence-first
                  </span>
                </div>
              </div>
            ) : (
              <div className="reportContent">
                <div className="reportHeading">
                  <div>
                    <div className="eyebrow">
                      <span className="eyebrowDot" /> ANALYSIS COMPLETE ·{" "}
                      {report.analysis_mode === "demo"
                        ? "SAMPLE DATA"
                        : report.analysis_mode === "meta_model_enhanced"
                          ? "META-ENHANCED"
                          : "LOCAL ANALYSIS"}
                    </div>
                    <h3>
                      {report.job_brief?.role_title || "Career evidence report"}
                    </h3>
                    <p>{report.repository_summary}</p>
                  </div>
                  <button
                    title="Export report JSON"
                    className="iconButton"
                    onClick={exportReport}
                  >
                    ↓
                  </button>
                </div>
                <div className="reportStats">
                  <div>
                    <strong>
                      {stats.requirements.toString().padStart(2, "0")}
                    </strong>
                    <span>Requirements</span>
                  </div>
                  <div className="statGreen">
                    <strong>
                      {stats.grounded.toString().padStart(2, "0")}
                    </strong>
                    <span>Evidence found</span>
                  </div>
                  <div className="statAmber">
                    <strong>{stats.partial.toString().padStart(2, "0")}</strong>
                    <span>Partial</span>
                  </div>
                  <div className="statMuted">
                    <strong>{stats.gaps.toString().padStart(2, "0")}</strong>
                    <span>To strengthen</span>
                  </div>
                </div>
                <div className="reportTabs">
                  <button
                    onClick={() => setActiveTab("report")}
                    className={activeTab === "report" ? "active" : ""}
                  >
                    Skill evidence <span>{stats.requirements}</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("plan")}
                    className={activeTab === "plan" ? "active" : ""}
                  >
                    Prep plan{" "}
                    <span>{report.preparation_plan?.length || 0}</span>
                  </button>
                  <button
                    onClick={() => setActiveTab("interview")}
                    className={activeTab === "interview" ? "active" : ""}
                  >
                    Mock interview{" "}
                    <span>{report.interview_questions?.length || 0}</span>
                  </button>
                </div>
                {activeTab === "report" && (
                  <div className="mappingList">
                    {(report.evidence_matrix || []).map((mapping) => (
                      <article
                        className="mappingCard"
                        key={mapping.requirement_id}
                      >
                        <div className="mappingTop">
                          <div>
                            <h4>{mapping.skill}</h4>
                            <span
                              className={`importance ${mapping.importance === "must_have" ? "important" : ""}`}
                            >
                              {mapping.importance === "must_have"
                                ? "MUST HAVE"
                                : "NICE TO HAVE"}
                            </span>
                          </div>
                          <StatusPill status={mapping.status} />
                        </div>
                        <p>{mapping.rationale}</p>
                        {mapping.evidence_ids.length > 0 && (
                          <div className="evidenceLinks">
                            {mapping.evidence_ids.map((id) => {
                              const ev = evidenceById.get(id);
                              return ev ? (
                                <button
                                  className="evidenceLink"
                                  key={id}
                                  onClick={() => setSelectedEvidence(ev)}
                                >
                                  <Icon name="file" />
                                  <span>
                                    {ev.relative_path || ev.source_label}
                                    {ev.line_start
                                      ? ` · L${ev.line_start}–${ev.line_end || ev.line_start}`
                                      : " · Resume"}
                                  </span>
                                  <Icon name="arrow" />
                                </button>
                              ) : (
                                <span className="tinyEvidence" key={id}>
                                  {id}
                                </span>
                              );
                            })}
                          </div>
                        )}
                      </article>
                    ))}
                  </div>
                )}
                {activeTab === "plan" && (
                  <div className="planList">
                    {(report.preparation_plan || []).map((step) => (
                      <article className="planCard" key={step.order}>
                        <div className="planNumber">
                          {String(step.order).padStart(2, "0")}
                        </div>
                        <div className="planBody">
                          <div className="planMeta">
                            <span>
                              <Icon name="clock" /> {step.duration_minutes} min
                            </span>
                            <span>STEP {step.order}</span>
                          </div>
                          <h4>{step.title}</h4>
                          <p>{step.task}</p>
                          <div className="successCriteria">
                            <b>Done when</b>
                            {step.success_criteria.map((item, i) => (
                              <span key={i}>
                                <Icon name="check" />
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>
                      </article>
                    ))}
                  </div>
                )}
                {activeTab === "interview" && (
                  <div className="interviewPanel">
                    {report.interview_questions?.length ? (
                      <>
                        <div className="interviewProgress">
                          <span>
                            QUESTION {activeQuestion + 1} OF{" "}
                            {report.interview_questions.length}
                          </span>
                          <div className="progressTrack">
                            <i
                              style={{
                                width: `${((activeQuestion + 1) / report.interview_questions.length) * 100}%`,
                              }}
                            />
                          </div>
                        </div>
                        <div className="questionCard">
                          <span className="questionLabel">
                            <Icon name="brain" />{" "}
                            {report.interview_questions[activeQuestion]
                              ?.skill || "Role-specific"}
                          </span>
                          <h4>
                            {
                              report.interview_questions[activeQuestion]
                                ?.question
                            }
                          </h4>
                          <form onSubmit={submitAnswer}>
                            <label htmlFor="interviewAnswer">Your answer</label>
                            <textarea
                              id="interviewAnswer"
                              rows={5}
                              value={answerText}
                              onChange={(e) => setAnswerText(e.target.value)}
                              placeholder="Explain the situation, what you did, the trade-offs, and how you validated the result…"
                              required
                            />
                            <button
                              className="button button-primary"
                              type="submit"
                              disabled={answerLoading}
                            >
                              {answerLoading ? (
                                <>
                                  <span className="spinner" /> Reviewing…
                                </>
                              ) : (
                                <>
                                  Review my answer <Icon name="arrow" />
                                </>
                              )}
                            </button>
                          </form>
                        </div>
                        {feedback && (
                          <div className="feedbackCard">
                            <div className="feedbackHead">
                              <h4>Practice feedback</h4>
                              <span>{feedback.word_count} words</span>
                            </div>
                            <div className="scoreGrid">
                              {Object.entries(feedback.scores).map(
                                ([key, value]) => (
                                  <div key={key}>
                                    <span>{key.replaceAll("_", " ")}</span>
                                    <strong>
                                      {value}
                                      <small>/5</small>
                                    </strong>
                                    <div className="scoreTrack">
                                      <i style={{ width: `${value * 20}%` }} />
                                    </div>
                                  </div>
                                ),
                              )}
                            </div>
                            <div className="feedbackColumns">
                              <div>
                                <b>What worked</b>
                                {feedback.strengths.map((s, i) => (
                                  <p key={i}>✓ {s}</p>
                                ))}
                              </div>
                              <div>
                                <b>Try next</b>
                                {feedback.improvements.map((s, i) => (
                                  <p key={i}>↗ {s}</p>
                                ))}
                              </div>
                            </div>
                            <p className="feedbackNote">{feedback.note}</p>
                            <button
                              className="button button-secondary"
                              onClick={startNextQuestion}
                            >
                              Next question <Icon name="arrow" />
                            </button>
                          </div>
                        )}
                      </>
                    ) : (
                      <p>No questions available for this report.</p>
                    )}
                  </div>
                )}
                <div className="reportFootnote">
                  <Icon name="shield" />
                  <span>
                    {report.limitations?.[2] ||
                      "AI results are limited to supplied materials. Review source evidence before relying on conclusions."}
                  </span>
                </div>
              </div>
            )}
          </section>
        </div>
      </section>

      <section className="principleSection">
        <div>
          <div className="eyebrow">BUILT DIFFERENTLY</div>
          <h2>
            No black-box score.
            <br />
            <span>Show the evidence.</span>
          </h2>
        </div>
        <div className="principleList">
          <div>
            <span>01</span>
            <div>
              <b>Every match has a source</b>
              <p>Inspect the file and excerpt behind a skill assessment.</p>
            </div>
          </div>
          <div>
            <span>02</span>
            <div>
              <b>Gaps are not judgments</b>
              <p>
                “Not demonstrated” means we couldn't find evidence in the
                material provided.
              </p>
            </div>
          </div>
          <div>
            <span>03</span>
            <div>
              <b>Advice you can act on</b>
              <p>
                Turn your real gaps into practical exercises with clear finish
                lines.
              </p>
            </div>
          </div>
        </div>
      </section>
      <footer className="footer">
        <a className="brand" href="#top">
          <span className="brandMark">
            <Icon name="spark" />
          </span>
          <span>
            proofpath<span className="brandAI">.ai</span>
          </span>
        </a>
        <span>Career confidence, built on evidence.</span>
        <span>© 2026 ProofPath AI · Developer preview</span>
      </footer>

      {selectedEvidence && (
        <div
          className="modalBackdrop"
          role="presentation"
          onClick={() => setSelectedEvidence(null)}
        >
          <section
            className="evidenceModal"
            role="dialog"
            aria-modal="true"
            aria-label="Evidence details"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="modalClose"
              onClick={() => setSelectedEvidence(null)}
              aria-label="Close"
            >
              ×
            </button>
            <div className="eyebrow">SOURCE EVIDENCE</div>
            <h3>
              {selectedEvidence.relative_path || selectedEvidence.source_label}
            </h3>
            <p className="mutedText">
              {selectedEvidence.source_label}
              {selectedEvidence.line_start
                ? ` · Lines ${selectedEvidence.line_start}–${selectedEvidence.line_end}`
                : " · Resume excerpt"}
            </p>
            <pre>{selectedEvidence.excerpt}</pre>
            <div className="modalFoot">
              <Icon name="shield" /> This excerpt is evidence to review, not
              proof of mastery or authorship.
            </div>
          </section>
        </div>
      )}
    </main>
  );
}

function makeBrowserDemo(): Report {
  const evidence: Evidence[] = [
    {
      id: "ev_100",
      source_kind: "repository",
      source_label: "Demo repository",
      relative_path: "src/App.tsx",
      line_start: 1,
      line_end: 5,
      excerpt:
        "import React, { useState } from 'react';\nexport default function App() {\n const [query, setQuery] = useState('');\n return <main><input value={query} onChange={(e) => setQuery(e.target.value)} /></main>;\n}",
      evidence_kind: "project_file",
    },
    {
      id: "ev_110",
      source_kind: "repository",
      source_label: "Demo repository",
      relative_path: "api/server.py",
      line_start: 1,
      line_end: 5,
      excerpt:
        "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\ndef health():\n    return {'status': 'ok'}",
      evidence_kind: "project_file",
    },
    {
      id: "ev_120",
      source_kind: "repository",
      source_label: "Demo repository",
      relative_path: "package.json",
      line_start: 1,
      line_end: 1,
      excerpt: '{"dependencies":{"react":"^19.0.0","typescript":"^5.0.0"}}',
      evidence_kind: "project_file",
    },
  ];
  const mappings: Mapping[] = [
    {
      requirement_id: "req_1",
      skill: "React",
      status: "demonstrated",
      rationale:
        "React state and component usage appears in the supplied source excerpt. Review the file to confirm it represents your own work.",
      evidence_ids: ["ev_100"],
      confidence: "medium",
      importance: "must_have",
      limitations: [],
    },
    {
      requirement_id: "req_2",
      skill: "TypeScript",
      status: "partial_evidence",
      rationale:
        "TypeScript appears in project metadata, but that alone does not demonstrate implementation depth.",
      evidence_ids: ["ev_120"],
      confidence: "low",
      importance: "must_have",
      limitations: [],
    },
    {
      requirement_id: "req_3",
      skill: "Node.js",
      status: "not_demonstrated",
      rationale:
        "No sufficient supporting evidence was found in the supplied sample files. This does not mean you lack the skill.",
      evidence_ids: [],
      confidence: "low",
      importance: "must_have",
      limitations: ["No matching evidence found in supplied materials."],
    },
    {
      requirement_id: "req_4",
      skill: "REST APIs",
      status: "demonstrated",
      rationale:
        "A FastAPI route is shown in the supplied project excerpt. Review the code for context.",
      evidence_ids: ["ev_110"],
      confidence: "medium",
      importance: "must_have",
      limitations: [],
    },
    {
      requirement_id: "req_5",
      skill: "PostgreSQL",
      status: "not_demonstrated",
      rationale:
        "No sufficient supporting evidence was found in supplied materials.",
      evidence_ids: [],
      confidence: "low",
      importance: "nice_to_have",
      limitations: ["No matching evidence found in supplied materials."],
    },
    {
      requirement_id: "req_6",
      skill: "Docker",
      status: "not_demonstrated",
      rationale:
        "No Docker configuration or relevant implementation evidence was found in the sample files.",
      evidence_ids: [],
      confidence: "low",
      importance: "nice_to_have",
      limitations: ["No matching evidence found in supplied materials."],
    },
  ];
  const plan: PlanStep[] = [
    {
      order: 1,
      title: "Strengthen Node.js evidence",
      duration_minutes: 45,
      reason:
        "Node.js is listed as a role requirement but wasn't demonstrated in the sample files.",
      task: "Implement a small API route with input validation and a consistent error response. Document the request and response contract.",
      success_criteria: [
        "Route works end-to-end",
        "Invalid input is handled",
        "Add three tests",
      ],
    },
    {
      order: 2,
      title: "Build a PostgreSQL-backed feature",
      duration_minutes: 45,
      reason:
        "Database design is a nice-to-have requirement with no source evidence in the sample.",
      task: "Create one small table and connect it to a route. Explain the primary key and one query/index decision.",
      success_criteria: [
        "Schema has appropriate constraints",
        "CRUD path works",
        "Explain one database trade-off",
      ],
    },
    {
      order: 3,
      title: "Practice a project walkthrough",
      duration_minutes: 45,
      reason:
        "You should be able to explain the design choices behind each demonstrated skill.",
      task: "Prepare a 2-minute walkthrough covering architecture, a difficult bug, a trade-off and how you tested the feature.",
      success_criteria: [
        "Explain one design choice",
        "Describe how you tested it",
        "Connect the project to the role",
      ],
    },
  ];
  return {
    analysis_id: "demo",
    status: "completed",
    job_brief: {
      role_title: "Full Stack Developer",
      requirements: mappings.map((m) => ({
        requirement_id: m.requirement_id,
        name: m.skill,
        importance: m.importance,
        source_text: m.skill,
      })),
    },
    evidence_matrix: mappings,
    top_gaps: mappings
      .filter((m) => m.status !== "demonstrated")
      .map((m) => ({
        skill: m.skill,
        status: m.status,
        importance: m.importance,
        reason: m.rationale,
      })),
    preparation_plan: plan,
    evidence,
    repository_summary: "Sample repository — synthetic demo data",
    limitations: [
      "Analysis is limited to the resume, job description and repository files supplied.",
      "Code references cannot prove authorship, production quality or mastery; review every cited excerpt.",
      "Not demonstrated means insufficient evidence was found, not that the candidate lacks the skill.",
    ],
    interview_questions: [
      {
        id: "q_1",
        skill: "React",
        question:
          "Walk me through a real project where you used React. What did you implement, what trade-off did you make, and how did you validate the result?",
        rubric: ["Correctness", "Specificity", "Trade-offs", "Validation"],
      },
      {
        id: "q_2",
        skill: "REST APIs",
        question:
          "Describe the API route you implemented. How do you validate requests, handle errors, and test reliability?",
        rubric: ["Correctness", "Specificity", "Trade-offs", "Validation"],
      },
      {
        id: "q_3",
        skill: "System design",
        question:
          "How would you design a reliable API for a growing application?",
        rubric: ["Requirements", "Design", "Failure handling", "Trade-offs"],
      },
    ],
    analysis_mode: "demo",
  };
}
