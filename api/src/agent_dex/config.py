"""Runtime settings. Environment variables override defaults (used by tests)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

HOST = "127.0.0.1"
DEFAULT_PORT = 8771

# Hard server-side caps: a request can ask for less, never more.
MAX_TURNS_CAP = 50
MAX_BUDGET_CAP_USD = 5.0
WORKFLOW_BUDGET_CAP_USD = 10.0
MAX_MESSAGE_CHARS = 20_000


@dataclass(frozen=True)
class Settings:
    port: int
    data_dir: Path
    claude_home: Path
    project_dir: Path
    model: str | None

    @property
    def db_path(self) -> Path:
        return self.data_dir / "agent-dex.sqlite3"

    @property
    def captures_path(self) -> Path:
        return self.data_dir / "captures.json"

    @property
    def allowed_hosts(self) -> set[str]:
        return {f"127.0.0.1:{self.port}", f"localhost:{self.port}"}

    @property
    def allowed_origins(self) -> set[str]:
        return {f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"}


def load_settings(port: int | None = None) -> Settings:
    home = Path.home()
    data_dir = Path(os.environ.get("AGENT_DEX_HOME", home / ".agent-dex"))
    claude_home = Path(os.environ.get("AGENT_DEX_CLAUDE_HOME", home / ".claude"))
    project_dir = Path(os.environ.get("AGENT_DEX_PROJECT_DIR", Path.cwd()))
    chosen = port or int(os.environ.get("AGENT_DEX_PORT", DEFAULT_PORT))
    data_dir.mkdir(parents=True, exist_ok=True)
    return Settings(
        port=chosen,
        data_dir=data_dir,
        claude_home=claude_home,
        project_dir=project_dir,
        model=os.environ.get("AGENT_DEX_MODEL") or None,
    )
