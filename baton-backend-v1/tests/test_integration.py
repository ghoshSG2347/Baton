from fastapi.testclient import TestClient
from app.main import app
from app.services.integration_service import compare, normalize_endpoint
from unittest.mock import AsyncMock, patch

client = TestClient(app)

def test_integration_single_branch_ready():
    r = client.post("/api/v1/integration", json={"owner": "o", "repo": "r", "branch": "main"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ready"
    assert "Provide frontend_branch and backend_branch" in data["message"]

def test_normalize_endpoint():
    assert normalize_endpoint("src/api/client.ts: /api/users") == "/api/users"
    assert normalize_endpoint("app/routes.py: get /api/items") == "GET /api/items"
    assert normalize_endpoint("app/routes.py: POST /api/items") == "POST /api/items"
    assert normalize_endpoint("/api/orders") == "/api/orders"
    assert normalize_endpoint("") == ""

def test_compare_integration_matching():
    # Frontend has API calls extracted by api_analyzer
    frontend_analysis = {
        "api_calls": [
            "src/components/UserList.tsx: /api/users",
            "src/components/OrderList.tsx: /api/orders",
        ],
        "routes": [],
    }
    # Backend has routes extracted by api_analyzer
    backend_analysis = {
        "routes": [
            "app/api/routes/users.py: /api/users",
            "app/api/routes/orders.py: /api/orders",
            "app/api/routes/health.py: /health",
        ],
        "api_calls": [],
    }

    comp = compare(frontend_analysis, backend_analysis)
    assert comp["frontend_routes"] == ["/api/orders", "/api/users"]
    assert comp["backend_routes"] == ["/api/orders", "/api/users", "/health"]
    assert comp["unmatched_frontend_routes"] == []
    assert comp["unmatched_backend_routes"] == ["/health"]
    assert comp["compatible"] is True

def test_compare_integration_unmatched_frontend():
    frontend_analysis = {
        "api_calls": ["src/api.ts: /api/missing-endpoint"],
        "routes": [],
    }
    backend_analysis = {
        "routes": ["app/api.py: /api/existing-endpoint"],
        "api_calls": [],
    }

    comp = compare(frontend_analysis, backend_analysis)
    assert comp["unmatched_frontend_routes"] == ["/api/missing-endpoint"]
    assert comp["unmatched_backend_routes"] == ["/api/existing-endpoint"]
    assert comp["compatible"] is False

@patch("app.api.routes.integration.AnalysisService")
def test_dual_branch_integration_endpoint(mock_service_class):
    mock_instance = mock_service_class.return_value
    mock_instance.analyze = AsyncMock()
    mock_instance.analyze.side_effect = [
        {"routes": [], "api_calls": ["src/api.ts: /api/v1/data"]},  # frontend branch
        {"routes": ["app/routes.py: /api/v1/data"], "api_calls": []},  # backend branch
    ]

    r = client.post(
        "/api/v1/integration",
        json={
            "owner": "org",
            "repo": "project",
            "branch": "main",
            "frontend_branch": "feature/frontend",
            "backend_branch": "feature/backend",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "analyzed"
    assert data["comparison"]["compatible"] is True
    assert data["comparison"]["frontend_routes"] == ["/api/v1/data"]
    assert data["comparison"]["backend_routes"] == ["/api/v1/data"]
