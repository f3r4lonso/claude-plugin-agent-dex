import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from agent_dex.main import create_app

from .conftest import AUTH, HOST, TOKEN


def client(settings):
    return TestClient(create_app(settings, TOKEN, static_dir=None))


def test_api_requires_token(settings):
    c = client(settings)
    assert c.get("/api/dex", headers=HOST).status_code == 401
    assert c.get("/api/dex", headers={**HOST, "Authorization": "Bearer nope"}).status_code == 401
    assert c.get("/api/dex", headers=AUTH).status_code == 200


def test_health_is_open_and_has_security_headers(settings):
    r = client(settings).get("/api/health", headers=HOST)
    assert r.status_code == 200
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert r.headers["x-content-type-options"] == "nosniff"


def test_rejects_unknown_host(settings):
    r = client(settings).get("/api/health", headers={"Host": "evil.example:8771"})
    assert r.status_code == 403


def test_rejects_foreign_origin_even_with_token(settings):
    r = client(settings).get("/api/dex", headers={**AUTH, "Origin": "https://evil.example"})
    assert r.status_code == 403


def test_hook_needs_json_post_without_origin(settings):
    c = client(settings)
    body = '{"hook_event_name":"SubagentStart","agent_type":"reviewer","agent_id":"a1"}'
    plain = {**HOST, "Content-Type": "text/plain"}
    assert c.post("/api/hook", content=body, headers=plain).status_code == 403
    foreign = {**HOST, "Content-Type": "application/json", "Origin": "https://evil.example"}
    assert c.post("/api/hook", content=body, headers=foreign).status_code == 403
    json_headers = {**HOST, "Content-Type": "application/json"}
    assert c.post("/api/hook", content=body, headers=json_headers).status_code == 200
    assert c.get("/api/status", headers=AUTH).json()["reviewer"]["state"] == "trabajando"
    c.post("/api/hook", content=body.replace("SubagentStart", "SubagentStop"), headers=json_headers)
    assert c.get("/api/status", headers=AUTH).json()["reviewer"]["state"] == "inactivo"


def test_websocket_requires_token(settings):
    c = TestClient(create_app(settings, TOKEN, static_dir=None), headers=HOST)
    with pytest.raises(WebSocketDisconnect), c.websocket_connect("/ws"):
        pass
    with c.websocket_connect(f"/ws?t={TOKEN}") as ws:
        assert ws.receive_json()["topic"] == "hello"
