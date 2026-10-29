"""FastAPI application: HTTP API, event WebSocket and the bundled web UI."""

from __future__ import annotations

import asyncio
import json
import shutil
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import APIRouter, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import __version__
from .config import MAX_MESSAGE_CHARS, Settings, load_settings
from .discovery import Resource, discover
from .glossary import CaptureError, Fetcher, Glossary, github_raw_fetch
from .hub import Hub
from .inbox import Inbox
from .security import LocalGuard
from .sessions import ClientFactory, SessionError, SessionManager
from .store import Store
from .workflows import WorkflowEngine, WorkflowIn

STATIC_DIR = Path(__file__).parent / "static"
HOOK_MAX_BYTES = 64 * 1024

FEATURES = [
    {"id": "dex", "nombre": "Dex", "estado": "disponible"},
    {"id": "sala", "nombre": "Sala", "estado": "disponible"},
    {"id": "chat", "nombre": "Chat y tareas", "estado": "disponible"},
    {"id": "bandeja", "nombre": "Bandeja", "estado": "disponible"},
    {"id": "workflows", "nombre": "Workflows (lineales)", "estado": "beta"},
    {"id": "glosario", "nombre": "Glosario y captura", "estado": "beta"},
    {"id": "creador", "nombre": "Creador guiado", "estado": "en diseño"},
    {"id": "gimnasio", "nombre": "Gimnasio", "estado": "en diseño"},
    {"id": "estudio", "nombre": "Estudio de imagen", "estado": "en diseño"},
    {"id": "exportar", "nombre": "Exportar a Codex y Copilot", "estado": "en diseño"},
]


class SessionIn(BaseModel):
    agent_id: str
    kind: Literal["chat", "task"] = "chat"
    prompt: str | None = Field(default=None, max_length=MAX_MESSAGE_CHARS)
    policy: Literal["ask", "readonly"] | None = None
    max_turns: int | None = Field(default=None, ge=1, le=50)
    max_budget_usd: float | None = Field(default=None, gt=0, le=5.0)


class MessageIn(BaseModel):
    text: str = Field(max_length=MAX_MESSAGE_CHARS)


class ResolveIn(BaseModel):
    allow: bool | None = None
    message: str | None = Field(default=None, max_length=2000)
    decision: Literal["approve", "reject"] | None = None
    note: str | None = Field(default=None, max_length=2000)
    edited_output: str | None = Field(default=None, max_length=20000)


class CaptureIn(BaseModel):
    confirm: bool
    expected_commit: str


class AppState:
    def __init__(
        self,
        settings: Settings,
        client_factory: ClientFactory | None,
        fetcher: Fetcher,
    ) -> None:
        self.settings = settings
        self.hub = Hub()
        self.inbox = Inbox(self.hub)
        self.store = Store(settings.db_path)
        self.sessions = SessionManager(settings, self.hub, self.inbox, self.store, client_factory)
        self.glossary = Glossary(settings, fetcher)
        self.workflows = WorkflowEngine(
            self.store, self.hub, self.inbox, self.find_agent_by_name, self.sessions.run_task
        )
        self._cache: tuple[float, list[Resource]] | None = None

    def resources(self) -> list[Resource]:
        now = time.monotonic()
        if self._cache is None or now - self._cache[0] > 2.0:
            self._cache = (now, discover(self.settings.claude_home, self.settings.project_dir))
        return self._cache[1]

    def find_agent(self, resource_id: str) -> Resource:
        for r in self.resources():
            if r.id == resource_id:
                return r
        raise HTTPException(404, "Recurso no encontrado")

    def find_agent_by_name(self, name: str) -> Resource | None:
        wanted = name.lower()
        matches = [r for r in self.resources() if r.kind == "agent" and r.name.lower() == wanted]
        order = {"project": 0, "user": 1, "plugin": 2}
        matches.sort(key=lambda r: order.get(r.source, 9))
        return matches[0] if matches else None


