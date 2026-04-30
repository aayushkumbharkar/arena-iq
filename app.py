"""
ElectIQ — AI-Powered Election Process Education Platform

A Flask web application that educates citizens about the democratic
election process using Google Gemini AI. Features an interactive chat
assistant, election process timeline, voter guides, and AI-generated quizzes.

Google Services Used:
    - Google Gemini 2.0 Flash (AI chat + quiz generation)
    - Google Cloud Logging (structured logging, auto-detected on Cloud Run)
    - Google Fonts (Inter + Space Grotesk)
"""

import os
import json
import logging
from typing import Dict, Any, List

from dotenv import load_dotenv

load_dotenv()

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core import retry as api_retry

from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_compress import Compress
from markupsafe import escape

from config import get_config

# ────────────────────────────────────────────────────────────
#  Logging — Google Cloud Logging if available, else stdlib
# ────────────────────────────────────────────────────────────
try:
    import google.cloud.logging as cloud_logging

    cloud_client = cloud_logging.Client()
    cloud_client.setup_logging()
    logging.info("Google Cloud Logging active")
except Exception:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────
#  App Initialisation
# ────────────────────────────────────────────────────────────
config = get_config()

app = Flask(__name__, static_folder="static")
app.config["SECRET_KEY"] = config.SECRET_KEY

CORS(app, resources={r"/api/*": {"origins": "*"}})

Talisman(
    app,
    content_security_policy=None,
    force_https=False,
    strict_transport_security=True,
)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[config.RATE_LIMIT_DEFAULT],
    storage_uri="memory://",
)

Compress(app)

cache = Cache(
    config={
        "CACHE_TYPE": config.CACHE_TYPE,
        "CACHE_DEFAULT_TIMEOUT": config.CACHE_DEFAULT_TIMEOUT,
    }
)
cache.init_app(app)

# ────────────────────────────────────────────────────────────
#  Gemini Configuration
# ────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = config.GEMINI_API_KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    logger.info("Gemini API configured")

# ────────────────────────────────────────────────────────────
#  Election Education Data
# ────────────────────────────────────────────────────────────
ELECTION_DATA: Dict[str, Any] = {
    "process_steps": [
        {
            "step": 1,
            "title": "Election Announcement",
            "description": "The Election Commission announces the schedule and the Model Code of Conduct comes into effect.",
            "details": "The ruling government cannot announce new policies to prevent voter influence. Key dates for nominations, campaigning, and polling are published.",
            "icon": "📢",
        },
        {
            "step": 2,
            "title": "Voter Registration",
            "description": "Eligible citizens register on the electoral roll to receive their voter ID.",
            "details": "Citizens must be 18+, hold citizenship, and reside in the constituency. Registration can be done online or at local offices.",
            "icon": "📝",
        },
        {
            "step": 3,
            "title": "Nomination of Candidates",
            "description": "Candidates file nominations with required documents and a security deposit.",
            "details": "Nominations are scrutinized for eligibility. Candidates may withdraw before the deadline. Final lists are published.",
            "icon": "🏛️",
        },
        {
            "step": 4,
            "title": "Election Campaign",
            "description": "Candidates campaign through rallies, ads, door-to-door visits, and social media.",
            "details": "Spending is regulated. Campaigning must stop 48 hours before polling (silence period). Hate speech and bribery are prohibited.",
            "icon": "📣",
        },
        {
            "step": 5,
            "title": "Polling Day",
            "description": "Registered voters visit designated polling stations to cast their vote.",
            "details": "Voters carry valid ID. Booths ensure ballot secrecy. Special provisions exist for disabled and senior voters.",
            "icon": "🗳️",
        },
        {
            "step": 6,
            "title": "Vote Counting",
            "description": "Votes are securely transported and counted under strict supervision.",
            "details": "Counting is observed by candidates' agents. EVM tallies are electronic. VVPAT slips can be audited.",
            "icon": "📊",
        },
        {
            "step": 7,
            "title": "Results & Government Formation",
            "description": "Results are declared, winners announced, and elected representatives take oath.",
            "details": "First-past-the-post: most votes wins. Majority party/coalition forms government. Results are publicly available in real-time.",
            "icon": "🏆",
        },
    ],
    "voting_methods": [
        {
            "name": "Electronic Voting Machine (EVM)",
            "description": "Portable battery-powered device with one button per candidate.",
            "pros": ["Fast and accurate", "Eliminates invalid votes", "Tamper-resistant"],
            "icon": "💻",
        },
        {
            "name": "Paper Ballot",
            "description": "Voters mark their choice on printed paper placed in a sealed box.",
            "pros": ["Simple to understand", "No technology needed", "Physical trail"],
            "icon": "📄",
        },
        {
            "name": "Postal / Mail-in Ballot",
            "description": "Ballots received and returned by mail for remote or mobility-impaired voters.",
            "pros": ["Remote accessibility", "Extended timeframe", "Convenient"],
            "icon": "📮",
        },
        {
            "name": "VVPAT (Voter Verified Paper Audit Trail)",
            "description": "EVM attachment printing a slip of the voter's choice for 7 seconds.",
            "pros": ["Adds EVM transparency", "Physical verification", "Strengthens trust"],
            "icon": "🧾",
        },
    ],
    "election_types": [
        {"name": "General / National", "description": "Elects national legislature members.", "frequency": "Every 4–5 years", "icon": "🏛️"},
        {"name": "State / Provincial", "description": "Forms state or provincial legislatures.", "frequency": "Every 4–5 years", "icon": "🏢"},
        {"name": "Local / Municipal", "description": "City councils, mayors, village heads.", "frequency": "Every 3–5 years", "icon": "🏘️"},
        {"name": "By-Elections", "description": "Fills seats vacant by death, resignation, or disqualification.", "frequency": "As needed", "icon": "🔄"},
        {"name": "Referendum", "description": "Direct public vote on a specific policy question.", "frequency": "As needed", "icon": "📋"},
    ],
    "voter_info": {
        "eligibility": [
            "Must be a citizen of the country",
            "Must be at least 18 years old",
            "Must reside in the constituency",
            "Must not be disqualified under law",
            "Must be on the electoral roll",
        ],
        "registration_steps": [
            "Visit the Election Commission website or local office",
            "Fill the voter registration form (Form 6 in India)",
            "Provide proof of identity (passport, licence, Aadhaar)",
            "Provide proof of address (utility bill, bank statement)",
            "Submit a passport-sized photograph",
            "Receive your Voter ID (EPIC) after verification",
        ],
        "rights": [
            "Right to vote by secret ballot",
            "Right to know candidates' backgrounds",
            "Right to reject all candidates (NOTA)",
            "Right to accessible polling stations",
            "Right to assistance if physically challenged",
            "Right to complain about electoral malpractice",
        ],
    },
    "quick_facts": [
        "India has the largest electorate — over 960 million registered voters.",
        "The first known election was held in Athens around 508 BC.",
        "Women gained voting rights in New Zealand first, in 1893.",
        "Compulsory voting exists in 21 countries including Australia.",
        "The word 'ballot' comes from Italian 'ballotta' — a small ball for secret voting.",
        "In India, a polling station must be within 2 km of every voter's home.",
        "The longest ballot ever was 15 feet long, used in Iraq's 2010 elections.",
        "The shortest election campaign was 9 days in the UK in 1918.",
    ],
}

