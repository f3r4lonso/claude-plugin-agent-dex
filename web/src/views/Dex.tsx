import { useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "../api";
import { useLive } from "../live";
import { Empty, ErrorBox, number3, Pill, Skeleton, Sprite, sourceLabel, StateBadge, useNow, visibleState } from "../ui";
import type { DexResponse, GlossaryEntry, Resource } from "../types";

export function Dex() {
  const [data, setData] = useState<DexResponse | null>(null);
  const [glossary, setGlossary] = useState<GlossaryEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [kind, setKind] = useState<"all" | "agent" | "skill">("all");
  const [source, setSource] = useState("all");
  const statuses = useLive((s) => s.statuses);
  const version = useLive((s) => s.dexVersion);
  const now = useNow();

  const load = () => {
    setError(null);
    api<DexResponse>("/api/dex")
      .then(setData)
      .catch((e) => setError(errorMessage(e)));
    api<GlossaryEntry[]>("/api/glossary")
      .then(setGlossary)
      .catch(() => undefined);
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [version]);

  const numbered = useMemo(() => (data?.resources ?? []).map((r, i) => ({ r, n: i + 1 })), [data]);
  const filtered = numbered.filter(({ r }) => {
    if (kind !== "all" && r.kind !== kind) return false;
    if (source !== "all" && r.source !== source) return false;
    const text = `${r.name} ${r.description}`.toLowerCase();
    return !q || text.includes(q.toLowerCase());
  });
  const missing = glossary.filter((g) => !g.instalada);
  const owned = glossary.length - missing.length;

  if (error) return <ErrorBox message={error} onRetry={load} />;
  if (!data) return <Skeleton />;

  return (
    <section aria-labelledby="h-dex">
      <header className="view-head">
        <div>
          <h1 id="h-dex">Tu Dex</h1>
          <p className="muted">
            {data.counts.agents} agentes · {data.counts.skills} skills
            {glossary.length > 0 && ` · Glosario: tienes ${owned} de ${glossary.length}`}
          </p>
        </div>
        <div className="toolbar">
          <label className="field">
            <span className="sr-only">Buscar</span>
            <input type="search" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} />
          </label>
          <label className="field">
            <span className="sr-only">Tipo</span>
            <select value={kind} onChange={(e) => setKind(e.target.value as typeof kind)}>
              <option value="all">Todos</option>
              <option value="agent">Agentes</option>
              <option value="skill">Skills</option>
            </select>
          </label>
          <label className="field">
            <span className="sr-only">Origen</span>
            <select value={source} onChange={(e) => setSource(e.target.value)}>
              <option value="all">Cualquier origen</option>
              <option value="user">Usuario</option>
              <option value="project">Proyecto</option>
              <option value="plugin">Plugins</option>
            </select>
          </label>
        </div>
      </header>

      {data.resources.length === 0 ? (
        <Empty title="Aún no tienes agentes ni skills">
          Captura uno desde el <a href="#/glosario">Glosario</a>.
        </Empty>
      ) : filtered.length === 0 ? (
        <Empty title="Nada coincide con los filtros" />
      ) : (
        <ul className="grid" role="list">
          {filtered.map(({ r, n }) => (
            <DexCard key={r.id} r={r} n={n} now={now} live={statuses[r.name.toLowerCase()] ?? r.status} />
          ))}
        </ul>
      )}

      {missing.length > 0 && kind !== "agent" && !q && source === "all" && (
        <>
          <h2 className="section-title">Por descubrir</h2>
          <ul className="grid" role="list">
            {missing.slice(0, 8).map((g) => (
              <li key={g.slug} className="card card-unknown">
                <a href={`#/glosario?e=${g.slug}`} className="card-link" aria-label={`Entrada del Glosario sin capturar: ${g.nombre}`}>
                  <div className="card-top">
                    <span className="num">???</span>
                    <Pill>{g.tipo === "agent" ? "agente" : "skill"}</Pill>
                  </div>
                  <div className="card-art">
                    <Sprite name={g.nombre} archetype="investigador" state="descansando" silhouette size={2} label="Silueta de entrada no capturada" />
                  </div>
                  <h3 className="card-name">?????</h3>
                  <p className="muted small">Capturar en el Glosario</p>
                </a>
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function DexCard({ r, n, now, live }: { r: Resource; n: number; now: number; live: Resource["status"] }) {
  const isAgent = r.kind === "agent";
  const state = visibleState(r.name, live, now);
  return (
    <li className="card">
      <a href={`#/resource/${r.id}`} className="card-link">
        <div className="card-top">
          <span className="num">{number3(n)}</span>
          <Pill tone={isAgent ? "info" : "neutral"}>{isAgent ? "agente" : "skill"}</Pill>
        </div>
        <div className="card-art">
          <Sprite name={r.name} archetype={r.archetype} state={isAgent ? state : "libre"} size={2} />
        </div>
        <h3 className="card-name">{r.name}</h3>
        {isAgent ? <StateBadge state={state} /> : <span className="badge">Skill</span>}
        <p className="muted small clamp">{r.description || "Sin descripción"}</p>
        <p className="meta small">
          {sourceLabel(r)} {!r.valid && <Pill tone="warn">archivo con aviso</Pill>}
        </p>
      </a>
    </li>
  );
}
