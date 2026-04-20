import pytest
import json
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route(client):
    """Test that the index route returns the HTML frontend."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data

def test_health_route(client):
    """Test the API health check."""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert data['service'] == 'ArenaIQ'

def test_venue_data_route(client):
    """Test the venue data retrieval."""
    response = client.get('/api/venue-data')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'sections' in data
    assert 'A' in data['sections']

def test_chat_no_message(client):
    """Test chat fallback on empty message."""
    response = client.post('/api/chat', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_chat_demo_fallback(client):
    """Test demo response when API key is not present or bypassing Gemini temporarily."""
    import os
    from unittest.mock import patch
    
    with patch('app.GEMINI_API_KEY', ''):
        response = client.post('/api/chat', json={'message': 'where is food'})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'response' in data
        assert 'venue_data' in data
