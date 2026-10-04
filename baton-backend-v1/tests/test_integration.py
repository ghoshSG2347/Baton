from fastapi.testclient import TestClient
from app.main import app
def test_integration():
 r=TestClient(app).post("/api/v1/integration",json={"owner":"o","repo":"r","branch":"main"}); assert r.status_code==200