# ────────────────────────────────────────────────────────────
#  Gemini System Prompt
# ────────────────────────────────────────────────────────────
SYSTEM_PROMPT: str = (
    "You are ElectIQ, an AI election process education assistant. "
    "Your mission: help citizens understand democratic elections, voting rights, and civic participation.\n\n"
    "You know about: election processes, voter registration, voting methods (EVM, ballot, postal, VVPAT), "
    "election types, voter rights, election security, campaign rules, and electoral systems.\n\n"
    "Election Knowledge Base:\n" + json.dumps(ELECTION_DATA, indent=2) + "\n\n"
    "Rules:\n"
    "- Be accurate, unbiased, non-partisan\n"
    "- Use simple language for first-time voters\n"
    "- Encourage civic participation\n"
    "- Use emojis sparingly\n"
    "- Redirect non-election questions politely\n"
    "- Cite official sources when possible"
)


# ────────────────────────────────────────────────────────────
#  Demo Responses
# ────────────────────────────────────────────────────────────
def get_demo_response(message: str) -> str:
    """Return a contextual demo response when Gemini API is unavailable."""
    msg: str = message.lower()

    if any(w in msg for w in ["register", "registration", "sign up", "voter id"]):
        return (
            "📝 **How to Register to Vote:**\n\n"
            "1. Visit your Election Commission website or local office\n"
            "2. Fill the voter registration form\n"
            "3. Provide **proof of identity** (passport, licence, national ID)\n"
            "4. Provide **proof of address** (utility bill, bank statement)\n"
            "5. Submit a passport-sized photograph\n"
            "6. Receive your **Voter ID** after verification\n\n"
            "📌 **Eligibility**: 18+ years, citizen, resident of constituency.\n\n"
            "Would you like more details on documents or eligibility?"
        )

    if any(w in msg for w in ["process", "steps", "how does", "procedure"]):
        lines = [f"{s['icon']} **Step {s['step']}: {s['title']}** — {s['description']}" for s in ELECTION_DATA["process_steps"]]
        return "🗳️ **The Election Process:**\n\n" + "\n\n".join(lines) + "\n\nAsk about any step for more detail!"

    if any(w in msg for w in ["secure", "security", "safe", "fraud", "tamper", "hack"]):
        return (
            "🔒 **Election Security Measures:**\n\n"
            "• **Sealed EVMs** — signed by candidates' agents\n"
            "• **VVPAT** — paper trail for electronic votes\n"
            "• **Randomized deployment** of machines\n"
            "• **CCTV** and observer supervision during counting\n"
            "• **Mock polls** verify machine integrity\n"
            "• **Indelible ink** prevents duplicate voting\n\n"
            "Want to know more about any security measure?"
        )

    if any(w in msg for w in ["method", "evm", "ballot", "postal", "vvpat"]):
        lines = [f"{m['icon']} **{m['name']}** — {m['description']}" for m in ELECTION_DATA["voting_methods"]]
        return "🗳️ **Voting Methods:**\n\n" + "\n\n".join(lines) + "\n\nAsk about any method for details!"

    if any(w in msg for w in ["type", "kinds", "general", "national", "state", "local"]):
        lines = [f"{t['icon']} **{t['name']}** ({t['frequency']}) — {t['description']}" for t in ELECTION_DATA["election_types"]]
        return "🏛️ **Types of Elections:**\n\n" + "\n\n".join(lines)

    if any(w in msg for w in ["right", "nota", "accessible"]):
        lines = [f"✅ {r}" for r in ELECTION_DATA["voter_info"]["rights"]]
        return "⚖️ **Your Voter Rights:**\n\n" + "\n".join(lines) + "\n\n💡 NOTA lets you reject all candidates while still participating!"

    if any(w in msg for w in ["quiz", "test", "knowledge"]):
        return (
            "🧠 **Quick Election Quiz!**\n\n"
            "**Q1:** Minimum voting age in most democracies?\n"
            "A) 16  B) 18  C) 21  D) 25\n\n"
            "**Q2:** What does NOTA stand for?\n"
            "A) Not On The Agenda  B) None Of The Above  C) National Option  D) No One To Accept\n\n"
            "**Q3:** Purpose of VVPAT?\n"
            "A) Speed up counting  B) Verify identity  C) Paper trail for e-votes  D) Prevent proxy voting\n\n"
            "💡 *Answers: B, B, C*\n\nWant more questions?"
        )

    if any(w in msg for w in ["campaign", "rules", "code", "conduct"]):
        return (
            "📣 **Campaign Rules:**\n\n"
            "• **Model Code of Conduct** activates on election announcement\n"
            "• **Spending limits** for all candidates\n"
            "• **48-hour silence period** before polling\n"
            "• **No bribery**, intimidation, or hate speech\n"
            "• Social media campaigns are monitored\n\n"
            "Want to know more about any rule?"
        )

    if any(w in msg for w in ["help", "hi", "hello", "hey", "start"]):
        return (
            "👋 **Welcome to ElectIQ!** I'm your election education assistant.\n\n"
            "I can help with:\n"
            "• 📝 **Voter Registration** — How to register\n"
            "• 🗳️ **Election Process** — Step-by-step guide\n"
            "• 🔒 **Election Security** — How votes are protected\n"
            "• 📊 **Voting Methods** — EVMs, ballots, postal\n"
            "• 🏛️ **Election Types** — National, state, local\n"
            "• ⚖️ **Voter Rights** — NOTA, accessibility\n"
            "• 🧠 **Quiz** — Test your knowledge!\n\n"
            "What would you like to learn?"
        )

    return (
        "🗳️ I'm **ElectIQ**, your election education assistant!\n\n"
        "Ask me about voter registration, election processes, voting methods, "
        "your rights, or take a quiz!\n\n"
        "💡 **Did you know?** " + ELECTION_DATA["quick_facts"][0]
    )


