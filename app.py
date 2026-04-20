import os
import json
import logging
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()  # loads .env file locally (ignored by git)
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from flask_talisman import Talisman

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
# Restrict CORS in production, but allow for testing
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Add security headers, but allow inline scripts/styles for our single-page app
# Disable force_https so local tests don't redirect (Render handles HTTPS organically)
Talisman(app, content_security_policy=None, force_https=False)

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Simulated real-time venue data
VENUE_DATA = {
    "sections": {
        "A": {"crowd_level": 85, "wait_time_food": 12, "wait_time_restroom": 8, "capacity": 500, "current": 425},
        "B": {"crowd_level": 45, "wait_time_food": 4, "wait_time_restroom": 3, "capacity": 500, "current": 225},
        "C": {"crowd_level": 92, "wait_time_food": 18, "wait_time_restroom": 14, "capacity": 500, "current": 460},
        "D": {"crowd_level": 30, "wait_time_food": 2, "wait_time_restroom": 2, "capacity": 500, "current": 150},
        "E": {"crowd_level": 67, "wait_time_food": 9, "wait_time_restroom": 7, "capacity": 500, "current": 335},
    },
    "gates": {
        "North Gate": {"status": "open", "queue_length": 120, "estimated_entry_time": 6},
        "South Gate": {"status": "open", "queue_length": 45, "estimated_entry_time": 2},
        "East Gate": {"status": "open", "queue_length": 230, "estimated_entry_time": 11},
        "West Gate": {"status": "closed", "queue_length": 0, "estimated_entry_time": 0},
    },
    "amenities": {
        "Food Court Alpha": {"section": "A", "wait_time": 12, "items": ["Burgers", "Hot Dogs", "Nachos"]},
        "Food Court Beta": {"section": "B", "wait_time": 4, "items": ["Pizza", "Sandwiches", "Fries"]},
        "Food Court Gamma": {"section": "D", "wait_time": 2, "items": ["Sushi", "Salads", "Wraps"]},
        "Snack Bar 1": {"section": "C", "wait_time": 7, "items": ["Popcorn", "Drinks", "Candy"]},
        "Snack Bar 2": {"section": "E", "wait_time": 5, "items": ["Ice Cream", "Pretzels", "Drinks"]},
    },
    "events": [
        {"time": "19:00", "event": "Gates Open", "status": "completed"},
        {"time": "19:30", "event": "Pre-show Entertainment", "status": "completed"},
        {"time": "20:00", "event": "Opening Ceremony", "status": "live"},
        {"time": "20:30", "event": "Main Event - Quarter 1", "status": "upcoming"},
        {"time": "21:15", "event": "Halftime Show", "status": "upcoming"},
        {"time": "22:00", "event": "Main Event - Quarter 2", "status": "upcoming"},
        {"time": "23:00", "event": "Closing Ceremony", "status": "upcoming"},
    ],
    "alerts": [
        {"type": "crowd", "message": "Section C is at 92% capacity. Consider moving to Section D for more space.", "severity": "high"},
        {"type": "traffic", "message": "East Gate has a long queue. South Gate recommended for faster entry.", "severity": "medium"},
        {"type": "food", "message": "Food Court Gamma in Section D has only 2 min wait - great time to grab food!", "severity": "low"},
    ]
}

SYSTEM_PROMPT = """You are ArenaIQ, an intelligent AI assistant for large-scale sporting venue events. You help attendees have the best possible experience by:

1. **Crowd Management**: Providing real-time crowd density information and suggesting less crowded alternatives
2. **Wait Time Optimization**: Giving accurate wait times for food, restrooms, and entry gates
3. **Navigation Assistance**: Helping attendees find the fastest routes to their seats, amenities, and exits
4. **Real-time Alerts**: Proactively notifying about crowd buildups, gate closures, and special opportunities
5. **Personalized Recommendations**: Suggesting optimal times to move, eat, or use facilities based on crowd patterns

Current Venue Status:
""" + json.dumps(VENUE_DATA, indent=2) + """

Always be helpful, concise, and actionable. When giving navigation advice, be specific about which sections, gates, or areas to use. Prioritize attendee safety and comfort. Use emojis sparingly but effectively to make responses more engaging.

If asked about something not venue-related, politely redirect to venue assistance topics."""


@app.route('/')
def index() -> Response:
    """Serve the main frontend application."""
    logger.info("Serving index.html")
    return send_from_directory('static', 'index.html')


