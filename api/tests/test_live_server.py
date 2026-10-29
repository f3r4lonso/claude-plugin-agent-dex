"""Runs the real uvicorn server: catches missing runtime pieces (e.g. a WebSocket library)
that the in-process TestClient hides."""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest
import websockets


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(tmp_path):
    port = free_port()
    home = tmp_path / "claude"
    (home / "agents").mkdir(parents=True)
    env = {
        **os.environ,
        "AGENT_DEX_HOME": str(tmp_path / "data"),
        "AGENT_DEX_CLAUDE_HOME": str(home),
        "AGENT_DEX_PROJECT_DIR": str(tmp_path),
        "PYTHONUNBUFFERED": "1",
    }
    proc = subprocess.Popen(
        [sys.executable, "-m", "agent_dex.cli", "serve", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    token = None
    deadline = time.time() + 20
    while time.time() < deadline and token is None:
        line = proc.stdout.readline()
        if "#t=" in line:
            token = line.strip().split("#t=")[1]
    assert token, "server did not print its launch URL"
    for _ in range(50):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            break
        except OSError:
            time.sleep(0.1)
    yield port, token
    proc.terminate()
    proc.wait(timeout=10)


def test_http_and_websocket_work_on_the_real_server(server):
    port, token = server
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/dex", headers={"Authorization": f"Bearer {token}"}
    )
    assert json.load(urllib.request.urlopen(req, timeout=5))["counts"] == {"agents": 0, "skills": 0}

    async def ws_roundtrip():
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws?t={token}") as ws:
            return json.loads(await asyncio.wait_for(ws.recv(), timeout=5))

    assert asyncio.run(ws_roundtrip())["topic"] == "hello"

    async def ws_without_token():
        async with websockets.connect(f"ws://127.0.0.1:{port}/ws") as ws:
            await asyncio.wait_for(ws.recv(), timeout=5)

    with pytest.raises(websockets.exceptions.WebSocketException):
        asyncio.run(ws_without_token())
