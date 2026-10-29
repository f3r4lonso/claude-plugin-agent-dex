"""Find agents and skills in Claude Code folders. Read-only.

File contents are untrusted data: they are parsed, never executed.
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ARCHETYPES = ["investigador", "constructor", "guardian", "mensajero", "artista"]
HOBBIES = {
    "investigador": "lee un libro",
    "constructor": "ordena sus herramientas",
    "guardian": "vigila desde su puesto",
    "mensajero": "estira las piernas",
    "artista": "dibuja en su libreta",
}
MAX_FILE_BYTES = 512 * 1024
MAX_WALK_DEPTH = 8


@dataclass
class Resource:
    id: str
    kind: str  # "agent" | "skill"
    name: str
    description: str
    source: str  # "user" | "project" | "plugin"
    plugin: str | None
    path: str
    model: str | None = None
    tools: list[str] = field(default_factory=list)
    body: str = ""
    valid: bool = True
    error: str | None = None
    archetype: str = "investigador"
    hobby: str = ""

    def public(self, with_body: bool = False) -> dict:
        data = {
            "id": self.id,
            "kind": self.kind,
            "name": self.name,
            "description": self.description,
            "source": self.source,
            "plugin": self.plugin,
            "path": self.path,
            "model": self.model,
            "tools": self.tools,
            "valid": self.valid,
            "error": self.error,
            "archetype": self.archetype,
            "hobby": self.hobby,
            "clients": ["claude"],
        }
        if with_body:
            data["body"] = self.body
        return data


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "x"


def archetype_for(name: str) -> str:
    digest = hashlib.sha1(name.lower().encode()).digest()
    return ARCHETYPES[digest[0] % len(ARCHETYPES)]


def parse_markdown(path: Path) -> tuple[dict, str, str | None]:
    """Return (frontmatter, body, error). Never raises."""
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return {}, "", "archivo demasiado grande"
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {}, "", f"no se pudo leer: {exc.strerror}"
    match = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", text, re.DOTALL)
    if not match:
        return {}, text, None
    try:
        data = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return {}, match.group(2), "frontmatter inválido"
    if not isinstance(data, dict):
        return {}, match.group(2), "frontmatter inválido"
    return data, match.group(2), None


def _as_tools(value: object) -> list[str]:
    if isinstance(value, str):
        return [t.strip() for t in value.split(",") if t.strip()]
    if isinstance(value, list):
        return [str(t) for t in value]
    return []


def _build(kind: str, path: Path, source: str, plugin: str | None, fallback_name: str) -> Resource:
    fm, body, error = parse_markdown(path)
    name = str(fm.get("name") or fallback_name)
    arche = archetype_for(name)
    rid = f"{kind}-{slug(name)}-{hashlib.sha1(str(path).encode()).hexdigest()[:6]}"
    desc = fm.get("description")
    model = fm.get("model")
    return Resource(
        id=rid,
        kind=kind,
        name=name,
        description=str(desc).strip() if desc else "",
        source=source,
        plugin=plugin,
        path=str(path),
        model=str(model) if model else None,
        tools=_as_tools(fm.get("tools")),
        body=body.strip(),
        valid=error is None,
        error=error,
        archetype=arche,
        hobby=HOBBIES[arche],
    )


def _scan_root(root: Path, source: str, plugin: str | None = None) -> list[Resource]:
    found: list[Resource] = []
    agents = root / "agents"
    if agents.is_dir():
        for f in sorted(agents.glob("*.md")):
            found.append(_build("agent", f, source, plugin, f.stem))
    skills = root / "skills"
    if skills.is_dir():
        for d in sorted(p for p in skills.iterdir() if p.is_dir()):
            f = d / "SKILL.md"
            if f.is_file():
                found.append(_build("skill", f, source, plugin, d.name))
    return found


def _plugin_name(start: Path, stop: Path) -> str:
    for parent in [start, *start.parents]:
        manifest = parent / ".claude-plugin" / "plugin.json"
        if manifest.is_file():
            try:
                import json

                return str(json.loads(manifest.read_text(encoding="utf-8")).get("name") or parent.name)
            except (OSError, ValueError):
                return parent.name
        if parent == stop:
            break
    return start.name


def _scan_plugins(cache: Path) -> list[Resource]:
    found: list[Resource] = []
    seen: set[Path] = set()
    base_depth = len(cache.parts)
    for dirpath, dirnames, _ in os.walk(cache):
        current = Path(dirpath)
        if len(current.parts) - base_depth > MAX_WALK_DEPTH:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in {"node_modules", ".git", "__pycache__"}]
        if (current / "agents").is_dir() or (current / "skills").is_dir():
            if current in seen:
                continue
            seen.add(current)
            found.extend(_scan_root(current, "plugin", _plugin_name(current, cache)))
    return found


def discover(claude_home: Path, project_dir: Path) -> list[Resource]:
    resources: list[Resource] = []
    resources += _scan_root(claude_home, "user")
    project_claude = project_dir / ".claude"
    if project_claude.resolve() != claude_home.resolve():
        resources += _scan_root(project_claude, "project")
    cache = claude_home / "plugins" / "cache"
    if cache.is_dir():
        resources += _scan_plugins(cache)
    # Same plugin can appear in several cached versions: keep one per (kind, plugin, name).
    unique: dict[tuple, Resource] = {}
    for r in resources:
        key = (r.kind, r.source, r.plugin, r.name.lower())
        if key not in unique or r.path > unique[key].path:
            unique[key] = r
    return sorted(unique.values(), key=lambda r: (r.kind != "agent", r.name.lower()))