@app.route('/api/chat', methods=['POST'])
def chat() -> tuple[Response, int] | Response:
    """
    Handle chat requests from the frontend, process through Gemini AI,
    and return the AI response along with current venue state.
    """
    data: Dict[str, Any] = request.get_json() or {}
    user_message: str = data.get('message', '').strip()
    history: List[Dict[str, str]] = data.get('history', [])
    
    if not user_message:
        logger.warning("Empty message received")
        return jsonify({'error': 'No message provided'}), 400
    
    if not GEMINI_API_KEY:
        logger.info("Demo mode: No API key found")
        return jsonify({
            'response': get_demo_response(user_message),
            'venue_data': VENUE_DATA
        })
    
    try:
        # AI Optimization: Add safety settings and generation config
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        generation_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=500,
        )

        model = genai.GenerativeModel(
            model_name='gemini-2.0-flash',
            system_instruction=SYSTEM_PROMPT,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Build chat history
        chat_history = []
        for msg in history[-10:]:  # Keep last 10 messages for context
            chat_history.append({
                'role': msg['role'],
                'parts': [msg['content']]
            })
        
        logger.info(f"Sending message to Gemini: {user_message[:50]}...")
        chat_session = model.start_chat(history=chat_history)
        response = chat_session.send_message(user_message)
        
        return jsonify({
            'response': response.text,
            'venue_data': VENUE_DATA
        })
    except Exception as e:
        logger.error(f"Gemini API Error: {str(e)}")
        return jsonify({
            'response': f"I'm having trouble connecting right now. {get_demo_response(user_message)}",
            'venue_data': VENUE_DATA
        }), 500


def get_demo_response(message: str) -> str:
    """Smart demo responses when API key is not configured."""
    msg_lower = message.lower()
    
    if any(w in msg_lower for w in ['crowd', 'busy', 'packed', 'full']):
        return "📊 **Current Crowd Status**: Section D is your best bet right now at only 30% capacity! Section C is critically high at 92% — I'd steer clear. Section B (45%) and E (67%) are also good options. Want me to help you navigate to a less crowded spot?"
    
    elif any(w in msg_lower for w in ['food', 'eat', 'hungry', 'drink', 'snack']):
        return "🍔 **Best Food Options Right Now**:\n• **Food Court Gamma** (Section D) — only **2 min wait!** Great selection\n• **Food Court Beta** (Section B) — 4 min wait, Pizza & Sandwiches\n• **Snack Bar 2** (Section E) — 5 min wait, Ice Cream & Pretzels\n\nAvoid Food Court Alpha and Section C — waiting 12-18 minutes there!"
    
    elif any(w in msg_lower for w in ['restroom', 'bathroom', 'toilet']):
        return "🚻 **Restroom Wait Times**:\n• Section D — **2 min wait** ✅ Best option!\n• Section B — 3 min wait ✅\n• Section A — 8 min wait ⚠️\n• Section C — 14 min wait ❌ Avoid!\n\nHead to Section D for the fastest experience."
    
    elif any(w in msg_lower for w in ['gate', 'enter', 'entry', 'exit']):
        return "🚪 **Gate Status**:\n• **South Gate** — 45 people queuing, ~2 min entry ✅ BEST OPTION\n• North Gate — 120 queuing, ~6 min ⚠️\n• East Gate — 230 queuing, ~11 min ❌\n• West Gate — Currently **CLOSED**\n\nUse South Gate for fastest access!"
    
    elif any(w in msg_lower for w in ['schedule', 'event', 'what', 'when', 'next']):
        return "📅 **Event Schedule**:\n• ✅ 19:00 — Gates Open\n• ✅ 19:30 — Pre-show Entertainment  \n• 🔴 **LIVE NOW: 20:00 — Opening Ceremony**\n• ⏳ 20:30 — Main Event Quarter 1\n• ⏳ 21:15 — Halftime Show\n• ⏳ 22:00 — Main Event Quarter 2\n• ⏳ 23:00 — Closing Ceremony"
    
    elif any(w in msg_lower for w in ['seat', 'find', 'where', 'navigate', 'section']):
        return "🗺️ **Navigation Tips**:\n• Your section letter is on your ticket\n• Use the interactive map above to see crowd density\n• Currently **Section D** has most space and shortest lines\n• Corridors between sections are clearly marked\n\nWhich section are you trying to reach? I can give you a specific route!"
    
    elif any(w in msg_lower for w in ['parking', 'car', 'vehicle']):
        return "🚗 **Parking Advice**:\n• Lot B (South) is 40% full — closest to South Gate (fastest entry!)\n• Lot A (North) is 75% full\n• Lot C (East) is 90% full — very congested\n\n💡 **Pro tip**: Plan to leave 20 minutes before the final buzzer to beat traffic!"
    
    elif any(w in msg_lower for w in ['help', 'hi', 'hello', 'hey', 'start']):
        return "👋 **Welcome to ArenaIQ!** I'm your intelligent venue assistant. I can help you with:\n\n• 📊 **Real-time crowd levels** by section\n• 🍔 **Food & drink** wait times\n• 🚻 **Restroom** availability\n• 🚪 **Gate** entry times\n• 🗺️ **Navigation** to your seat\n• 📅 **Event schedule** & updates\n• 🚨 **Live alerts** & recommendations\n\nWhat can I help you with today?"
    
    else:
        return "🏟️ I'm ArenaIQ, your smart venue assistant! I can help with crowd levels, food options, restrooms, gates, navigation, and event schedules. What would you like to know?\n\n**Quick tip**: Right now, **Section D** is the least crowded and **South Gate** has the shortest queue!"


@app.route('/api/venue-data', methods=['GET'])
def venue_data() -> Response:
    """Returns current venue data for the dashboard."""
    return jsonify(VENUE_DATA)


@app.route('/api/health', methods=['GET'])
def health() -> Response:
    """Health check endpoint for container orchestration readiness."""
    return jsonify({'status': 'healthy', 'service': 'ArenaIQ', 'version': '1.0.0'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
