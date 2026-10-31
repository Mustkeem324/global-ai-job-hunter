import pytest
from fastapi.testclient import TestClient
from app.main import app, bootstrap_initial_state

@pytest.fixture(scope="module")
def client():
    bootstrap_initial_state()
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"

def test_get_jobs(client):
    resp = client.get("/api/v1/jobs/")
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert data["total"] >= 1

def test_get_candidate_profile(client):
    resp = client.get("/api/v1/resumes/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert "Mustkeem" in data["full_name"]
    assert "skills" in data

def test_analytics_overview(client):
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_jobs_discovered" in data
    assert "high_match_jobs" in data
