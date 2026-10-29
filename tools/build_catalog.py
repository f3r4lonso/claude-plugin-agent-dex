"""Rebuild catalog/index.json from pinned commits of public repositories.

Needs the GitHub CLI (`gh`) logged in. Run it only when adding or updating
entries; each update must be reviewed by a person (see docs/catalog.md).
"""

import base64
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

SCRIPT_EXT = {".py", ".sh", ".ps1", ".js", ".ts", ".bat", ".cmd", ".mjs"}

SOURCES = [
    {
        "repo": "anthropics/skills",
        "license": "Apache-2.0",
        "kind": "skill",
        "paths": [
            ("skills/frontend-design", ["diseño", "frontend"]),
            ("skills/theme-factory", ["diseño", "temas"]),
            ("skills/internal-comms", ["escritura", "comunicación"]),
            ("skills/mcp-builder", ["código", "mcp"]),
            ("skills/webapp-testing", ["código", "pruebas"]),
            ("skills/skill-creator", ["meta", "skills"]),
        ],
    },
    {
        "repo": "wshobson/agents",
        "license": "MIT",
        "kind": "agent",
        "paths": [
            ("plugins/debugging-toolkit/agents/debugger.md", ["código", "depuración"]),
            ("plugins/comprehensive-review/agents/code-reviewer.md", ["código", "revisión"]),
            ("plugins/python-development/agents/python-pro.md", ["código", "python"]),
            ("plugins/comprehensive-review/agents/security-auditor.md", ["seguridad", "revisión"]),
            ("plugins/code-documentation/agents/docs-architect.md", ["escritura", "documentación"]),
            ("plugins/ui-design/agents/ui-designer.md", ["diseño", "ui"]),
        ],
    },
]


def gh(*args: str) -> str:
    return subprocess.run(["gh", "api", *args], check=True, capture_output=True, text=True).stdout


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.S)
    out: dict = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line and not line.startswith(" "):
                k, v = line.split(":", 1)
                out[k.strip()] = v.strip().strip("'\"")
    return out


def main() -> None:
    entries = []
    for src in SOURCES:
        repo = src["repo"]
        sha = gh(f"repos/{repo}/commits/HEAD", "--jq", ".sha").strip()
        tree = json.loads(gh(f"repos/{repo}/git/trees/{sha}?recursive=1"))["tree"]
        blobs = {t["path"]: (t["size"], t["sha"]) for t in tree if t["type"] == "blob"}
        for path, cats in src["paths"]:
            if src["kind"] == "skill":
                files = sorted(p for p in blobs if p.startswith(path + "/"))
                main_file = f"{path}/SKILL.md"
            else:
                files = [path]
                main_file = path
            if main_file not in blobs:
                sys.exit(f"missing {main_file}")
            raw = gh(f"repos/{repo}/contents/{main_file}?ref={sha}", "--jq", ".content")
            fm = frontmatter(base64.b64decode(raw).decode("utf-8", "replace"))
            name = fm.get("name") or Path(path).stem
            scripts = [p for p in files if Path(p).suffix.lower() in SCRIPT_EXT]
            entries.append(
                {
                    "id": f"{repo}/{path}",
                    "tipo": src["kind"],
                    "nombre": name,
                    "descripcion": (fm.get("description") or "")[:400],
                    "repo": f"https://github.com/{repo}",
                    "commit": sha,
                    "ruta": path,
                    "archivos": [{"ruta": p, "bytes": blobs[p][0], "sha": blobs[p][1]} for p in files],
                    "licencia": src["license"],
                    "clientes": ["claude"],
                    "categorias": cats,
                    "revision": {
                        "fecha": date.today().isoformat(),
                        "resultado": "aviso" if scripts else "ok",
                        "notas": (
                            f"Incluye {len(scripts)} script(s) ejecutable(s); revísalos antes de usarlos."
                            if scripts
                            else "Solo texto: sin scripts ni hooks."
                        ),
                    },
                }
            )
    out = Path(__file__).resolve().parent.parent / "api" / "src" / "agent_dex" / "data" / "catalog.json"
    out.write_text(json.dumps({"version": 1, "entradas": entries}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(entries)} entries written")


if __name__ == "__main__":
    main()
