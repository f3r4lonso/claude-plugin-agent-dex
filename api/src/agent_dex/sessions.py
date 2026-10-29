"""Chat and task sessions on top of the Claude Agent SDK.

A session is one agent talking to Claude Code. Permission requests become
inbox items; a person answers them in the chat or in the inbox. Sessions never
approve anything on their own.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Callable
from typing import Any

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    StreamEvent,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

from .config import MAX_BUDGET_CAP_USD, MAX_MESSAGE_CHARS, MAX_TURNS_CAP, Settings
from .discovery import Resource
from .hub import Hub
from .inbox import Inbox
from .store import Store

READ_ONLY_TOOLS = ["Read", "Glob", "Grep"]
MAX_EVENTS = 1000
KNOWN_MODEL_ALIASES = {"haiku", "sonnet", "opus"}

LIMIT_MESSAGES = {
    "error_max_turns": "Se alcanzó el máximo de turnos configurado.",
    "error_max_budget_usd": "Se alcanzó el presupuesto máximo configurado.",
}


class SessionError(Exception):
    """A request the server refuses (bad state or bad input)."""


def clamp_limits(
    max_turns: int | None, max_budget_usd: float | None, default_turns: int, default_budget: float
):
    turns = min(max(int(max_turns or default_turns), 1), MAX_TURNS_CAP)
    budget = min(max(float(max_budget_usd or default_budget), 0.01), MAX_BUDGET_CAP_USD)
    return turns, budget


def summarize_input(data: Any, limit: int = 1500) -> Any:
    """Short, JSON-safe view of a tool input for display."""

    def cut(value: Any) -> Any:
        if isinstance(value, str):
            return value if len(value) <= 400 else value[:400] + "…"
        if isinstance(value, dict):
            return {str(k): cut(v) for k, v in list(value.items())[:12]}
        if isinstance(value, list):
            return [cut(v) for v in value[:12]]
        return value

    text = json.dumps(cut(data), ensure_ascii=False, default=str)
    return json.loads(text) if len(text) <= limit else {"_truncated": text[:limit] + "…"}


class Session:
    def __init__(
        self,
        manager: SessionManager,
        agent: Resource,
        kind: str,
        policy: str,
        max_turns: int,
        max_budget_usd: float,
        prompt: str | None,
    ) -> None:
        self.mgr = manager
        self.id = uuid.uuid4().hex[:12]
        self.agent = agent
        self.kind = kind  # "chat" | "task"
        self.policy = policy  # "ask" | "readonly"
        self.max_turns = max_turns
        self.max_budget_usd = max_budget_usd
        self.prompt = prompt
        self.status = "starting"  # starting|running|idle|done|limit|error|cancelled
        self.created = time.time()
        self.finished: float | None = None
        self.cost_usd = 0.0
        self.turns = 0
        self.final_text = ""
        self.workflow_run_id: str | None = None
        self.events: list[dict[str, Any]] = []
        self.done = asyncio.Event()
        self._inputs: asyncio.Queue[str | None] = asyncio.Queue()
        self._client: Any = None
        self._task: asyncio.Task | None = None
        self._pending_permissions = 0

    # ---- public state -------------------------------------------------
    def public(self, with_events: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "agent": self.agent.name,
            "agent_id": self.agent.id,
            "kind": self.kind,
            "policy": self.policy,
            "status": self.status,
            "created": self.created,
            "finished": self.finished,
            "cost_usd": self.cost_usd,
            "turns": self.turns,
            "max_turns": self.max_turns,
            "max_budget_usd": self.max_budget_usd,
            "workflow_run_id": self.workflow_run_id,
        }
        if with_events:
            data["events"] = self.events
        return data

    def _emit(self, event: dict[str, Any], store: bool = True) -> None:
        event = {"ts": time.time(), **event}
        if store:
            self.events.append(event)
            del self.events[:-MAX_EVENTS]
        self.mgr.hub.publish({"topic": "session", "session_id": self.id, "event": event})

    def _set_status(self, status: str) -> None:
        self.status = status
        self.mgr.hub.publish({"topic": "session_status", "session": self.public()})

    # ---- control ------------------------------------------------------
    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name=f"session-{self.id}")
        if self.prompt:
            self.send(self.prompt)

    def send(self, text: str) -> None:
        if self.status in ("done", "limit", "error", "cancelled"):
            raise SessionError("La sesión ya terminó.")
        text = text.strip()
        if not text:
            raise SessionError("El mensaje está vacío.")
        if len(text) > MAX_MESSAGE_CHARS:
            raise SessionError("El mensaje es demasiado largo.")
        if self.status == "running":
            raise SessionError("El agente aún está respondiendo.")
        self._inputs.put_nowait(text)

    async def interrupt(self) -> None:
        if self._client is not None and self.status == "running":
            await self._client.interrupt()

    async def close(self) -> None:
        """Ask the loop to finish; stop a running turn first."""
        await self.interrupt()
        self._inputs.put_nowait(None)
        if self._task is not None:
            try:
                await asyncio.wait_for(asyncio.shield(self._task), timeout=15)
            except (TimeoutError, Exception):  # noqa: BLE001 - best effort on shutdown
                self._task.cancel()

    # ---- SDK wiring ---------------------------------------------------
    def _options(self) -> ClaudeAgentOptions:
        kwargs: dict[str, Any] = {
            "cwd": str(self.mgr.settings.project_dir),
            "can_use_tool": self._can_use_tool,
            "allowed_tools": list(READ_ONLY_TOOLS),
            "permission_mode": "default",
            "max_turns": self.max_turns,
            "max_budget_usd": self.max_budget_usd,
            "include_partial_messages": self.kind == "chat",
            "setting_sources": ["user", "project"],
        }
        if self.agent.kind == "agent" and self.agent.body:
            kwargs["system_prompt"] = {"type": "preset", "preset": "claude_code", "append": self.agent.body}
        model = self.mgr.settings.model
        if not model and self.agent.model:
            declared = self.agent.model.strip()
            if declared in KNOWN_MODEL_ALIASES or declared.startswith("claude-"):
                model = declared
        if model:
            kwargs["model"] = model
        return ClaudeAgentOptions(**kwargs)

    async def _can_use_tool(self, tool_name: str, tool_input: dict[str, Any], _ctx: Any):
        if self.policy == "readonly":
            return PermissionResultDeny(message="Esta tarea es de solo lectura; la acción fue denegada.")
        self._pending_permissions += 1
        self.mgr.hub.claim(self.agent.name, self.id, "esperando", f"Permiso: {tool_name}")
        self._emit({"type": "permission_requested", "tool": tool_name})
        try:
            answer = await self.mgr.inbox.ask(
                "permission",
                f"Permiso: {tool_name}",
                self.agent.name,
                {"tool": tool_name, "input": summarize_input(tool_input)},
                session_id=self.id,
                workflow_run_id=self.workflow_run_id,
            )
        finally:
            self._pending_permissions -= 1
            if self._pending_permissions == 0 and self.status == "running":
                self.mgr.hub.claim(self.agent.name, self.id, "trabajando")
        if answer.get("allow"):
            self._emit({"type": "permission_resolved", "tool": tool_name, "allow": True})
            return PermissionResultAllow()
        self._emit({"type": "permission_resolved", "tool": tool_name, "allow": False})
        return PermissionResultDeny(message=str(answer.get("message") or "Denegado por la persona usuaria."))

    def _handle(self, msg: Any) -> None:
        if isinstance(msg, StreamEvent):
            ev = msg.event or {}
            delta = ev.get("delta") or {}
            if ev.get("type") == "content_block_delta" and delta.get("type") == "text_delta":
                self._emit({"type": "delta", "text": delta.get("text", "")}, store=False)
        elif isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock) and block.text.strip():
                    self.final_text = block.text
                    self._emit({"type": "assistant", "text": block.text})
                elif isinstance(block, ToolUseBlock):
                    self._emit(
                        {
                            "type": "tool",
                            "id": block.id,
                            "name": block.name,
                            "input": summarize_input(block.input),
                        }
                    )
        elif isinstance(msg, UserMessage) and isinstance(msg.content, list):
            for block in msg.content:
                if isinstance(block, ToolResultBlock):
                    self._emit(
                        {"type": "tool_result", "id": block.tool_use_id, "is_error": bool(block.is_error)}
                    )
        elif isinstance(msg, ResultMessage):
            self.turns = msg.num_turns or self.turns
            if msg.total_cost_usd is not None:
                self.cost_usd = msg.total_cost_usd
            if msg.result:
                self.final_text = msg.result
            self._emit(
                {
                    "type": "result",
                    "subtype": msg.subtype,
                    "is_error": msg.is_error,
                    "cost_usd": self.cost_usd,
                    "turns": self.turns,
                    "limit": LIMIT_MESSAGES.get(msg.subtype),
                }
            )
            if msg.subtype in LIMIT_MESSAGES:
                self._limit_hit = msg.subtype
            elif msg.is_error:
                self._turn_failed = True

    _limit_hit: str | None = None
    _turn_failed: bool = False

    async def _run(self) -> None:
        agent_name = self.agent.name
        final_status = "done"
        try:
            async with self.mgr.client_factory(self._options()) as client:
                self._client = client
                self._set_status("idle")
                while True:
                    text = await self._inputs.get()
                    if text is None:
                        final_status = "cancelled" if self.kind == "task" and not self.final_text else "done"
                        break
                    self._emit({"type": "user", "text": text})
                    self._set_status("running")
                    self.mgr.hub.claim(agent_name, self.id, "trabajando")
                    await client.query(text)
                    async for msg in client.receive_response():
                        self._handle(msg)
                    if self._limit_hit:
                        final_status = "limit"
                        break
                    if self._turn_failed:
                        final_status = "error"
                        break
                    if self.kind == "task":
                        break
                    self.mgr.hub.release(agent_name, self.id)
                    self._set_status("idle")
        except asyncio.CancelledError:
            final_status = "cancelled"
            raise
        except Exception as exc:  # noqa: BLE001 - surface any SDK failure to the UI
            final_status = "error"
            self._emit({"type": "error", "message": f"{type(exc).__name__}: {str(exc)[:300]}"})
        finally:
            self._client = None
            self.mgr.hub.release(agent_name, self.id)
            if final_status == "error":
                self.mgr.hub.claim(agent_name, f"{self.id}-err", "error")
                asyncio.get_running_loop().call_later(60, self.mgr.hub.release, agent_name, f"{self.id}-err")
            self.finished = time.time()
            self._set_status(final_status)
            self.mgr.record(self)
            self.done.set()


ClientFactory = Callable[[ClaudeAgentOptions], Any]


class SessionManager:
    def __init__(
        self,
        settings: Settings,
        hub: Hub,
        inbox: Inbox,
        store: Store,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self.settings = settings
        self.hub = hub
        self.inbox = inbox
        self.store = store
        self.client_factory: ClientFactory = client_factory or (
            lambda options: ClaudeSDKClient(options=options)
        )
        self.sessions: dict[str, Session] = {}

    def create(
        self,
        agent: Resource,
        kind: str,
        prompt: str | None = None,
        policy: str | None = None,
        max_turns: int | None = None,
        max_budget_usd: float | None = None,
    ) -> Session:
        if kind not in ("chat", "task"):
            raise SessionError("Tipo de sesión inválido.")
        if agent.kind != "agent":
            raise SessionError("Solo los agentes pueden conversar o ejecutar tareas.")
        if kind == "task" and not (prompt and prompt.strip()):
            raise SessionError("Una tarea necesita una descripción.")
        policy = policy or ("ask" if kind == "chat" else "readonly")
        if policy not in ("ask", "readonly"):
            raise SessionError("Política inválida.")
        turns, budget = clamp_limits(
            max_turns,
            max_budget_usd,
            default_turns=25 if kind == "chat" else 10,
            default_budget=2.0 if kind == "chat" else 1.0,
        )
        session = Session(self, agent, kind, policy, turns, budget, prompt.strip() if prompt else None)
        self.sessions[session.id] = session
        session.start()
        return session

    def get(self, session_id: str) -> Session:
        try:
            return self.sessions[session_id]
        except KeyError:
            raise KeyError(session_id) from None

    def record(self, session: Session) -> None:
        self.store.save_run(
            {
                "id": session.id,
                "agent": session.agent.name,
                "kind": session.kind,
                "status": session.status,
                "created": session.created,
                "finished": session.finished,
                "cost_usd": session.cost_usd,
                "turns": session.turns,
                "prompt": (session.prompt or "")[:2000],
                "result": session.final_text[:8000],
            }
        )

    async def run_task(
        self,
        agent: Resource,
        prompt: str,
        policy: str,
        max_turns: int,
        max_budget_usd: float,
        workflow_run_id: str,
    ) -> Session:
        """Run one non-interactive task to the end (used by workflows)."""
        session = self.create(agent, "task", prompt, policy, max_turns, max_budget_usd)
        session.workflow_run_id = workflow_run_id
        await session.done.wait()
        return session

    async def shutdown(self) -> None:
        await asyncio.gather(
            *(s.close() for s in list(self.sessions.values()) if not s.done.is_set()), return_exceptions=True
        )
