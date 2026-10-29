import json

import pytest

from agent_dex.glossary import CaptureError, Glossary

from .conftest import blob_sha

SKILL_MD = b"---\nname: demo\ndescription: d\n---\nhello\n"
EXTRA = b"print('x')\n"
COMMIT = "c" * 40
SKILL_SLUG = "o-r-skills-demo"
AGENT_SLUG = "o-r-agents-helper-md"
FILES = {"skills/demo/SKILL.md": SKILL_MD, "skills/demo/scripts/run.py": EXTRA, "agents/helper.md": b"abc"}


def catalog():
    base = {
        "descripcion": "d",
        "repo": "https://github.com/o/r",
        "commit": COMMIT,
        "licencia": "MIT",
        "clientes": ["claude"],
        "categorias": [],
        "revision": {"fecha": "2026-01-01", "resultado": "ok", "notas": ""},
    }
    return {
        "entradas": [
            {
                **base,
                "id": "o/r/skills/demo",
                "tipo": "skill",
                "nombre": "demo",
                "ruta": "skills/demo",
                "archivos": [
                    {"ruta": "skills/demo/SKILL.md", "bytes": len(SKILL_MD), "sha": blob_sha(SKILL_MD)},
                    {"ruta": "skills/demo/scripts/run.py", "bytes": len(EXTRA), "sha": blob_sha(EXTRA)},
                ],
            },
            {
                **base,
                "id": "o/r/agents/helper.md",
                "tipo": "agent",
                "nombre": "helper",
                "ruta": "agents/helper.md",
                "archivos": [{"ruta": "agents/helper.md", "bytes": 3, "sha": blob_sha(b"abc")}],
            },
        ]
    }


def make(settings, files=FILES, cat=None):
    return Glossary(settings, lambda repo, commit, path: files[path], cat or catalog())


def test_preview_flags_scripts_and_writes_nothing(settings):
    p = make(settings).preview(SKILL_SLUG)
    flags = {f["origen"]: f["requiere_atencion"] for f in p["archivos"]}
    assert flags == {"skills/demo/SKILL.md": False, "skills/demo/scripts/run.py": True}
    assert not (settings.claude_home / "skills" / "demo").exists()


def test_capture_requires_confirmation_and_matching_commit(settings):
    g = make(settings)
    with pytest.raises(CaptureError):
        g.capture(SKILL_SLUG, confirm=False, expected_commit=COMMIT)
    with pytest.raises(CaptureError):
        g.capture(SKILL_SLUG, confirm=True, expected_commit="d" * 40)
    assert not (settings.claude_home / "skills" / "demo").exists()


def test_capture_then_release_restores_state(settings):
    g = make(settings)
    record = g.capture(SKILL_SLUG, confirm=True, expected_commit=COMMIT)
    folder = settings.claude_home / "skills" / "demo"
    assert (folder / "SKILL.md").read_bytes() == SKILL_MD
    assert (folder / "scripts" / "run.py").exists()
    assert record["commit"] == COMMIT
    assert json.loads(settings.captures_path.read_text())[0]["slug"] == SKILL_SLUG
    g.release(SKILL_SLUG)
    assert not folder.exists()
    assert json.loads(settings.captures_path.read_text()) == []


def test_integrity_failure_installs_nothing(settings):
    g = make(settings, {**FILES, "skills/demo/scripts/run.py": b"tampered"})
    with pytest.raises(CaptureError, match="integridad"):
        g.capture(SKILL_SLUG, confirm=True, expected_commit=COMMIT)
    assert not (settings.claude_home / "skills" / "demo").exists()


def test_never_overwrites(settings):
    target = settings.claude_home / "agents" / "helper.md"
    target.write_text("mine", encoding="utf-8")
    with pytest.raises(CaptureError, match="no se sobrescribe"):
        make(settings).capture(AGENT_SLUG, confirm=True, expected_commit=COMMIT)
    assert target.read_text() == "mine"


def test_release_refuses_things_it_did_not_capture(settings):
    target = settings.claude_home / "agents" / "helper.md"
    target.write_text("mine", encoding="utf-8")
    with pytest.raises(CaptureError):
        make(settings).release(AGENT_SLUG)
    assert target.exists()


def test_unsafe_names_and_paths_are_refused(settings):
    cat = catalog()
    cat["entradas"][0]["nombre"] = "../evil"
    with pytest.raises(CaptureError):
        make(settings, cat=cat).preview(SKILL_SLUG)
    cat = catalog()
    cat["entradas"][0]["archivos"][1]["ruta"] = "skills/demo/../../../outside.txt"
    with pytest.raises(CaptureError):
        make(settings, cat=cat).preview(SKILL_SLUG)


def test_shipped_catalog_is_well_formed(settings):
    g = Glossary(settings)
    assert len(g.entries) >= 10
    for e in g.entries.values():
        assert len(e["commit"]) == 40
        assert e["licencia"]
        assert all(len(f["sha"]) == 40 for f in e["archivos"])
        g.preview(e["slug"])  # the install plan must be valid for every shipped entry
