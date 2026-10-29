"""Pending human actions (permissions, workflow approvals).

Items never expire and are never auto-resolved. They live in memory: after a
restart the work that was waiting is marked interrupted instead.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from .hub import Hub


@dataclass
class InboxItem:
    id: str
    kind: str  # "permission" | "approval"
    title: str
    agent: str
    detail: dict[str, Any]
    created: float = field(default_factory=time.time)
    status: str = "pending"  # "pending" | "resolved"
    resolution: dict[str, Any] | None = None
    session_id: str | None = None
    workflow_run_id: str | None = None
    _future: asyncio.Future[dict[str, Any]] | None = field(default=None, repr=False)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "agent": self.agent,
            "detail": self.detail,
            "created": self.created,
            "status": self.status,
            "resolution": self.resolution,
            "session_id": self.session_id,
            "workflow_run_id": self.workflow_run_id,
        }


class Inbox:
    def __init__(self, hub: Hub) -> None:
        self.hub = hub
        self.items: dict[str, InboxItem] = {}

    def pending(self) -> list[InboxItem]:
        return sorted((i for i in self.items.values() if i.status == "pending"), key=lambda i: i.created)

    async def ask(
        self,
        kind: str,
        title: str,
        agent: str,
        detail: dict[str, Any],
        session_id: str | None = None,
        workflow_run_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a pending item and wait (without any timeout) for a person."""
        item = InboxItem(
            id=uuid.uuid4().hex[:12],
            kind=kind,
            title=title,
            agent=agent,
            detail=detail,
            session_id=session_id,
            workflow_run_id=workflow_run_id,
        )
        item._future = asyncio.get_running_loop().create_future()
        self.items[item.id] = item
        self.hub.publish({"topic": "inbox", "event": "created", "item": item.public()})
        try:
            return await item._future
        except asyncio.CancelledError:
            self._close(item, {"cancelled": True})
            raise

    def resolve(self, item_id: str, resolution: dict[str, Any]) -> InboxItem:
        item = self.items.get(item_id)
        if item is None:
            raise KeyError(item_id)
        if item.status != "pending":
            raise ValueError("already resolved")
        self._close(item, resolution)
        if item._future and not item._future.done():
            item._future.set_result(resolution)
        return item

    def _close(self, item: InboxItem, resolution: dict[str, Any]) -> None:
        item.status = "resolved"
        item.resolution = resolution
        self.hub.publish({"topic": "inbox", "event": "resolved", "item": item.public()})
