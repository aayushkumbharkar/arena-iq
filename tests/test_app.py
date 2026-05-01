"""
Comprehensive test suite for ElectIQ application.

Tests cover all API endpoints, input validation, security measures,
demo response branches, quiz functionality, translation endpoint,
security headers, ETag support, and edge cases.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app import app, ELECTION_DATA, QUIZ_BANK, get_demo_response


@pytest.fixture
def client():
    """Create a Flask test client with testing mode enabled."""
    app.config["TESTING"] = True
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

    def test_index_contains_lang_select(self, client):
        """Index page should include a language selector for accessibility."""
        response = client.get("/")
        assert b"lang-select" in response.data

    def test_index_has_skip_link(self, client):
        """Index page should have a skip-to-main-content link."""
        response = client.get("/")
        assert b"skip-link" in response.data or b"Skip to main" in response.data


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

    def test_health_lists_google_services(self, client):
        """Health endpoint should enumerate integrated Google services."""
        response = client.get("/api/health")
        data = json.loads(response.data)
        assert "google_services" in data
        services = data["google_services"]
        assert "gemini" in services
        assert "cloud_translation" in services

    def test_health_version_format(self, client):
        """Version string should follow semver format."""
        response = client.get("/api/health")
        data = json.loads(response.data)
        parts = data["version"].split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)


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

    def test_election_data_returns_etag(self, client):
        """Election data endpoint should return an ETag header."""
        response = client.get("/api/election-data")
        assert "ETag" in response.headers

    def test_election_data_etag_is_stable(self, client):
        """ETag should be consistent across multiple requests (content hasn't changed)."""
        r1 = client.get("/api/election-data")
        r2 = client.get("/api/election-data")
        etag1 = r1.headers.get("ETag")
        etag2 = r2.headers.get("ETag")
        assert etag1 is not None
        assert etag1 == etag2  # ETag is deterministic for same content

    def test_election_data_cache_control_header(self, client):
        """Election data should include Cache-Control header."""
        response = client.get("/api/election-data")
        assert "Cache-Control" in response.headers

    def test_voting_methods_count(self, client):
        """Should have at least 4 voting methods."""
        response = client.get("/api/election-data")
        data = json.loads(response.data)
        assert len(data["voting_methods"]) >= 4

    def test_election_types_count(self, client):
        """Should have at least 5 election types."""
        response = client.get("/api/election-data")
        data = json.loads(response.data)
        assert len(data["election_types"]) >= 5


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

    def test_chat_demo_source_label(self, client):
        """Demo mode should label source as 'demo'."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.post("/api/chat", json={"message": "hello"})
            data = json.loads(response.data)
            assert data.get("source") == "demo"

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

    def test_chat_invalid_history_type_ignored(self, client):
        """Non-list history should be handled gracefully."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.post("/api/chat", json={
                "message": "hello",
                "history": "not-a-list",
            })
            assert response.status_code == 200

    def test_chat_xss_sanitized(self, client):
        """HTML/script tags should be escaped in input processing."""
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

    def test_chat_exactly_max_length(self, client):
        """Message at exactly max length should be accepted."""
        with patch("app.GEMINI_API_KEY", ""):
            msg = "a" * 500
            response = client.post("/api/chat", json={"message": msg})
            assert response.status_code == 200


# ── Demo Response Branches ───────────────────────────────────

class TestDemoResponses:
    """Tests for all demo response keyword branches."""

    def test_registration_keywords(self):
        resp = get_demo_response("How do I register to vote?")
        assert "Register" in resp or "registration" in resp.lower()

    def test_process_keywords(self):
        resp = get_demo_response("What are the steps in an election?")
        assert "Step" in resp

    def test_security_keywords(self):
        resp = get_demo_response("Is voting secure?")
        assert "Security" in resp or "secure" in resp.lower()

    def test_method_keywords(self):
        resp = get_demo_response("What is an EVM?")
        assert "EVM" in resp or "Voting Method" in resp

    def test_type_keywords(self):
        resp = get_demo_response("What types of elections exist?")
        assert "National" in resp or "General" in resp

    def test_rights_keywords(self):
        resp = get_demo_response("What are my rights as a voter?")
        assert "Rights" in resp or "NOTA" in resp

    def test_quiz_keywords(self):
        resp = get_demo_response("Give me a quiz")
        assert "Quiz" in resp or "Q1" in resp

    def test_campaign_keywords(self):
        resp = get_demo_response("What are campaign rules?")
        assert "Campaign" in resp or "Code" in resp

    def test_hello_keywords(self):
        resp = get_demo_response("hello")
        assert "Welcome" in resp or "ElectIQ" in resp

    def test_default_response(self):
        resp = get_demo_response("xyzzy random gibberish")
        assert "ElectIQ" in resp

    def test_nota_keyword(self):
        resp = get_demo_response("What is NOTA?")
        assert "NOTA" in resp or "reject" in resp.lower()

    def test_hey_keyword(self):
        resp = get_demo_response("hey there")
        assert "Welcome" in resp or "ElectIQ" in resp


# ── Quiz Endpoint ────────────────────────────────────────────