def create_app(
    settings: Settings | None = None,
    token: str = "test-token",
    client_factory: ClientFactory | None = None,
    fetcher: Fetcher = github_raw_fetch,
    static_dir: Path | None = STATIC_DIR,
) -> FastAPI:
    settings = settings or load_settings()
    state = AppState(settings, client_factory, fetcher)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        state.store.mark_interrupted()
        yield
        await state.workflows.shutdown()
        await state.sessions.shutdown()

    app = FastAPI(
        title="Agent Dex",
        version=__version__,
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    api = APIRouter(prefix="/api")

    # ---- general ------------------------------------------------------
    @api.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "version": __version__}

    @api.get("/settings")
    def get_settings() -> dict[str, Any]:
        return {
            "version": __version__,
            "claude_home": str(settings.claude_home),
            "claude_home_exists": settings.claude_home.is_dir(),
            "project_dir": str(settings.project_dir),
            "data_dir": str(settings.data_dir),
            "claude_cli": shutil.which("claude"),
            "model_override": settings.model,
            "features": FEATURES,
        }

    # ---- dex ----------------------------------------------------------
    @api.get("/dex")
    def dex() -> dict[str, Any]:
        statuses = state.hub.snapshot()
        items = []
        for r in state.resources():
            data = r.public()
            if r.kind == "agent":
                data["status"] = statuses.get(
                    r.name.lower(), {"state": "inactivo", "since": None, "detail": None}
                )
            items.append(data)
        return {
            "resources": items,
            "counts": {
                "agents": sum(1 for r in items if r["kind"] == "agent"),
                "skills": sum(1 for r in items if r["kind"] == "skill"),
            },
        }

    @api.get("/resources/{resource_id}")
    def resource_detail(resource_id: str) -> dict[str, Any]:
        r = state.find_agent(resource_id)
        data = r.public(with_body=True)
        if r.kind == "agent":
            data["status"] = state.hub.state_of(r.name)
            data["stats"] = state.store.stats_for(r.name)
        return data

    @api.get("/status")
    def status() -> dict[str, Any]:
        return state.hub.snapshot()

    @api.post("/hook")
    async def hook(request: Request) -> dict[str, bool]:
        raw = await request.body()
        if len(raw) > HOOK_MAX_BYTES:
            raise HTTPException(413, "payload too large")
        try:
            data = json.loads(raw)
        except ValueError:
            raise HTTPException(400, "invalid JSON") from None
        event = data.get("hook_event_name") if isinstance(data, dict) else None
        agent = str(data.get("agent_type") or "")[:100] if isinstance(data, dict) else ""
        claim = (
            f"hook-{str(data.get('agent_id') or data.get('session_id') or 'x')[:60]}"
            if isinstance(data, dict)
            else ""
        )
        if agent and event == "SubagentStart":
            state.hub.claim(agent, claim, "trabajando", "Subagente activo en Claude Code")
        elif agent and event == "SubagentStop":
            state.hub.release(agent, claim)
        return {"ok": True}

    # ---- sessions -----------------------------------------------------
    def session_or_404(session_id: str):
        try:
            return state.sessions.get(session_id)
        except KeyError:
            raise HTTPException(404, "Sesión no encontrada") from None

    @api.post("/sessions")
    async def create_session(body: SessionIn) -> dict[str, Any]:
        agent = state.find_agent(body.agent_id)
        try:
            s = state.sessions.create(
                agent, body.kind, body.prompt, body.policy, body.max_turns, body.max_budget_usd
            )
        except SessionError as exc:
            raise HTTPException(400, str(exc)) from None
        return s.public()

    @api.get("/sessions")
    def list_sessions() -> list[dict[str, Any]]:
        return [s.public() for s in sorted(state.sessions.sessions.values(), key=lambda s: -s.created)]

    @api.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        return session_or_404(session_id).public(with_events=True)

    @api.post("/sessions/{session_id}/message")
    async def send_message(session_id: str, body: MessageIn) -> dict[str, bool]:
        try:
            session_or_404(session_id).send(body.text)
        except SessionError as exc:
            raise HTTPException(409, str(exc)) from None
        return {"ok": True}

    @api.post("/sessions/{session_id}/interrupt")
    async def interrupt(session_id: str) -> dict[str, bool]:
        await session_or_404(session_id).interrupt()
        return {"ok": True}

    @api.post("/sessions/{session_id}/close")
    async def close(session_id: str) -> dict[str, bool]:
        await session_or_404(session_id).close()
        return {"ok": True}

    @api.get("/runs")
    def runs() -> list[dict[str, Any]]:
        return state.store.list_runs()

    # ---- inbox --------------------------------------------------------
    @api.get("/inbox")
    def inbox_list() -> list[dict[str, Any]]:
        return [i.public() for i in state.inbox.pending()]

    @api.post("/inbox/{item_id}/resolve")
    async def inbox_resolve(item_id: str, body: ResolveIn) -> dict[str, Any]:
        item = state.inbox.items.get(item_id)
        if item is None:
            raise HTTPException(404, "Pendiente no encontrado")
        if item.kind == "permission":
            if body.allow is None:
                raise HTTPException(400, "Falta «allow»")
            resolution = {"allow": body.allow, "message": body.message}
        else:
            if body.decision is None:
                raise HTTPException(400, "Falta «decision»")
            resolution = {"decision": body.decision, "note": body.note, "edited_output": body.edited_output}
        try:
            return state.inbox.resolve(item_id, resolution).public()
        except ValueError:
            raise HTTPException(409, "Ya estaba resuelto") from None

    # ---- workflows ----------------------------------------------------
    @api.get("/workflows")
    def workflows_list() -> list[dict[str, Any]]:
        return state.store.list_workflows()

    @api.post("/workflows")
    async def workflows_create(body: WorkflowIn) -> dict[str, Any]:
        return state.workflows.save(body)

    @api.put("/workflows/{wid}")
    async def workflows_update(wid: str, body: WorkflowIn) -> dict[str, Any]:
        if state.store.get_workflow(wid) is None:
            raise HTTPException(404, "Workflow no encontrado")
        return state.workflows.save(body, wid)

    @api.delete("/workflows/{wid}")
    def workflows_delete(wid: str) -> dict[str, bool]:
        if not state.store.delete_workflow(wid):
            raise HTTPException(404, "Workflow no encontrado")
        return {"ok": True}

    @api.post("/workflows/{wid}/run")
    async def workflows_run(wid: str) -> dict[str, Any]:
        wf = state.store.get_workflow(wid)
        if wf is None:
            raise HTTPException(404, "Workflow no encontrado")
        try:
            return state.workflows.start(wf)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from None

    @api.get("/workflow-runs")
    def workflow_runs() -> list[dict[str, Any]]:
        return state.store.list_workflow_runs()

    @api.get("/workflow-runs/{rid}")
    def workflow_run(rid: str) -> dict[str, Any]:
        run = state.store.get_workflow_run(rid)
        if run is None:
            raise HTTPException(404, "Ejecución no encontrada")
        return run

    @api.post("/workflow-runs/{rid}/cancel")
    async def workflow_cancel(rid: str) -> dict[str, bool]:
        return {"ok": state.workflows.cancel(rid)}

    # ---- glossary -----------------------------------------------------
    @api.get("/glossary")
    def glossary_list() -> list[dict[str, Any]]:
        return state.glossary.list()

    @api.get("/glossary/{slug}/preview")
    def glossary_preview(slug: str) -> dict[str, Any]:
        try:
            return state.glossary.preview(slug)
        except CaptureError as exc:
            raise HTTPException(400, str(exc)) from None

    @api.post("/glossary/{slug}/capture")
    async def glossary_capture(slug: str, body: CaptureIn) -> dict[str, Any]:
        try:
            result = await asyncio.to_thread(state.glossary.capture, slug, body.confirm, body.expected_commit)
        except CaptureError as exc:
            raise HTTPException(400, str(exc)) from None
        state._cache = None
        return result

    @api.post("/glossary/{slug}/release")
    async def glossary_release(slug: str) -> dict[str, Any]:
        try:
            result = state.glossary.release(slug)
        except CaptureError as exc:
            raise HTTPException(400, str(exc)) from None
        state._cache = None
        return result

    app.include_router(api)

    # ---- websocket ----------------------------------------------------
    @app.websocket("/ws")
    async def ws(socket: WebSocket) -> None:
        await socket.accept()
        queue = state.hub.subscribe()
        try:
            await socket.send_json({"topic": "hello", "version": __version__})
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25)
                except TimeoutError:
                    await socket.send_json({"topic": "ping"})
                    continue
                await socket.send_json(event)
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            state.hub.unsubscribe(queue)

    @app.exception_handler(Exception)
    async def unhandled(_request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": "Error interno del servicio local."}, status_code=500)

    if static_dir is not None and static_dir.is_dir() and (static_dir / "index.html").is_file():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")
    else:

        @app.get("/")
        def no_ui() -> dict[str, str]:
            return {"detail": "La interfaz no está compilada en este paquete."}

    app.state.dex = state
    app.add_middleware(LocalGuard, settings=settings, token=token)
    return app
