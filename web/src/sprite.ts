import { ARCHETYPE_OVERLAY, BASE, EYES_CLOSED, GRID, HOBBY_PROP, PROPS } from "./sprite-data";

export type AgentState = "trabajando" | "entrenando" | "descansando" | "libre" | "esperando" | "error";

export type Run = { x: number; y: number; w: number; color: string };

export function hash(text: string): number {
  let h = 2166136261;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function palette(name: string): Record<string, string> {
  const hue = hash(name) % 360;
  return {
    o: `hsl(${hue} 40% 16%)`,
    b: `hsl(${hue} 55% 58%)`,
    l: `hsl(${hue} 65% 78%)`,
    d: `hsl(${hue} 50% 38%)`,
    w: "#ffffff",
    k: "#111827",
    m: `hsl(${hue} 45% 28%)`,
    a: `hsl(${(hue + 160) % 360} 65% 55%)`,
    g: "#8b95a7",
    y: "#facc15",
    r: "#ef4444",
  };
}

/** Compose the creature grid for an archetype and state. */
export function compose(archetype: string, state: AgentState): string[] {
  const rows = BASE.map((r) => r.split(""));
  const overlay = ARCHETYPE_OVERLAY[archetype] ?? {};
  for (const [rowIndex, text] of Object.entries(overlay)) {
    const row = rows[Number(rowIndex)];
    if (!row) continue;
    text.split("").forEach((ch, x) => {
      if (ch !== ".") row[x] = ch;
    });
  }
  if (state === "descansando") rows[4] = EYES_CLOSED.split("");
  const propName = propFor(archetype, state);
  const prop = propName ? PROPS[propName] : undefined;
  if (prop) {
    prop.rows.forEach((text, dy) => {
      const row = rows[prop.y + dy];
      if (!row) return;
      text.split("").forEach((ch, dx) => {
        if (ch !== "." && prop.x + dx < GRID) row[prop.x + dx] = ch;
      });
    });
  }
  return rows.map((r) => r.join(""));
}

export function propFor(archetype: string, state: AgentState): string | null {
  switch (state) {
    case "trabajando":
      return "laptop";
    case "entrenando":
      return "dumbbell";
    case "descansando":
      return "z";
    case "esperando":
      return "question";
    case "error":
      return "alert";
    case "libre":
      return HOBBY_PROP[archetype] ?? "book";
  }
}

/** Merge horizontal runs of the same color to keep the SVG small. */
export function toRuns(rows: string[], colors: Record<string, string>): Run[] {
  const runs: Run[] = [];
  rows.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const ch = row[x] as string;
      if (ch === "." || !colors[ch]) {
        x++;
        continue;
      }
      let w = 1;
      while (row[x + w] === ch) w++;
      runs.push({ x, y, w, color: colors[ch] as string });
      x += w;
    }
  });
  return runs;
}

const IDLE_BUCKET_MS = 90_000;

/** "inactivo" has no animation of its own: it rotates between rest and free time. */
export function resolveIdle(name: string, since: number | null, nowMs: number): AgentState {
  if (since !== null && nowMs - since * 1000 < 60_000) return "libre";
  const bucket = Math.floor(nowMs / IDLE_BUCKET_MS);
  return (hash(name) + bucket) % 3 === 0 ? "libre" : "descansando";
}

export const STATE_LABEL: Record<AgentState, string> = {
  trabajando: "Trabajando",
  entrenando: "Entrenando",
  descansando: "Descansando",
  libre: "Tiempo libre",
  esperando: "Esperando",
  error: "Error",
};

export const STATE_ICON: Record<AgentState, string> = {
  trabajando: "●",
  entrenando: "◐",
  descansando: "☾",
  libre: "☺",
  esperando: "⏸",
  error: "✖",
};