# ────────────────────────────────────────────────────────────
#  Quiz Bank (fallback)
# ────────────────────────────────────────────────────────────
QUIZ_BANK: List[Dict[str, Any]] = [
    {"question": "What is the minimum voting age in most democracies?", "options": ["16", "18", "21", "25"], "correct": 1, "explanation": "18 is standard in most countries."},
    {"question": "What does NOTA stand for?", "options": ["Not On The Agenda", "None Of The Above", "National Option To Abstain", "No One To Accept"], "correct": 1, "explanation": "NOTA lets voters reject all candidates."},
    {"question": "What is VVPAT?", "options": ["Voter ID type", "Paper audit trail for EVMs", "Online voting system", "Campaign document"], "correct": 1, "explanation": "VVPAT prints a slip confirming the voter's EVM choice."},
    {"question": "When must campaigning stop before polling?", "options": ["24 hours", "48 hours", "72 hours", "1 week"], "correct": 1, "explanation": "The 48-hour silence period ensures voters decide without last-minute pressure."},
    {"question": "Which country granted women's suffrage first?", "options": ["USA", "UK", "New Zealand", "France"], "correct": 2, "explanation": "New Zealand granted women voting rights in 1893."},
    {"question": "What prevents a person from voting twice?", "options": ["Voter ID only", "Indelible ink", "Facial recognition", "Fingerprint scan"], "correct": 1, "explanation": "Indelible ink on the finger marks that a person has already voted."},
    {"question": "Who conducts elections in India?", "options": ["Supreme Court", "Parliament", "Election Commission", "President"], "correct": 2, "explanation": "The Election Commission of India is an autonomous constitutional body."},
    {"question": "What is a by-election?", "options": ["Annual election", "Election to fill a vacant seat", "Presidential election", "Party internal election"], "correct": 1, "explanation": "By-elections fill seats vacated by death, resignation, or disqualification."},
]


