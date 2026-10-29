"""Spike 1.1: can Python drive Claude Code with streaming, permission prompts and limits?

Runs in a throwaway temp directory. Each scenario uses a tiny budget and the
cheapest model alias. Nothing here is product code.
"""

import asyncio
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    StreamEvent,
    SystemMessage,
    TextBlock,
    ToolUseBlock,
    UserMessage,
    query,
)

MODEL = "haiku"
LOG: dict = {}


def summarize(msg) -> dict:
    kind = type(msg).__name__
    if isinstance(msg, AssistantMessage):
        parts = []
        for b in msg.content:
            if isinstance(b, TextBlock):
                parts.append({"text": b.text[:80]})
            elif isinstance(b, ToolUseBlock):
                parts.append({"tool": b.name})
        return {"type": kind, "parts": parts}
    if isinstance(msg, ResultMessage):
        return {
            "type": kind,
            "subtype": msg.subtype,
            "is_error": msg.is_error,
            "turns": msg.num_turns,
            "cost_usd": msg.total_cost_usd,
            "terminal_reason": msg.terminal_reason,
            "denials": len(msg.permission_denials or []),
        }
    if isinstance(msg, SystemMessage):
        return {"type": kind, "subtype": msg.subtype}
    if isinstance(msg, StreamEvent):
        return {"type": kind}
    return {"type": kind}


def compact(events: list[dict]) -> list[dict]:
    out: list[dict] = []
    for e in events:
        if out and out[-1]["type"] == e["type"] == "StreamEvent":
            out[-1]["count"] = out[-1].get("count", 1) + 1
        else:
            out.append(e)
    return out


async def scenario_interactive(decision: str, workdir: Path) -> dict:
    """Permission prompt surfaced to Python; we answer allow or deny."""
    asked: list[dict] = []
    t_ask = {}

    async def can_use_tool(tool_name, tool_input, ctx):
        t_ask["t"] = time.monotonic()
        asked.append({"tool": tool_name, "input_keys": sorted(tool_input)})
        await asyncio.sleep(1.0)  # simulate a human taking a moment to answer
        if decision == "allow":
            return PermissionResultAllow()
        return PermissionResultDeny(message="Denied by the user in the Dex UI.")

    options = ClaudeAgentOptions(
        model=MODEL,
        cwd=str(workdir),
        permission_mode="default",
        can_use_tool=can_use_tool,
        max_turns=4,
        max_budget_usd=0.25,
        include_partial_messages=True,
        setting_sources=[],  # ignore the user's own settings/hooks for a clean test
    )
    events: list[dict] = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query(
            "Create a file named hello.txt in the current directory containing the word hi. "
            "Then reply 'done' in one word."
        )
        async for msg in client.receive_response():
            events.append(summarize(msg))
    return {
        "decision": decision,
        "permission_requests": asked,
        "file_created": (workdir / "hello.txt").exists(),
        "events": compact(events),
    }


async def scenario_headless(workdir: Path) -> dict:
    """Non-interactive: read-only tools, hard limits, no callback."""
    options = ClaudeAgentOptions(
        model=MODEL,
        cwd=str(workdir),
        allowed_tools=["Read", "Glob", "Grep"],
        permission_mode="default",
        max_turns=3,
        max_budget_usd=0.25,
        setting_sources=[],
    )
    events: list[dict] = []
    async for msg in query(prompt="List the files in the current directory, then say 'ok'.", options=options):
        events.append(summarize(msg))
    return {"events": compact(events)}


async def scenario_interrupt(workdir: Path) -> dict:
    """Cancel mid-response."""
    options = ClaudeAgentOptions(
        model=MODEL,
        cwd=str(workdir),
        max_turns=2,
        max_budget_usd=0.25,
        include_partial_messages=True,
        setting_sources=[],
    )
    events: list[dict] = []
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Count slowly from 1 to 200, one number per line.")
        n = 0
        async for msg in client.receive_response():
            events.append(summarize(msg))
            if isinstance(msg, StreamEvent):
                n += 1
                if n == 5:
                    await client.interrupt()
    return {"stream_events_before_interrupt": n, "events": compact(events)[-4:]}


async def main(which: str) -> None:
    root = Path(tempfile.mkdtemp(prefix="dex-spike-"))
    try:
        if which in ("allow", "all"):
            d = root / "allow"
            d.mkdir()
            LOG["interactive_allow"] = await scenario_interactive("allow", d)
        if which in ("deny", "all"):
            d = root / "deny"
            d.mkdir()
            LOG["interactive_deny"] = await scenario_interactive("deny", d)
        if which in ("headless", "all"):
            d = root / "headless"
            d.mkdir()
            (d / "a.txt").write_text("x")
            LOG["headless"] = await scenario_headless(d)
        if which in ("interrupt", "all"):
            d = root / "interrupt"
            d.mkdir()
            LOG["interrupt"] = await scenario_interrupt(d)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(json.dumps(LOG, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "all"))
