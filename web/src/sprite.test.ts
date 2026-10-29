import { describe, expect, it } from "vitest";
import { ARCHETYPE_OVERLAY, BASE, EYES_CLOSED, GRID, PROPS } from "./sprite-data";
import { compose, resolveIdle, toRuns, palette, type AgentState } from "./sprite";

const STATES: AgentState[] = ["trabajando", "entrenando", "descansando", "libre", "esperando", "error"];

describe("sprite data", () => {
  it("keeps every row exactly 16 wide", () => {
    expect(BASE).toHaveLength(GRID);
    for (const row of BASE) expect(row).toHaveLength(GRID);
    expect(EYES_CLOSED).toHaveLength(GRID);
    for (const overlay of Object.values(ARCHETYPE_OVERLAY)) {
      for (const row of Object.values(overlay)) expect(row).toHaveLength(GRID);
    }
  });

  it("props fit inside the grid", () => {
    for (const [name, p] of Object.entries(PROPS)) {
      const width = Math.max(...p.rows.map((r) => r.length));
      expect(p.x + width, name).toBeLessThanOrEqual(GRID);
      expect(p.y + p.rows.length, name).toBeLessThanOrEqual(GRID);
    }
  });
});

describe("compose", () => {
  it("renders every archetype in every state with 16x16 rows", () => {
    for (const a of Object.keys(ARCHETYPE_OVERLAY)) {
      for (const s of STATES) {
        const rows = compose(a, s);
        expect(rows).toHaveLength(GRID);
        for (const r of rows) expect(r).toHaveLength(GRID);
      }
    }
  });

  it("closes the eyes only when resting", () => {
    // The "z" prop sits right of the head (columns 13+), so compare the head only.
    expect(compose("investigador", "descansando")[4]?.slice(0, 13)).toBe(EYES_CLOSED.slice(0, 13));
    expect(compose("investigador", "trabajando")[4]?.slice(0, 13)).toBe(BASE[4]?.slice(0, 13));
  });

  it("only uses colors that exist in the palette", () => {
    const colors = palette("x");
    for (const s of STATES) {
      for (const row of compose("artista", s)) {
        for (const ch of row) if (ch !== ".") expect(colors[ch], ch).toBeDefined();
      }
    }
  });
});

describe("toRuns", () => {
  it("merges adjacent pixels of one color", () => {
    expect(toRuns(["aab."], { a: "red", b: "blue" })).toEqual([
      { x: 0, y: 0, w: 2, color: "red" },
      { x: 2, y: 0, w: 1, color: "blue" },
    ]);
  });
});

describe("resolveIdle", () => {
  it("shows free time right after finishing work", () => {
    const now = 1_000_000_000_000;
    expect(resolveIdle("x", now / 1000 - 10, now)).toBe("libre");
  });
  it("rotates between rest and free time for long-idle agents", () => {
    const seen = new Set<string>();
    for (let i = 0; i < 12; i++) seen.add(resolveIdle("reviewer", null, i * 90_000));
    expect(seen).toEqual(new Set(["libre", "descansando"]));
  });
  it("is stable within one time bucket", () => {
    expect(resolveIdle("a", null, 5_000)).toBe(resolveIdle("a", null, 80_000));
  });
});
