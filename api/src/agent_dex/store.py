"""Small SQLite store for run history and workflow definitions."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, agent TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
  created REAL NOT NULL, finished REAL, cost_usd REAL, turns INTEGER,
  prompt TEXT, result TEXT
);
CREATE TABLE IF NOT EXISTS workflows (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, body TEXT NOT NULL, updated REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS workflow_runs (
  id TEXT PRIMARY KEY, workflow_id TEXT NOT NULL, status TEXT NOT NULL,
  created REAL NOT NULL, finished REAL, body TEXT NOT NULL
);
"""


class Store:
    def __init__(self, path: Path) -> None:
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        with self._lock:
            self._db.executescript(SCHEMA)
            self._db.commit()

    def _exec(self, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._db.execute(sql, args)
            rows = cur.fetchall()
            self._db.commit()
            return rows

    # ---- runs ---------------------------------------------------------
    def save_run(self, run: dict[str, Any]) -> None:
        self._exec(
            "INSERT OR REPLACE INTO runs (id, agent, kind, status, created, finished, cost_usd, turns, prompt, result)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                run["id"],
                run["agent"],
                run["kind"],
                run["status"],
                run["created"],
                run.get("finished"),
                run.get("cost_usd"),
                run.get("turns"),
                run.get("prompt"),
                run.get("result"),
            ),
        )

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        return [dict(r) for r in self._exec("SELECT * FROM runs ORDER BY created DESC LIMIT ?", (limit,))]

    def stats_for(self, agent: str) -> dict[str, Any]:
        rows = self._exec(
            "SELECT status, COUNT(*) n, COALESCE(SUM(cost_usd),0) cost, MAX(created) last"
            " FROM runs WHERE lower(agent)=lower(?) GROUP BY status",
            (agent,),
        )
        total = sum(r["n"] for r in rows)
        done = sum(r["n"] for r in rows if r["status"] == "done")
        return {
            "runs": total,
            "done": done,
            "success_rate": (done / total) if total else None,
            "cost_usd": sum(r["cost"] for r in rows),
            "last": max((r["last"] for r in rows), default=None),
        }

    # ---- workflows ----------------------------------------------------
    def save_workflow(self, wid: str, name: str, body: dict[str, Any], updated: float) -> None:
        self._exec(
            "INSERT OR REPLACE INTO workflows (id, name, body, updated) VALUES (?,?,?,?)",
            (wid, name, json.dumps(body, ensure_ascii=False), updated),
        )

    def list_workflows(self) -> list[dict[str, Any]]:
        return [json.loads(r["body"]) for r in self._exec("SELECT body FROM workflows ORDER BY updated DESC")]

    def get_workflow(self, wid: str) -> dict[str, Any] | None:
        rows = self._exec("SELECT body FROM workflows WHERE id=?", (wid,))
        return json.loads(rows[0]["body"]) if rows else None

    def delete_workflow(self, wid: str) -> bool:
        before = self.get_workflow(wid)
        self._exec("DELETE FROM workflows WHERE id=?", (wid,))
        return before is not None

    def save_workflow_run(self, run: dict[str, Any]) -> None:
        self._exec(
            "INSERT OR REPLACE INTO workflow_runs (id, workflow_id, status, created, finished, body) VALUES (?,?,?,?,?,?)",
            (
                run["id"],
                run["workflow_id"],
                run["status"],
                run["created"],
                run.get("finished"),
                json.dumps(run, ensure_ascii=False),
            ),
        )

    def list_workflow_runs(self, limit: int = 50) -> list[dict[str, Any]]:
        return [
            json.loads(r["body"])
            for r in self._exec("SELECT body FROM workflow_runs ORDER BY created DESC LIMIT ?", (limit,))
        ]

    def get_workflow_run(self, rid: str) -> dict[str, Any] | None:
        rows = self._exec("SELECT body FROM workflow_runs WHERE id=?", (rid,))
        return json.loads(rows[0]["body"]) if rows else None

    def mark_interrupted(self) -> int:
        """Anything still 'running' or waiting from a previous process cannot continue."""
        rows = self._exec("SELECT body FROM workflow_runs WHERE status IN ('running','waiting_human')")
        for r in rows:
            run = json.loads(r["body"])
            run["status"] = "interrupted"
            for step in run.get("steps", []):
                if step["status"] in ("running", "waiting_human"):
                    step["status"] = "interrupted"
            self.save_workflow_run(run)
        return len(rows)
