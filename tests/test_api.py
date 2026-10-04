from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ask_endpoint_returns_full_payload():
    resp = client.post("/api/ask", json={"question": "Will this work?", "qubits": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert data["qubits"] == 3
    assert data["n_answers"] == 8
    assert len(data["steps"]) == data["iterations"] + 1


def test_ask_endpoint_rejects_too_many_qubits():
    resp = client.post("/api/ask", json={"question": "x", "qubits": 99})
    assert resp.status_code == 422  # pydantic field validation


def test_index_serves_html():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Quantum Magic 8-Ball" in resp.text
