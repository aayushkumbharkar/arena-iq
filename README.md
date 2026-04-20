# ArenaIQ — AI-Powered Smart Venue Assistant

> 🏟️ Transforming the large-scale sporting event experience with real-time AI intelligence

**Built for PromptWars Virtual Challenge 1 — Google Antigravity × Hack2skill**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Cloud%20Run-blue?style=for-the-badge&logo=googlecloud)](YOUR_CLOUD_RUN_URL)

---

## 🎯 Problem Statement

Large-scale sporting venues face critical attendee experience challenges:
- **Crowd Bottlenecks**: Fans cluster in high-density zones without knowing alternatives exist
- **Long Wait Times**: No real-time visibility into food court or restroom queues  
- **Poor Navigation**: Attendees miss events while lost or stuck in queues
- **Reactive Management**: Venue staff react to problems instead of preventing them

## 💡 Solution: ArenaIQ

ArenaIQ is an **intelligent venue assistant** powered by **Google Gemini 2.0 Flash** that provides:

| Feature | Description |
|---------|-------------|
| 🗺️ **Live Crowd Map** | Real-time density visualization across all venue sections |
| ⏱️ **Wait Time Intelligence** | Accurate wait estimates for food courts, restrooms, and gates |
| 🤖 **AI Chat Assistant** | Natural language queries powered by Gemini AI |
| 🚨 **Proactive Alerts** | Smart notifications before problems escalate |
| 📅 **Event Timeline** | Live event schedule with current status |
| 🚪 **Gate Optimization** | Route attendees to fastest entry/exit points |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              ArenaIQ Frontend                │
│  Single-page app · Interactive SVG map       │
│  Real-time panels · Gemini chat interface    │
└──────────────────┬──────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────┐
│           Flask Backend (Python)             │
│  /api/chat — Gemini 2.0 Flash integration   │
│  /api/venue-data — Live venue state          │
│  Simulated real-time crowd data engine       │
└──────────────────┬──────────────────────────┘
                   │ API calls
┌──────────────────▼──────────────────────────┐
│         Google Gemini 2.0 Flash              │
│  Context-aware venue assistant               │
│  System prompt with live venue data          │
└─────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/))

### Local Development

```bash
# Clone the repository
git clone <your-repo-url>
cd arena-iq

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
set GEMINI_API_KEY=your_api_key_here   # Windows
# export GEMINI_API_KEY=your_api_key_here  # Linux/Mac

# Run the app
python app.py

# Visit http://localhost:8080
```

### Docker

```bash
docker build -t arena-iq .
docker run -p 8080:8080 -e GEMINI_API_KEY=your_key arena-iq
```

## ☁️ Google Cloud Run Deployment

```bash
# Set your project
export PROJECT_ID=your-gcp-project-id

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/arena-iq

# Deploy to Cloud Run
gcloud run deploy arena-iq \
  --image gcr.io/$PROJECT_ID/arena-iq \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_api_key_here
```

## 🧠 AI Integration Details

ArenaIQ uses **Google Gemini 2.0 Flash** with a context-rich system prompt that includes:

- **Live venue state**: All 5 sections with crowd density, wait times, and capacity data
- **Gate status**: Queue lengths and estimated entry times for all gates
- **Amenity data**: Food court menus, wait times, and locations
- **Event schedule**: Timeline with live/upcoming/completed states

The AI provides:
- Contextual navigation recommendations
- Crowd-aware food suggestions
- Optimal timing advice (e.g., "go get food during halftime before lines build up")
- Safety and comfort guidance

## 📊 Key Metrics Addressed

| Challenge | ArenaIQ Solution |
|-----------|-----------------|
| Crowd congestion | Real-time density map + proactive section recommendations |
| Long food queues | Live wait times + AI suggestions for shortest waits |
| Gate bottlenecks | Queue lengths + estimated entry times per gate |
| Navigation confusion | Interactive map + natural language directions |
| Missing event content | Live timeline with status indicators |

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS — interactive SVG maps, glassmorphism UI
- **Backend**: Python Flask + Gunicorn
- **AI**: Google Gemini 2.0 Flash (`google-generativeai`)
- **Deployment**: Docker + Google Cloud Run
- **Design**: Space Grotesk + Inter fonts, HSL-tuned color palette

## 📁 Project Structure

```
arena-iq/
├── app.py              # Flask backend + Gemini integration
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition for Cloud Run
├── README.md           # This file
└── static/
    └── index.html      # Full frontend (SPA)
```

## 🏆 Why ArenaIQ Wins

1. **Real Problem, Real Solution**: Addresses genuine pain points at sporting events
2. **AI-Native Design**: Gemini is deeply integrated, not bolted on
3. **Context-Aware Intelligence**: The AI has full venue state in every conversation
4. **Production-Ready**: Docker + Cloud Run deployment from day one
5. **Beautiful UX**: Dark mode, animated maps, real-time updates
6. **Lightweight**: Well under 1MB total size

---

*Built with ❤️ using Google Antigravity + Google Gemini 2.0 Flash*