# ────────────────────────────────────────────────────────────
#  Routes
# ────────────────────────────────────────────────────────────
@app.route("/")
def index() -> Response:
    """Serve the single-page frontend application."""
    logger.info("Serving index page")
    return send_from_directory("static", "index.html")


@app.route("/api/chat", methods=["POST"])
@limiter.limit(config.RATE_LIMIT_CHAT)
def chat() -> tuple[Response, int] | Response:
    """
    Process user messages through Gemini AI for election education.

    Accepts JSON with 'message' and optional 'history'. Validates input
    length and returns AI-generated or demo responses about elections.
    """
    data: Dict[str, Any] = request.get_json(silent=True) or {}
    user_message: str = data.get("message", "").strip()
    history: List[Dict[str, str]] = data.get("history", [])

    # Input validation
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    if len(user_message) > config.MAX_MESSAGE_LENGTH:
        return jsonify({"error": f"Message too long (max {config.MAX_MESSAGE_LENGTH} chars)"}), 400

    # Sanitise input
    user_message = str(escape(user_message))

    if not GEMINI_API_KEY:
        logger.info("Demo mode response")
        return jsonify({"response": get_demo_response(user_message), "source": "demo"})

    try:
        safety = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        gen_config = genai.types.GenerationConfig(
            temperature=config.GEMINI_TEMPERATURE,
            max_output_tokens=config.GEMINI_MAX_TOKENS,
        )

        model = genai.GenerativeModel(
            model_name=config.GEMINI_MODEL,
            system_instruction=SYSTEM_PROMPT,
            generation_config=gen_config,
            safety_settings=safety,
        )

        chat_history = [
            {"role": m["role"], "parts": [m["content"]]}
            for m in history[-10:]
        ]

        session = model.start_chat(history=chat_history)
        retry_policy = api_retry.Retry(initial=1.0, maximum=10.0, multiplier=2.0, deadline=30.0)
        response = retry_policy(session.send_message)(user_message)

        return jsonify({"response": response.text, "source": "gemini"})

    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        return jsonify({
            "response": f"I'm having a brief connection issue. {get_demo_response(user_message)}",
            "source": "fallback",
        }), 500


@app.route("/api/quiz", methods=["GET"])
@cache.cached(timeout=60, query_string=True)
def quiz() -> Response:
    """
    Return election quiz questions.

    Attempts to generate fresh questions via Gemini; falls back to
    the built-in quiz bank if the API is unavailable.
    """
    count = min(int(request.args.get("count", 5)), 8)

    if GEMINI_API_KEY:
        try:
            model = genai.GenerativeModel(config.GEMINI_MODEL)
            prompt = (
                f"Generate {count} multiple-choice quiz questions about democratic election processes. "
                "Return ONLY valid JSON array. Each object: "
                '{"question":"...","options":["A","B","C","D"],"correct":0-3,"explanation":"..."}'
            )
            resp = model.generate_content(prompt)
            text = resp.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            questions = json.loads(text)
            return jsonify({"questions": questions[:count], "source": "gemini"})
        except Exception as exc:
            logger.warning("Quiz generation fallback: %s", exc)

    import random
    questions = random.sample(QUIZ_BANK, min(count, len(QUIZ_BANK)))
    return jsonify({"questions": questions, "source": "bank"})


@app.route("/api/election-data", methods=["GET"])
@cache.cached(timeout=30)
def election_data() -> Response:
    """Return the election education dataset for frontend panels."""
    return jsonify(ELECTION_DATA)


@app.route("/api/health", methods=["GET"])
def health() -> Response:
    """Health check for container orchestration."""
    return jsonify({
        "status": "healthy",
        "service": config.APP_NAME,
        "version": config.APP_VERSION,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
