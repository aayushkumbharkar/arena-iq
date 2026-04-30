# ElectIQ — AI-Powered Election Process Education

> 🗳️ Empowering citizens with AI-driven election literacy

**Challenge 2 — Election Process Education · Google Antigravity × Hack2skill**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Render-blue?style=for-the-badge&logo=render)](https://arena-iq.onrender.com)
[![Tests](https://img.shields.io/badge/Tests-29%20Passed-brightgreen?style=for-the-badge)](#-testing)
[![Coverage](https://img.shields.io/badge/Coverage-82%25-green?style=for-the-badge)](#-testing)
[![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python)](https://python.org)

---

## 🎯 Chosen Vertical

**Election Process Education** — Building an intelligent assistant that helps citizens understand the entire democratic election process, from voter registration to government formation.

## 💡 Approach and Logic

### Problem
Democratic participation depends on informed citizens, yet election processes are complex and often poorly understood. First-time voters especially struggle with:
- Understanding the end-to-end election process
- Knowing how to register and what documents are needed
- Understanding how their vote is secured and counted
- Differentiating between election types and voting methods

### Solution: ElectIQ
ElectIQ is a **context-aware AI education platform** that uses **Google Gemini 2.0 Flash** to provide personalised election education through natural conversation. Instead of static content, users interact with an AI expert that adapts to their specific questions and knowledge level.

**Key Design Decisions:**
1. **Conversational AI over static content** — Users learn by asking questions naturally, powered by Gemini's understanding
2. **Comprehensive knowledge base** — The AI has a structured election database injected as system context
3. **Interactive learning** — AI-generated quizzes reinforce understanding
4. **Non-partisan by design** — System prompt enforces neutrality and factual accuracy
5. **Fallback architecture** — Full functionality without API key via intelligent demo responses

## 🏗️ How the Solution Works

### Architecture

```
┌───────────────────────────────────────────────┐
│            ElectIQ Frontend (SPA)             │
│  Election timeline · AI chat · Quiz engine    │
│  Voter info panels · Accessibility features   │
└──────────────────┬────────────────────────────┘
                   │ REST API
┌──────────────────▼────────────────────────────┐
│          Flask Backend (Python)               │
│  /api/chat — Gemini AI election expert        │
│  /api/quiz — AI-generated quiz questions      │
│  /api/election-data — Structured knowledge    │
│  /api/health — Container health check         │
│  Security · Caching · Rate Limiting           │
└──────────────────┬────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────┐
│       Google Gemini 2.0 Flash                 │
│  Context-aware election expert                │
│  Quiz question generation                     │
│  System prompt + knowledge base               │
└───────────────────────────────────────────────┘
```

### Features

| Feature | Description |
|---------|-------------|
| 🤖 **AI Chat** | Natural language election education powered by Gemini |
| 🗳️ **Interactive Timeline** | Visual 7-step election process walkthrough |
| 🧠 **Smart Quiz** | AI-generated quiz questions with explanations |
| 📝 **Voter Guide** | Registration steps, eligibility, required documents |
| 📊 **Voting Methods** | EVM, paper ballot, postal, VVPAT explained |
| 🏛️ **Election Types** | National, state, local, by-elections, referendums |
| ⚖️ **Voter Rights** | NOTA, accessible voting, right to information |
| ◑ **Accessibility** | High contrast mode, keyboard nav, screen reader support |

### User Flow
1. User lands on the dashboard with election timeline, chat, and info panels
2. Quick prompt buttons let users jump to common topics instantly
3. Chat with Gemini AI for in-depth, personalised election education
4. Click timeline steps or info cards to explore specific topics
5. Take the quiz to test and reinforce knowledge

## 📋 Assumptions

- The application focuses on democratic election processes generally, with examples from the Indian election system
- Internet connectivity is required for Gemini AI features; demo mode works offline
- Users are citizens seeking to understand election processes (first-time voters, students, educators)
- The AI maintains strict non-partisan neutrality and redirects political questions

## 🛡️ Google Services Integration

| Service | Usage | Purpose |
|---------|-------|---------|
| **Google Gemini 2.0 Flash** | AI chat + quiz generation | Core intelligence for personalised education |
| **Google Cloud Logging** | Structured logging | Production observability (auto-detects Cloud Run) |
| **Google Fonts** | Inter + Space Grotesk | Premium typography |
| **Google API Core** | Retry policies | Resilient API communication |

## 🧪 Testing

```bash
# Run full test suite with coverage
pytest tests/ -v --cov=. --cov-report=term-missing

# Results: 29 tests passed, 82% coverage
```

**Test categories:**
- Index route and health endpoint
- Election data API structure and integrity
- Chat input validation (empty, too long, XSS)
- All 10 demo response branches
- Quiz endpoint and question structure
- Data integrity checks

## ♿ Accessibility

- **Skip navigation** link for keyboard users
- **High contrast mode** toggle in header
- **Visible focus rings** on all interactive elements
- **ARIA live regions** for dynamic chat updates
- **Keyboard navigation** throughout (Enter on timeline items, quiz)
- **Semantic HTML5** (`<main>`, `<aside>`, `role` attributes)
- **Reduced motion** media query support
- **Screen reader** labels on all interactive elements

## 🔒 Security

- **Flask-Talisman** — HSTS, security headers
- **Rate limiting** — 15 req/min on chat, 200/day default
- **Input validation** — Max 500 chars, HTML escaping via MarkupSafe
- **Non-root Docker** — Container runs as unprivileged user
- **API key protection** — `.env` gitignored, `.env.example` template only
- **Safety filters** — Gemini content safety settings enabled

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### Local Development

```bash
git clone https://github.com/aayushkumbharkar/arena-iq.git
cd arena-iq
pip install -r requirements.txt

# Set your API key
echo GEMINI_API_KEY=your_key > .env   # or set as environment variable

python app.py
# Visit http://localhost:8080
```

### Docker

```bash
docker build -t electiq .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key electiq
```

## 📁 Project Structure

```
arena-iq/
├── app.py              # Flask backend, routes, Gemini integration
├── config.py           # Centralized environment-based configuration
├── requirements.txt    # Python dependencies
├── Dockerfile          # Production container (non-root, health check)
├── .dockerignore       # Docker build exclusions
├── .env.example        # Environment variable template
├── render.yaml         # Render.com deployment config
├── pytest.ini          # Test configuration
├── .coveragerc         # Coverage settings
├── static/
│   ├── index.html      # Semantic HTML structure
│   ├── styles.css      # Design system (indigo/gold theme)
│   └── app.js          # Frontend logic, chat, quiz engine
└── tests/
    ├── __init__.py
    └── test_app.py     # 29 comprehensive tests
```

## 🛠️ Tech Stack

- **Frontend**: HTML5 / CSS3 / Vanilla JS — semantic, accessible, responsive
- **Backend**: Python Flask + Gunicorn
- **AI**: Google Gemini 2.0 Flash (`google-generativeai`)
- **Security**: Flask-Talisman, Flask-Limiter, MarkupSafe
- **Performance**: Flask-Compress (gzip), Flask-Caching
- **Logging**: Google Cloud Logging (production) / stdlib (local)
- **Testing**: pytest + pytest-cov (82% coverage)
- **Deployment**: Docker + Render.com

---

*Built with ❤️ using Google Antigravity + Google Gemini 2.0 Flash*
