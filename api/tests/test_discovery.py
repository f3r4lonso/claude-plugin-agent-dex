from agent_dex.discovery import discover

from .conftest import make_client


def test_discovers_agents_and_skills_and_flags_invalid(settings):
    found = {(r.kind, r.name): r for r in discover(settings.claude_home, settings.project_dir)}
    assert ("agent", "reviewer") in found
    assert ("skill", "demo-skill") in found
    reviewer = found[("agent", "reviewer")]
    assert reviewer.tools == ["Read", "Grep"]
    assert reviewer.model == "haiku"
    assert reviewer.body == "You review code."
    broken = found[("agent", "broken")]
    assert broken.valid is False and broken.error


def test_project_resources_and_plugin_dedupe(settings):
    proj = settings.project_dir / ".claude" / "agents"
    proj.mkdir(parents=True)
    (proj / "local.md").write_text("---\nname: local\ndescription: x\n---\nbody", encoding="utf-8")
    for version in ("1.0.0", "1.1.0"):
        d = settings.claude_home / "plugins" / "cache" / "mkt" / "acme" / version
        (d / ".claude-plugin").mkdir(parents=True)
        (d / ".claude-plugin" / "plugin.json").write_text('{"name":"acme"}', encoding="utf-8")
        (d / "agents").mkdir()
        (d / "agents" / "helper.md").write_text("---\nname: helper\ndescription: h\n---\nb", encoding="utf-8")
    found = discover(settings.claude_home, settings.project_dir)
    assert [r.source for r in found if r.name == "local"] == ["project"]
    helpers = [r for r in found if r.name == "helper"]
    assert len(helpers) == 1 and helpers[0].plugin == "acme"


def test_dex_endpoint_does_not_leak_body_in_list(settings):
    client, _, _ = make_client(settings)
    data = client.get("/api/dex").json()
    assert data["counts"] == {"agents": 2, "skills": 1}
    assert all("body" not in r for r in data["resources"])
    rid = next(r["id"] for r in data["resources"] if r["name"] == "reviewer")
    detail = client.get(f"/api/resources/{rid}").json()
    assert detail["body"] == "You review code."
    assert detail["stats"]["runs"] == 0
