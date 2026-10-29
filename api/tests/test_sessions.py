import time

import pytest

from .conftest import make_client, result, simple_script, writing_script


def agent_id(client, name="reviewer"):
    return next(r["id"] for r in client.get("/api/dex").json()["resources"] if r["name"] == name)


def until(fn, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        value = fn()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("timeout")


def wait(client, sid, states):
    return until(lambda: (s := client.get(f"/api/sessions/{sid}").json())["status"] in states and s)


def start_chat(client):
    s = client.post("/api/sessions", json={"agent_id": agent_id(client), "kind": "chat"}).json()
    wait(client, s["id"], {"idle"})
    return s


def test_chat_roundtrip_and_options(settings):
    client, _, created = make_client(settings, simple_script)
    with client:
        s = client.post(
            "/api/sessions",
            json={"agent_id": agent_id(client), "kind": "chat", "max_turns": 50, "max_budget_usd": 5},
        ).json()
        wait(client, s["id"], {"idle"})
        assert client.post(f"/api/sessions/{s['id']}/message", json={"text": "hola"}).status_code == 200
        done = until(
            lambda: (
                (d := client.get(f"/api/sessions/{s['id']}").json())["turns"] == 1
                and d["status"] == "idle"
                and d
            )
        )
        assert [e["type"] for e in done["events"]][:3] == ["user", "assistant", "result"]
        assert done["cost_usd"] == pytest.approx(0.01)
        opts = created[0].options
        assert opts.max_turns == 50 and opts.max_budget_usd == 5
        assert opts.system_prompt["append"] == "You review code."
        assert opts.model == "haiku"
        assert opts.permission_mode == "default"
        too_many = client.post("/api/sessions", json={"agent_id": agent_id(client), "max_turns": 500})
        assert too_many.status_code == 422
        client.post(f"/api/sessions/{s['id']}/close")


def test_permission_goes_to_inbox_and_allow_runs_tool(settings):
    client, _, _ = make_client(settings, writing_script)
    with client:
        s = start_chat(client)
        client.post(f"/api/sessions/{s['id']}/message", json={"text": "haz algo"})
        pending = until(lambda: client.get("/api/inbox").json())
        assert pending[0]["kind"] == "permission" and pending[0]["detail"]["tool"] == "Bash"
        assert client.get("/api/status").json()["reviewer"]["state"] == "esperando"
        client.post(f"/api/inbox/{pending[0]['id']}/resolve", json={"allow": True})
        done = until(lambda: (d := client.get(f"/api/sessions/{s['id']}").json())["turns"] == 1 and d)
        assert any(e.get("text") == "ejecutado" for e in done["events"])
        assert client.get("/api/inbox").json() == []
        again = client.post(f"/api/inbox/{pending[0]['id']}/resolve", json={"allow": True})
        assert again.status_code == 409
        client.post(f"/api/sessions/{s['id']}/close")


def test_denied_permission_is_reported_to_agent(settings):
    client, _, _ = make_client(settings, writing_script)
    with client:
        s = start_chat(client)
        client.post(f"/api/sessions/{s['id']}/message", json={"text": "haz algo"})
        pending = until(lambda: client.get("/api/inbox").json())
        client.post(f"/api/inbox/{pending[0]['id']}/resolve", json={"allow": False, "message": "no"})
        done = until(lambda: (d := client.get(f"/api/sessions/{s['id']}").json())["turns"] == 1 and d)
        assert any(e.get("text") == "denegado" for e in done["events"])
        client.post(f"/api/sessions/{s['id']}/close")


def test_readonly_task_denies_without_waiting_for_a_human(settings):
    client, _, _ = make_client(settings, writing_script)
    with client:
        s = client.post(
            "/api/sessions", json={"agent_id": agent_id(client), "kind": "task", "prompt": "haz algo"}
        ).json()
        assert s["policy"] == "readonly"
        done = wait(client, s["id"], {"done", "error", "limit"})
        assert done["status"] == "done"
        assert any(e.get("text") == "denegado" for e in done["events"])
        assert client.get("/api/inbox").json() == []
        runs = client.get("/api/runs").json()
        assert runs[0]["id"] == s["id"] and runs[0]["status"] == "done"


def test_budget_limit_ends_session_with_clear_status(settings):
    async def limited(client):
        yield result(subtype="error_max_budget_usd", is_error=True, text="")

    client, _, _ = make_client(settings, limited)
    with client:
        s = client.post(
            "/api/sessions", json={"agent_id": agent_id(client), "kind": "task", "prompt": "x"}
        ).json()
        done = wait(client, s["id"], {"limit", "done", "error"})
        assert done["status"] == "limit"
        assert any("presupuesto" in (e.get("limit") or "") for e in done["events"])


def test_skills_cannot_chat_and_empty_task_is_rejected(settings):
    client, _, _ = make_client(settings)
    with client:
        assert (
            client.post("/api/sessions", json={"agent_id": agent_id(client, "demo-skill")}).status_code == 400
        )
        assert (
            client.post("/api/sessions", json={"agent_id": agent_id(client), "kind": "task"}).status_code
            == 400
        )
        assert client.post("/api/sessions", json={"agent_id": "nope"}).status_code == 404


def test_sdk_failure_is_reported_not_raised(settings):
    async def boom(client):
        raise RuntimeError("cli exploded")
        yield  # pragma: no cover

    client, _, _ = make_client(settings, boom)
    with client:
        s = client.post(
            "/api/sessions", json={"agent_id": agent_id(client), "kind": "task", "prompt": "x"}
        ).json()
        done = wait(client, s["id"], {"error"})
        assert any(e["type"] == "error" for e in done["events"])