class TestQuizEndpoint:
    """Tests for the quiz API."""

    def test_quiz_returns_questions(self, client):
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "questions" in data
            assert len(data["questions"]) > 0

    def test_quiz_respects_count_param(self, client):
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=3")
            data = json.loads(response.data)
            assert len(data["questions"]) == 3

    def test_quiz_max_count_capped_at_8(self, client):
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=100")
            data = json.loads(response.data)
            assert len(data["questions"]) <= 8

    def test_quiz_min_count_at_least_1(self, client):
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=0")
            data = json.loads(response.data)
            assert len(data["questions"]) >= 1

    def test_quiz_question_structure(self, client):
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=1")
            data = json.loads(response.data)
            q = data["questions"][0]
            assert "question" in q
            assert "options" in q
            assert "correct" in q
            assert "explanation" in q

    def test_quiz_correct_index_valid(self, client):
        """Correct answer index should be within options range."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz?count=5")
            data = json.loads(response.data)
            for q in data["questions"]:
                assert 0 <= q["correct"] < len(q["options"])

    def test_quiz_source_label(self, client):
        """Quiz source should be labeled."""
        with patch("app.GEMINI_API_KEY", ""):
            response = client.get("/api/quiz")
            data = json.loads(response.data)
            assert "source" in data


# ── Translate Endpoint ────────────────────────────────────────

class TestTranslateEndpoint:
    """Tests for the Google Cloud Translation API endpoint."""

    def test_translate_empty_texts_returns_400(self, client):
        """Empty texts array should return 400."""
        response = client.post("/api/translate", json={"texts": [], "target": "hi"})
        assert response.status_code == 400

    def test_translate_missing_texts_returns_400(self, client):
        """Missing texts field should return 400."""
        response = client.post("/api/translate", json={"target": "hi"})
        assert response.status_code == 400

    def test_translate_invalid_lang_returns_400(self, client):
        """Unsupported language code should return 400."""
        response = client.post("/api/translate", json={"texts": ["hello"], "target": "xx"})
        assert response.status_code == 400

    def test_translate_passthrough_english(self, client):
        """Target=en should pass texts through unchanged."""
        texts = ["hello world", "election process"]
        response = client.post("/api/translate", json={"texts": texts, "target": "en"})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["translations"] == texts
        assert data["source"] == "passthrough"

    def test_translate_no_api_key_passthrough(self, client):
        """Without API key, should return passthrough of original texts."""
        with patch("app.config.TRANSLATE_API_KEY", ""):
            texts = ["voting registration"]
            response = client.post("/api/translate", json={"texts": texts, "target": "hi"})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["translations"] == texts

    def test_translate_too_many_texts_returns_400(self, client):
        """More than 50 texts should be rejected."""
        texts = ["text"] * 51
        response = client.post("/api/translate", json={"texts": texts, "target": "hi"})
        assert response.status_code == 400

    def test_translate_returns_language_name(self, client):
        """Response should include human-readable language name."""
        response = client.post("/api/translate", json={"texts": ["hello"], "target": "en"})
        data = json.loads(response.data)
        assert "language" in data
        assert data["language"] == "English"

    def test_translate_with_api_key_calls_google(self, client):
        """With API key, should call Google Translation API."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": {"translations": [{"translatedText": "नमस्ते"}]}
        }
        mock_resp.raise_for_status = MagicMock()

        with patch("app.config.TRANSLATE_API_KEY", "fake-key"), \
             patch("app.requests.post", return_value=mock_resp) as mock_post:
            response = client.post("/api/translate", json={"texts": ["hello"], "target": "hi"})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["translations"] == ["नमस्ते"]
            assert data["source"] == "google_translate"
            mock_post.assert_called_once()


# ── Data Integrity ───────────────────────────────────────────

class TestDataIntegrity:
    """Tests for election data integrity."""

    def test_quiz_bank_not_empty(self):
        assert len(QUIZ_BANK) >= 5

    def test_quiz_bank_all_have_explanation(self):
        for q in QUIZ_BANK:
            assert "explanation" in q and q["explanation"]

    def test_election_data_quick_facts(self):
        assert len(ELECTION_DATA["quick_facts"]) >= 5

    def test_voter_eligibility_not_empty(self):
        assert len(ELECTION_DATA["voter_info"]["eligibility"]) >= 3

    def test_voter_rights_count(self):
        """Voter rights should have at least 5 items."""
        assert len(ELECTION_DATA["voter_info"]["rights"]) >= 5

    def test_registration_steps_count(self):
        """Registration steps should have at least 4 items."""
        assert len(ELECTION_DATA["voter_info"]["registration_steps"]) >= 4

    def test_process_steps_sequential(self):
        """Process steps should be numbered sequentially from 1."""
        steps = ELECTION_DATA["process_steps"]
        for i, step in enumerate(steps):
            assert step["step"] == i + 1

    def test_voting_methods_have_pros(self):
        """Each voting method should list pros."""
        for method in ELECTION_DATA["voting_methods"]:
            assert "pros" in method and len(method["pros"]) > 0

    def test_election_types_have_frequency(self):
        """Each election type should specify a frequency."""
        for et in ELECTION_DATA["election_types"]:
            assert "frequency" in et and et["frequency"]
