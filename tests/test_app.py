"""
Comprehensive test suite for ElectIQ application.

Tests cover all API endpoints, input validation, security measures,
demo response branches, quiz functionality, and edge cases.
"""

import json
import pytest
from unittest.mock import patch

from app import app, ELECTION_DATA, QUIZ_BANK, get_demo_response


@pytest.fixture
def client():
    """Create a Flask test client with testing mode enabled."""
    app.config["TESTING"] = True
    # Disable rate limiter for testing
    app.config["RATELIMIT_ENABLED"] = False
    with app.test_client() as test_client:
        yield test_client


# ── Index Route ──────────────────────────────────────────────

class TestIndexRoute:
    """Tests for the main page route."""

    def test_index_returns_html(self, client):
        """Index route should return the HTML frontend."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data

    def test_index_contains_electiq(self, client):
        """Index page should contain the ElectIQ branding."""
        response = client.get("/")
        assert b"ElectIQ" in response.data


# ── Health Endpoint ──────────────────────────────────────────

class TestHealthEndpoint:
    """Tests for the health check API."""

    def test_health_returns_ok(self, client):
        """Health endpoint should return 200 with correct fields."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "ElectIQ"
        assert "version" in data


# ── Election Data Endpoint ───────────────────────────────────

class TestElectionDataEndpoint:
    """Tests for the election data API."""

    def test_election_data_structure(self, client):
        """Election data should contain all required sections."""
        response = client.get("/api/election-data")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "process_steps" in data
        assert "voting_methods" in data
        assert "election_types" in data
        assert "voter_info" in data
        assert "quick_facts" in data

    def test_election_data_has_seven_steps(self, client):
        """Election process should have exactly 7 steps."""
        response = client.get("/api/election-data")
        data = json.loads(response.data)
        assert len(data["process_steps"]) == 7

    def test_each_step_has_required_fields(self, client):
        """Each process step should have step, title, description, icon."""
        response = client.get("/api/election-data")
        data = json.loads(response.data)
        for step in data["process_steps"]:
            assert "step" in step
            assert "title" in step
            assert "description" in step
            assert "icon" in step


# ── Chat Endpoint ────────────────────────────────────────────

class TestChatEndpoint:
    """Tests for the chat API."""

    def test_chat_empty_message_returns_400(self, client):
        """Empty message should return 400 error."""
        response = client.post("/api/chat", json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_chat_blank_message_returns_400(self, client):
        """Whitespace-only message should return 400."""
        response = client.post("/api/chat", json={"message": "   "})
        assert response.status_code == 400

    def test_chat_too_long_message_returns_400(self, client):
        """Messages exceeding max length should be rejected."""
        long_msg = "a" * 501
        response = client.post("/api/chat", json={"message": long_msg})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "too long" in data["error"].lower() or "max" in data["error"].lower()

    def test_chat_demo_mode(self, client):
        """Chat should return demo response when API key is absent."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.post("/api/chat", json={"message": "hello"})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "response" in data

    def test_chat_demo_with_history(self, client):
        """Chat should accept history parameter without errors."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.post("/api/chat", json={
                "message": "tell me about voting",
                "history": [
                    {"role": "user", "content": "hi"},
                    {"role": "model", "content": "Hello!"},
                ],
            })
            assert response.status_code == 200

    def test_chat_xss_sanitized(self, client):
        """HTML/script tags should be escaped in responses."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.post("/api/chat", json={
                "message": "<script>alert('xss')</script>"
            })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "<script>" not in data["response"]

    def test_chat_malformed_json(self, client):
        """Non-JSON request body should be handled gracefully."""
        response = client.post(
            "/api/chat",
            data="not json",
            content_type="text/plain",
        )
        assert response.status_code == 400


# ── Demo Response Branches ───────────────────────────────────

class TestDemoResponses:
    """Tests for all demo response keyword branches."""

    def test_registration_keywords(self):
        """Registration keywords should return registration info."""
        resp = get_demo_response("How do I register to vote?")
        assert "Register" in resp or "registration" in resp.lower()

    def test_process_keywords(self):
        """Process keywords should return election steps."""
        resp = get_demo_response("What are the steps in an election?")
        assert "Step" in resp

    def test_security_keywords(self):
        """Security keywords should return security measures."""
        resp = get_demo_response("Is voting secure?")
        assert "Security" in resp or "secure" in resp.lower()

    def test_method_keywords(self):
        """Method keywords should return voting methods."""
        resp = get_demo_response("What is an EVM?")
        assert "EVM" in resp or "Voting Method" in resp

    def test_type_keywords(self):
        """Type keywords should return election types."""
        resp = get_demo_response("What types of elections exist?")
        assert "National" in resp or "General" in resp

    def test_rights_keywords(self):
        """Rights keywords should return voter rights."""
        resp = get_demo_response("What are my rights as a voter?")
        assert "Rights" in resp or "NOTA" in resp

    def test_quiz_keywords(self):
        """Quiz keywords should return quiz questions."""
        resp = get_demo_response("Give me a quiz")
        assert "Quiz" in resp or "Q1" in resp

    def test_campaign_keywords(self):
        """Campaign keywords should return campaign rules."""
        resp = get_demo_response("What are campaign rules?")
        assert "Campaign" in resp or "Code" in resp

    def test_hello_keywords(self):
        """Greeting keywords should return welcome message."""
        resp = get_demo_response("hello")
        assert "Welcome" in resp or "ElectIQ" in resp

    def test_default_response(self):
        """Unknown input should return a helpful default."""
        resp = get_demo_response("xyzzy random gibberish")
        assert "ElectIQ" in resp


# ── Quiz Endpoint ────────────────────────────────────────────

class TestQuizEndpoint:
    """Tests for the quiz API."""

    def test_quiz_returns_questions(self, client):
        """Quiz endpoint should return questions array."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "questions" in data
            assert len(data["questions"]) > 0

    def test_quiz_respects_count_param(self, client):
        """Quiz should return the requested number of questions."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=3")
            data = json.loads(response.data)
            assert len(data["questions"]) == 3

    def test_quiz_question_structure(self, client):
        """Each quiz question should have required fields."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=1")
            data = json.loads(response.data)
            q = data["questions"][0]
            assert "question" in q
            assert "options" in q
            assert "correct" in q


# ── Data Integrity ───────────────────────────────────────────

class TestDataIntegrity:
    """Tests for election data integrity."""

    def test_quiz_bank_not_empty(self):
        """Quiz bank should have questions."""
        assert len(QUIZ_BANK) >= 5

    def test_election_data_quick_facts(self):
        """Quick facts should have multiple entries."""
        assert len(ELECTION_DATA["quick_facts"]) >= 5

    def test_voter_eligibility_not_empty(self):
        """Voter eligibility criteria should be defined."""
        assert len(ELECTION_DATA["voter_info"]["eligibility"]) >= 3
