"""In-process event bus and live agent status.

Several activities can claim the same agent at once (a chat and a workflow
step). The visible state is the highest-priority claim.
"""

from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

# Highest priority first. "inactivo" is resolved by the UI into rest / free time.
PRIORITY = ["esperando", "trabajando", "entrenando", "error", "inactivo"]


class Hub:
    def __init__(self) -> None:
        self._claims: dict[str, dict[str, tuple[str, float, str | None]]] = defaultdict(dict)
        self._idle_since: dict[str, float] = {}
        self._subs: set[asyncio.Queue[dict[str, Any]]] = set()

    # ---- events -------------------------------------------------------
    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=500)
        self._subs.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subs.discard(queue)

    def publish(self, event: dict[str, Any]) -> None:
        for queue in list(self._subs):
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                self._subs.discard(queue)  # a stalled client must not block the server

    # ---- status -------------------------------------------------------
    def claim(self, agent: str, claim_id: str, state: str, detail: str | None = None) -> None:
        key = agent.lower()
        self._claims[key][claim_id] = (state, time.time(), detail)
        self._idle_since.pop(key, None)
        self.publish({"topic": "status", "agent": key, **self.state_of(key)})

    def release(self, agent: str, claim_id: str) -> None:
        key = agent.lower()
        self._claims[key].pop(claim_id, None)
        if not self._claims[key]:
            self._idle_since[key] = time.time()
        self.publish({"topic": "status", "agent": key, **self.state_of(key)})

    def state_of(self, agent: str) -> dict[str, Any]:
        key = agent.lower()
        claims = self._claims.get(key, {})
        if not claims:
            return {"state": "inactivo", "since": self._idle_since.get(key), "detail": None}
        best = min(claims.values(), key=lambda c: (PRIORITY.index(c[0]), -c[1]))
        return {"state": best[0], "since": best[1], "detail": best[2]}

    def snapshot(self) -> dict[str, dict[str, Any]]:
        keys = set(self._claims) | set(self._idle_since)
        return {k: self.state_of(k) for k in keys}
