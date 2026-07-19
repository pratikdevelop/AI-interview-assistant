# 🎯 DevPrep AI — Free AI Interview Practice for Freshers & Junior Devs

> Practice real technical interview questions and get instant AI-powered feedback.  
> No login. No payment. Just practice.

![Demo](docs/demo.gif)

---

## 🚀 What It Does

- **Practice interviews** with real questions across 14+ technical domains
- **Get instant AI feedback** — strengths, missing points, score out of 10
- **Multiple practice modes**:
  - Text-based practice (traditional)
  - Voice-based mock interviews
  - **🎬 Comprehensive AI Video Interviews** (NEW!)
- **No account needed** — open and start practicing in 30 seconds
- **Completely free** — built by a dev, for devs

---

## 🧩 Who It's For

- Freshers preparing for their first dev job
- Junior developers aiming for mid-level roles  
- Anyone who learns better by doing, not just reading

---

## ⚡ Quick Start

### Option 1: Frontend Only (No backend needed)
Open `frontend/index.html` directly in your browser.  
It works offline with a built-in question bank. Add your backend URL in the ⚙️ panel.

### Option 2: Full Stack (Real AI feedback)

**Backend:**
```bash
cd backend
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
# Just open frontend/index.html in your browser
# Or serve it with any static server:
npx serve frontend/
```

Visit `http://localhost:3000` — the app auto-connects to your backend.

---

## 🗂️ Project Structure

```
ai-interview-prep/
├── backend/
│   ├── main.py              # FastAPI app + evaluation endpoint
│   ├── requirements.txt
│   └── .env.example
├── data/
│   └── questions.json       # 60 questions (React, Backend, SQL)
├── frontend/
│   └── index.html           # Complete React-like SPA (single file)
└── README.md
```

---

## 🤖 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/roles` | Get all available roles |
| GET | `/questions?role=react` | Get questions for a role |
| GET | `/questions/mixed` | Get mixed questions from all domains |
| POST | `/evaluate` | AI evaluation of an answer |
| POST | `/hint` | Get interview tips before answering |
| POST | `/execute-code` | Execute code snippets in sandbox |

**Evaluate request:**
```json
{
  "question": "What is the virtual DOM?",
  "answer": "The virtual DOM is a lightweight copy of the real DOM..."
}
```

**Evaluate response:**
```json
{
  "strengths": ["Correctly identified the purpose of virtual DOM"],
  "missing_points": ["Didn't mention reconciliation algorithm"],
  "score": 7,
  "summary": "Good foundational answer...",
  "ideal_answer_hint": "Mention diffing, reconciliation, and batch updates."
}
```

---

## 🚢 Deployment

**Backend → Railway / Render (free tier):**
1. Push repo to GitHub
2. Connect to [Railway](https://railway.app) or [Render](https://render.com)
3. Set `ANTHROPIC_API_KEY` environment variable
4. Deploy → get your backend URL

**Frontend → Vercel / Netlify / GitHub Pages:**
1. The `frontend/` folder is a single HTML file
2. Works on any static host
3. Update the backend URL in the ⚙️ config panel

---

## 🎬 Comprehensive AI Video Interview (New Feature)

The newest addition combines all domains into a professional-grade interview simulation:

**Features:**
- **Mixed-domain questions** — Randomly selected from all 14+ technical areas
- **Video recording** — Records your webcam feed throughout the session
- **Voice transcription** — Real-time speech-to-text for your answers
- **Domain-specific evaluation** — Tracks performance by technical area
- **Professional feedback** — Detailed scoring with domain breakdown
- **Privacy-focused** — All processing happens locally in your browser

**How it works:**
1. Select which technical domains to include
2. Choose number of questions (3-20)
3. Grant camera/microphone permissions
4. AI speaks each question aloud
5. You answer verbally while being recorded
6. Get instant evaluation with domain-specific insights
7. Receive comprehensive results with performance breakdown

**Technical domains covered:**
JavaScript, React, TypeScript, Python, Backend, SQL, DSA, System Design, CSS, Git, DevOps, Networking, OS Concepts, Behavioral

## 🧠 AI Evaluation Prompt

The AI acts as a senior technical interviewer and evaluates:
- **Strengths** — what the candidate got right
- **Missing points** — key concepts not mentioned
- **Score (1–10)** — honest assessment
- **Ideal answer hint** — what a 9-10 answer includes

---

## ❤️ Sponsor This Project

If DevPrep AI helped you land an interview or get better at practicing, please consider sponsoring. I built this while job hunting myself, in my spare time, completely free.

**[→ Sponsor on GitHub](https://github.com/sponsors/your-username)**

Even $1/month helps me keep this running and build more free tools.

---

## 🤝 Contributing

Pull requests are welcome! Ideas for contribution:
- Add more question categories (System Design, DSA, etc.)
- Add a timer mode
- Improve the AI evaluation prompt
- Add dark/light theme toggle

---

## 📊 Roadmap

- [x] Question bank (React, Backend, SQL)
- [x] AI evaluation with Claude
- [x] Offline fallback mode
- [x] System Design category
- [x] DSA / coding questions
- [x] Resume review mode
- [x] Share your score
- [x] Comprehensive AI video interview
- [x] Domain-specific performance tracking
- [x] Code execution sandbox
- [x] Interview hints and tips

---

## 📄 License

MIT — free to use, fork, and build on.

---

<div align="center">

Built with ❤️ by an indie dev · [GitHub](https://github.com/your-username/ai-interview-prep) · [Sponsor](https://github.com/sponsors/your-username)

</div>