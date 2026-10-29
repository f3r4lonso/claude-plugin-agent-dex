// Shared presentational pieces: sprite, badges, empty/error states.
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { compose, palette, resolveIdle, STATE_ICON, STATE_LABEL, toRuns, type AgentState } from "./sprite";
import type { LiveState, Resource } from "./types";
import { GRID } from "./sprite-data";

export function useNow(intervalMs = 15_000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);
  return now;
}

export function visibleState(name: string, live: LiveState | undefined, now: number): AgentState {
  if (!live || live.state === "inactivo") return resolveIdle(name, live?.since ?? null, now);
  return live.state;
}

export function Sprite({
  name,
  archetype,
  state,
  size = 3,
  silhouette = false,
  label,
}: {
  name: string;
  archetype: string;
  state: AgentState;
  size?: number;
  silhouette?: boolean;
  label?: string;
}) {
  const runs = useMemo(() => toRuns(compose(archetype, state), palette(name)), [name, archetype, state]);
  const px = GRID * size * 4;
  return (
    <svg
      className={`sprite${silhouette ? " silhouette" : ""}`}
      data-state={state}
      width={px}
      height={px}
      viewBox={`0 0 ${GRID} ${GRID}`}
      shapeRendering="crispEdges"
      role="img"
      aria-label={label ?? `${name}: ${STATE_LABEL[state]}`}
    >
      <g className="sprite-body">
        {runs.map((r, i) => (
          <rect key={i} x={r.x} y={r.y} width={r.w} height={1} fill={r.color} />
        ))}
      </g>
    </svg>
  );
}

export function StateBadge({ state }: { state: AgentState }) {
  return (
    <span className={`badge state-${state}`}>
      <span aria-hidden="true">{STATE_ICON[state]}</span> {STATE_LABEL[state]}
    </span>
  );
}

export function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "ok" | "warn" | "bad" | "info" }) {
  return <span className={`pill pill-${tone}`}>{children}</span>;
}

export function Empty({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="empty">
      <p className="empty-title">{title}</p>
      {children && <div className="empty-body">{children}</div>}
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="error-box" role="alert">
      <p>{message}</p>
      {onRetry && (
        <button className="btn" onClick={onRetry}>
          Reintentar
        </button>
      )}
    </div>
  );
}

export function Skeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid" aria-busy="true" aria-label="Cargando">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="card skeleton" />
      ))}
    </div>
  );
}

export function number3(n: number): string {
  return `Nº ${String(n).padStart(3, "0")}`;
}

export function sourceLabel(r: Resource): string {
  if (r.source === "plugin") return `plugin ${r.plugin ?? ""}`.trim();
  return r.source === "project" ? "proyecto" : "usuario";
}

export function money(n: number | null | undefined): string {
  return `${(n ?? 0).toFixed(n && n < 0.1 ? 4 : 2)} $`;
}

export function ago(ts: number | null | undefined, now = Date.now()): string {
  if (!ts) return "—";
  const s = Math.max(0, Math.round((now - ts * 1000) / 1000));
  if (s < 60) return `hace ${s} s`;
  if (s < 3600) return `hace ${Math.round(s / 60)} min`;
  if (s < 86400) return `hace ${Math.round(s / 3600)} h`;
  return `hace ${Math.round(s / 86400)} d`;
}
