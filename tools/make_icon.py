"""Render the plugin icon (1024x1024 PNG) from the UI's own pixel creature.

Pure standard library. Reads the sprite grid from web/src/sprite-data.ts so the
icon always matches the characters shown in the app.
"""

import colorsys
import re
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SIZE = 1024
CELL = 48  # 16 cells * 48 = 768 px creature
HUE = 205


def hsl(h: float, s: float, light: float) -> tuple[int, int, int]:
    r, g, b = colorsys.hls_to_rgb(h / 360, light, s)
    return round(r * 255), round(g * 255), round(b * 255)


def read_grid() -> list[list[str]]:
    text = (ROOT / "web" / "src" / "sprite-data.ts").read_text(encoding="utf-8")
    base = re.search(r"export const BASE: string\[\] = \[(.*?)\];", text, re.S)
    assert base, "BASE grid not found"
    rows = [list(r) for r in re.findall(r'"([^"]{16})"', base.group(1))]
    overlay = {0: ".......aa.......", 1: ".....ooaaoo....."}  # the "investigador" antenna
    for y, row in overlay.items():
        for x, ch in enumerate(row):
            if ch != ".":
                rows[y][x] = ch
    return rows


def render() -> bytes:
    colors = {
        "o": hsl(HUE, 0.40, 0.16),
        "b": hsl(HUE, 0.55, 0.58),
        "l": hsl(HUE, 0.65, 0.78),
        "w": (255, 255, 255),
        "k": (17, 24, 39),
        "m": hsl(HUE, 0.45, 0.28),
        "a": hsl((HUE + 160) % 360, 0.65, 0.55),
    }
    bg = (31, 42, 68)
    frame = hsl(HUE, 0.55, 0.58)
    grid = read_grid()
    margin = (SIZE - CELL * 16) // 2
    raw = bytearray()
    for y in range(SIZE):
        raw.append(0)  # PNG filter: none
        for x in range(SIZE):
            px = bg
            border = 28
            if x < border or y < border or x >= SIZE - border or y >= SIZE - border:
                px = frame
            gx, gy = (x - margin) // CELL, (y - margin) // CELL
            if 0 <= gx < 16 and 0 <= gy < 16 and (x - margin) >= 0 and (y - margin) >= 0:
                ch = grid[gy][gx]
                if ch in colors:
                    px = colors[ch]
            raw.extend(px)

    def chunk(kind: bytes, data: bytes) -> bytes:
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")


if __name__ == "__main__":
    out = ROOT / ".claude-plugin" / "icon.png"
    out.write_bytes(render())
    print(f"wrote {out} ({out.stat().st_size // 1024} KB)")
