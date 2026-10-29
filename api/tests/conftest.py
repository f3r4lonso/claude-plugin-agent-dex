from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from claude_agent_sdk import AssistantMessage, ResultMessage, TextBlock, ToolUseBlock
from fastapi.testclient import TestClient

from agent_dex.config import Settings
from agent_dex.main import create_app

TOKEN = "test-token"
HOST = {"Host": "127.0.0.1:8771"}
AUTH = {"Authorization": f"Bearer {TOKEN}", **HOST}


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    claude = tmp_path / "claude"
    (claude / "agents").mkdir(parents=True)
    (claude / "skills" / "demo-skill").mkdir(parents=True)
    (claude / "agents" / "reviewer.md").write_text(
        "---\nname: reviewer\ndescription: Reviews code\ntools: Read, Grep\nmodel: haiku\n---\nYou review code.\n",
        encoding="utf-8",
    )
    (claude / "agents" / "broken.md").write_text("---\nname: [unclosed\n---\nbody", encoding="utf-8")
    (claude / "skills" / "demo-skill" / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: A demo\n---\nSteps.\n", encoding="utf-8"
    )
    project = tmp_path / "project"
    project.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    return Settings(port=8771, data_dir=data, claude_home=claude, project_dir=project, model=None)


class FakeClient:
    """Stands in for ClaudeSDKClient. `script` decides what a turn does."""

    def __init__(self, options, script):
        self.options = options
        self.script = script
        self.prompts: list[str] = []
        self.interrupted = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def query(self, text: str):
        self.prompts.append(text)

    async def interrupt(self):
        self.interrupted = True

    async def receive_response(self):
        async for msg in self.script(self):
            yield msg


def result(subtype="success", cost=0.01, turns=1, text="listo", is_error=False):
    return ResultMessage(
        subtype=subtype,
        duration_ms=1,
        duration_api_ms=1,
        is_error=is_error,
        num_turns=turns,
        session_id="s",
        total_cost_usd=cost,
        result=text,
    )


async def simple_script(client):
    yield AssistantMessage(content=[TextBlock(text="hola")], model="fake")
    yield result()


async def writing_script(client):
    """Asks permission to run a Bash command, then reports what happened."""
    from claude_agent_sdk import PermissionResultAllow

    yield AssistantMessage(
        content=[ToolUseBlock(id="t1", name="Bash", input={"command": "echo hi"})], model="fake"
    )
    verdict = await client.options.can_use_tool("Bash", {"command": "echo hi"}, None)
    ok = isinstance(verdict, PermissionResultAllow)
    yield AssistantMessage(content=[TextBlock(text="ejecutado" if ok else "denegado")], model="fake")
    yield result(text="ejecutado" if ok else "denegado")


def make_client(settings, script=simple_script, **app_kwargs):
    created: list[FakeClient] = []

    def factory(options):
        c = FakeClient(options, script)
        created.append(c)
        return c

    app = create_app(settings, TOKEN, client_factory=factory, static_dir=None, **app_kwargs)
    return TestClient(app, headers=AUTH), app, created
