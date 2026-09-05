import io
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "healthcare-agentic-chatbot"
    assert "version" in data


def test_get_health_ollama():
    response = client.get("/health/ollama")
    assert response.status_code in (200, 503)
    data = response.json()
    if response.status_code == 200:
        assert data["status"] == "healthy"
        assert "available_models" in data
    else:
        assert "error" in data or "detail" in data


def test_post_chat_validation():
    # Too short question (min_length=3)
    response = client.post("/chat", json={"question": "hi"})
    assert response.status_code == 422


def test_post_chat_grounded():
    payload = {"question": "What are the DASH diet sodium limits for high blood pressure?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "grounded" in data
    assert "abstained" in data
    assert "sources" in data
    assert "retrieval_info" in data


def test_post_chat_abstain():
    payload = {"question": "What is the surgical procedure for pediatric scoliosis?"}
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["abstained"] is True
    assert data["grounded"] is False
    assert "I don't have enough information" in data["answer"]


def test_post_ingest_directory_reprocess():
    # Calling /ingest with no file payload re-processes data/documents/
    response = client.post("/ingest")
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert data["summary"]["documents_processed"] >= 1


def test_post_ingest_invalid_filetype():
    # Try uploading a .txt file instead of .pdf
    files = {"files": ("test.txt", io.BytesIO(b"Hello world"), "text/plain")}
    response = client.post("/ingest", files=files)
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]
