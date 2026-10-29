import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { useLive } from "../live";
import { Empty, ErrorBox, Skeleton, Sprite, StateBadge, useNow, visibleState } from "../ui";
import { STATE_LABEL, type AgentState } from "../sprite";
import type { DexResponse, Resource } from "../types";

const ORDER: AgentState[] = ["esperando", "trabajando", "entrenando", "error", "libre", "descansando"];

export function Sala() {
  const [agents, setAgents] = useState<Resource[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [onlyAttention, setOnlyAttention] = useState(false);
  const [asList, setAsList] = useState(false);
  const statuses = useLive((s) => s.statuses);
  const version = useLive((s) => s.dexVersion);
  const now = useNow(10_000);

  useEffect(() => {
    api<DexResponse>("/api/dex")
      .then((d) => setAgents(d.resources.filter((r) => r.kind === "agent")))
      .catch((e) => setError(errorMessage(e)));
  }, [version]);

  if (error) return <ErrorBox message={error} />;
  if (!agents) return <Skeleton />;

  const entries = agents.map((r) => ({ r, state: visibleState(r.name, statuses[r.name.toLowerCase()] ?? r.status, now) }));
  const shown = onlyAttention ? entries.filter((e) => e.state === "esperando" || e.state === "error") : entries;
  const groups = ORDER.map((s) => ({ s, items: shown.filter((e) => e.state === s) })).filter((g) => g.items.length);

  return (
    <section aria-labelledby="h-sala">
      <header className="view-head">
        <div>
          <h1 id="h-sala">Sala</h1>
          <p className="muted">Tus agentes, ahora mismo. Se actualiza en vivo.</p>
        </div>
        <div className="toolbar">
          <label className="check">
            <input type="checkbox" checked={onlyAttention} onChange={(e) => setOnlyAttention(e.target.checked)} />
            Solo lo que requiere mi atención
          </label>
          <label className="check">
            <input type="checkbox" checked={asList} onChange={(e) => setAsList(e.target.checked)} />
            Vista de lista
          </label>
        </div>
      </header>

      {agents.length === 0 ? (
        <Empty title="No hay agentes en la Sala">Captura o crea un agente para verlo aquí.</Empty>
      ) : groups.length === 0 ? (
        <Empty title="Nada requiere tu atención ahora mismo" />
      ) : (
        groups.map(({ s, items }) => (
          <div key={s} className={`zone zone-${s}`}>
            <h2 className="zone-title">
              {STATE_LABEL[s]} <span className="count">{items.length}</span>
            </h2>
            {asList ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>Agente</th>
                    <th>Estado</th>
                    <th>Detalle</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(({ r, state }) => (
                    <tr key={r.id}>
                      <td>
                        <a href={`#/resource/${r.id}`}>{r.name}</a>
                      </td>
                      <td>
                        <StateBadge state={state} />
                      </td>
                      <td>{statuses[r.name.toLowerCase()]?.detail ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <ul className="stage" role="list">
                {items.map(({ r, state }) => (
                  <li key={r.id} className="actor">
                    <a href={s === "esperando" ? "#/bandeja" : `#/resource/${r.id}`} className="actor-link">
                      <Sprite name={r.name} archetype={r.archetype} state={state} size={2} />
                      <span className="actor-name">{r.name}</span>
                      <span className="small muted">{statuses[r.name.toLowerCase()]?.detail ?? (s === "libre" ? r.hobby : "")}</span>
                    </a>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))
      )}
    </section>
  );
}
