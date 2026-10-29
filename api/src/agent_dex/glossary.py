"""Curated catalogue and capture ("install") of agents and skills.

Rules: every entry is pinned to a commit; nothing is written before an explicit
confirmation; downloaded bytes are checked against the pinned git blob hashes;
nothing from a captured repository is ever executed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from importlib import resources
from pathlib import Path
from typing import Any

from .config import Settings

SCRIPT_EXT = {".py", ".sh", ".ps1", ".js", ".ts", ".bat", ".cmd", ".mjs"}
SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
MAX_FILE_BYTES = 1_000_000
MAX_TOTAL_BYTES = 2_000_000
MAX_FILES = 60

Fetcher = Callable[[str, str, str], bytes]


class CaptureError(Exception):
    """User-facing refusal (conflict, integrity failure, unsafe path...)."""


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def github_raw_fetch(repo_url: str, commit: str, path: str) -> bytes:
    slug = repo_url.removeprefix("https://github.com/").strip("/")
    url = f"https://raw.githubusercontent.com/{slug}/{commit}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "agent-dex"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read(MAX_FILE_BYTES + 1)
    except urllib.error.URLError as exc:
        raise CaptureError(f"No se pudo descargar {path}: {exc.reason}") from exc
    if len(data) > MAX_FILE_BYTES:
        raise CaptureError(f"{path} supera el tamaño máximo permitido.")
    return data


def entry_slug(entry_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", entry_id.lower()).strip("-")


class Glossary:
    def __init__(
        self, settings: Settings, fetcher: Fetcher = github_raw_fetch, catalog: dict | None = None
    ) -> None:
        self.settings = settings
        self.fetch = fetcher
        raw = catalog or json.loads(
            resources.files("agent_dex").joinpath("data/catalog.json").read_text(encoding="utf-8")
        )
        self.entries: dict[str, dict[str, Any]] = {}
        for e in raw["entradas"]:
            e = dict(e)
            e["slug"] = entry_slug(e["id"])
            self.entries[e["slug"]] = e

    # ---- registry -----------------------------------------------------
    def _registry(self) -> list[dict[str, Any]]:
        try:
            return json.loads(self.settings.captures_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []

    def _save_registry(self, items: list[dict[str, Any]]) -> None:
        tmp = self.settings.captures_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.settings.captures_path)

    # ---- targets ------------------------------------------------------
    def _target(self, entry: dict[str, Any]) -> Path:
        name = entry["nombre"].lower()
        if not SAFE_NAME.match(name):
            raise CaptureError("El nombre de la entrada no es seguro para instalar.")
        base = self.settings.claude_home
        if entry["tipo"] == "skill":
            return base / "skills" / name
        return base / "agents" / f"{name}.md"

    def _plan(self, entry: dict[str, Any]) -> list[dict[str, Any]]:
        target = self._target(entry)
        files = entry["archivos"]
        if len(files) > MAX_FILES or sum(f["bytes"] for f in files) > MAX_TOTAL_BYTES:
            raise CaptureError("La entrada supera los límites de tamaño permitidos.")
        plan = []
        for f in files:
            if entry["tipo"] == "skill":
                rel = f["ruta"].removeprefix(entry["ruta"] + "/")
                dest = target / rel
            else:
                dest = target
            resolved = dest.resolve()
            if not resolved.is_relative_to(self.settings.claude_home.resolve()):
                raise CaptureError("Ruta de destino fuera de la carpeta de Claude.")
            plan.append(
                {
                    "origen": f["ruta"],
                    "destino": str(dest),
                    "bytes": f["bytes"],
                    "sha": f["sha"],
                    "requiere_atencion": Path(f["ruta"]).suffix.lower() in SCRIPT_EXT,
                }
            )
        return plan

    # ---- queries ------------------------------------------------------
    def owned_names(self) -> set[tuple[str, str]]:
        owned: set[tuple[str, str]] = set()
        for e in self.entries.values():
            try:
                if self._target(e).exists():
                    owned.add((e["tipo"], e["nombre"].lower()))
            except CaptureError:
                continue
        return owned

    def list(self) -> list[dict[str, Any]]:
        captured = {c["slug"] for c in self._registry()}
        owned = self.owned_names()
        out = []
        for e in self.entries.values():
            installed = (e["tipo"], e["nombre"].lower()) in owned
            out.append(
                {
                    **{k: v for k, v in e.items() if k != "archivos"},
                    "archivos_total": len(e["archivos"]),
                    "instalada": installed,
                    "capturada_por_dex": e["slug"] in captured,
                }
            )
        return out

    def preview(self, slug: str) -> dict[str, Any]:
        entry = self._entry(slug)
        plan = self._plan(entry)
        conflicts = [p["destino"] for p in plan if Path(p["destino"]).exists()]
        return {
            "slug": slug,
            "nombre": entry["nombre"],
            "tipo": entry["tipo"],
            "repo": entry["repo"],
            "commit": entry["commit"],
            "licencia": entry["licencia"],
            "revision": entry["revision"],
            "archivos": plan,
            "conflictos": conflicts,
            "total_bytes": sum(p["bytes"] for p in plan),
        }

    # ---- capture / release -------------------------------------------
    def capture(self, slug: str, confirm: bool, expected_commit: str) -> dict[str, Any]:
        if confirm is not True:
            raise CaptureError("Falta la confirmación explícita.")
        entry = self._entry(slug)
        if expected_commit != entry["commit"]:
            raise CaptureError(
                "El commit mostrado no coincide con el del catálogo; vuelve a abrir la vista previa."
            )
        plan = self._plan(entry)
        if any(Path(p["destino"]).exists() for p in plan):
            raise CaptureError("Ya existe algo en el destino; no se sobrescribe nada.")

        staged: list[tuple[Path, bytes]] = []
        for item in plan:
            data = self.fetch(entry["repo"], entry["commit"], item["origen"])
            if git_blob_sha(data) != item["sha"]:
                raise CaptureError(
                    f"Verificación de integridad fallida en {item['origen']}; no se instaló nada."
                )
            staged.append((Path(item["destino"]), data))

        written: list[Path] = []
        try:
            for dest, data in staged:
                dest.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(dir=dest.parent, prefix=".dex-")
                with open(fd, "wb") as fh:
                    fh.write(data)
                Path(tmp).replace(dest)
                written.append(dest)
        except OSError as exc:
            for p in written:
                p.unlink(missing_ok=True)
            raise CaptureError(f"No se pudo escribir: {exc.strerror}") from exc

        record = {
            "slug": slug,
            "id": entry["id"],
            "nombre": entry["nombre"],
            "tipo": entry["tipo"],
            "repo": entry["repo"],
            "commit": entry["commit"],
            "archivos": [str(p) for p in written],
            "capturada": time.time(),
        }
        self._save_registry([*self._registry(), record])
        return record

    def release(self, slug: str) -> dict[str, Any]:
        registry = self._registry()
        record = next((r for r in registry if r["slug"] == slug), None)
        if record is None:
            raise CaptureError("Esta entrada no fue capturada desde Agent Dex; no se borra nada.")
        home = self.settings.claude_home.resolve()
        for f in record["archivos"]:
            p = Path(f)
            if p.resolve().is_relative_to(home):
                p.unlink(missing_ok=True)
        entry = self.entries.get(slug)
        if entry and entry["tipo"] == "skill":
            folder = self._target(entry)
            if folder.is_dir():
                for sub in sorted((d for d in folder.rglob("*") if d.is_dir()), reverse=True):
                    if not any(sub.iterdir()):
                        sub.rmdir()
                if not any(folder.iterdir()):
                    shutil.rmtree(folder, ignore_errors=True)
        self._save_registry([r for r in registry if r["slug"] != slug])
        return {"slug": slug, "liberada": True}

    def _entry(self, slug: str) -> dict[str, Any]:
        try:
            return self.entries[slug]
        except KeyError:
            raise CaptureError("Entrada desconocida.") from None
