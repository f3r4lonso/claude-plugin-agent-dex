import time

from .conftest import make_client, simple_script

WF = {
    "name": "Informe",
    "goal": "Escribir un informe",
    "steps": [
        {"type": "agent", "agent": "reviewer", "instruction": "Investiga"},
        {"type": "human", "instruction": "¿Apruebas?"},
        {"type": "agent", "agent": "reviewer", "instruction": "Redacta"},
    ],
}


def until(fn, timeout=6.0):
    end = time.time() + timeout
    while time.time() < end:
        value = fn()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("timeout")


def run_status(client, rid, wanted):
    return until(lambda: (r := client.get(f"/api/workflow-runs/{rid}").json())["status"] in wanted and r)


def test_workflow_pauses_for_human_then_continues(settings):
    client, _, created = make_client(settings, simple_script)
    with client:
        wid = client.post("/api/workflows", json=WF).json()["id"]
        run = client.post(f"/api/workflows/{wid}/run").json()
        pending = until(lambda: client.get("/api/inbox").json())
        assert pending[0]["kind"] == "approval"
        assert pending[0]["detail"]["output"] == "listo"
        assert client.get(f"/api/workflow-runs/{run['id']}").json()["status"] == "waiting_human"
        resolution = {"decision": "approve", "edited_output": "texto editado"}
        client.post(f"/api/inbox/{pending[0]['id']}/resolve", json=resolution)
        final = run_status(client, run["id"], {"done", "failed"})
        assert final["status"] == "done"
        assert [s["status"] for s in final["steps"]] == ["done", "done", "done"]
        assert "texto editado" in created[-1].prompts[0]  # the handoff carries the human's edit
        assert "Resultado del paso anterior" in created[-1].prompts[0]


def test_rejection_stops_the_run(settings):
    client, _, created = make_client(settings, simple_script)
    with client:
        wid = client.post("/api/workflows", json=WF).json()["id"]
        run = client.post(f"/api/workflows/{wid}/run").json()
        pending = until(lambda: client.get("/api/inbox").json())
        client.post(
            f"/api/inbox/{pending[0]['id']}/resolve", json={"decision": "reject", "note": "no me gusta"}
        )
        final = run_status(client, run["id"], {"rejected"})
        assert final["steps"][2]["status"] == "pending"
        assert len(created) == 1  # the last agent never ran


def test_validation(settings):
    client, _, _ = make_client(settings)
    with client:
        bad_first = {**WF, "steps": [WF["steps"][1], WF["steps"][0]]}
        assert client.post("/api/workflows", json=bad_first).status_code == 422
        no_agent = {**WF, "steps": [{"type": "agent", "instruction": "x"}]}
        assert client.post("/api/workflows", json=no_agent).status_code == 422
        ghost_steps = [{"type": "agent", "agent": "ghost", "instruction": "x"}]
        ghost = client.post("/api/workflows", json={**WF, "steps": ghost_steps}).json()
        assert client.post(f"/api/workflows/{ghost['id']}/run").status_code == 400
        assert client.post("/api/workflows", json={**WF, "max_total_budget_usd": 999}).status_code == 422


def test_interrupted_runs_are_marked_on_restart(settings):
    client, _, _ = make_client(settings, simple_script)
    with client:
        wid = client.post("/api/workflows", json=WF).json()["id"]
        run = client.post(f"/api/workflows/{wid}/run").json()
        until(lambda: client.get("/api/inbox").json())
    # A new process starts: whatever was waiting cannot continue.
    client2, _, _ = make_client(settings, simple_script)
    with client2:
        assert client2.get(f"/api/workflow-runs/{run['id']}").json()["status"] == "interrupted"
