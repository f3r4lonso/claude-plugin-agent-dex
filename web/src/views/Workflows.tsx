import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { useLive } from "../live";
import { ago, Empty, ErrorBox, money, Pill, Skeleton } from "../ui";
import type { DexResponse, Resource, Workflow, WorkflowRun, WorkflowStep } from "../types";

type Draft = Omit<Workflow, "id"> & { id?: string };

const blankStep = (type: "agent" | "human"): WorkflowStep => ({
  type,
  agent: null,
  instruction: "",
  policy: "readonly",
  max_turns: 10,
  max_budget_usd: 1,
});

const blank = (): Draft => ({ name: "", goal: "", steps: [blankStep("agent")], max_total_budget_usd: 3 });

const RUN_TONE: Record<string, "ok" | "warn" | "bad" | "info" | "neutral"> = {
  running: "info",
  waiting_human: "warn",
  done: "ok",
  failed: "bad",
  rejected: "bad",
  cancelled: "neutral",
  interrupted: "warn",
  limit: "bad",
};
const RUN_LABEL: Record<string, string> = {
  running: "En curso",
  waiting_human: "Esperando tu decisión",
  done: "Terminado",
  failed: "Falló",
  rejected: "Rechazado",
  cancelled: "Cancelado",
  interrupted: "Interrumpido",
  limit: "Límite alcanzado",
  pending: "Pendiente",
};

export function Workflows() {
  const [list, setList] = useState<Workflow[] | null>(null);
  const [agents, setAgents] = useState<Resource[]>([]);
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [error, setError] = useState<string | null>(null);
  const live = useLive((s) => s.workflowRuns);

  const load = () => {
    api<Workflow[]>("/api/workflows").then(setList).catch((e) => setError(errorMessage(e)));
    api<WorkflowRun[]>("/api/workflow-runs").then(setRuns).catch(() => undefined);
  };
  useEffect(() => {
    load();
    api<DexResponse>("/api/dex").then((d) => setAgents(d.resources.filter((r) => r.kind === "agent"))).catch(() => undefined);
  }, []);

  const merged = Object.values({ ...Object.fromEntries(runs.map((r) => [r.id, r])), ...live }).sort((a, b) => b.created - a.created);

  const run = async (wid: string) => {
    setError(null);
    try {
      const r = await api<WorkflowRun>(`/api/workflows/${wid}/run`, { method: "POST" });
      setRuns((prev) => [r, ...prev]);
    } catch (e) {
      setError(errorMessage(e));
    }
  };
  const remove = async (wid: string) => {
    await api(`/api/workflows/${wid}`, { method: "DELETE" }).catch((e) => setError(errorMessage(e)));
    load();
  };

  if (!list) return error ? <ErrorBox message={error} onRetry={load} /> : <Skeleton count={2} />;

  return (
    <section aria-labelledby="h-wf">
      <header className="view-head">
        <div>
          <h1 id="h-wf">Workflows <Pill tone="warn">beta</Pill></h1>
          <p className="muted">Agentes que se pasan el trabajo uno a otro, con pausas para que decidas tú. En esta beta el flujo es lineal y, si cierras la app, lo que estaba en curso queda «interrumpido».</p>
        </div>
        {!draft && <button className="btn btn-primary" onClick={() => setDraft(blank())}>Nuevo workflow</button>}
      </header>
      {error && <ErrorBox message={error} />}

      {draft && <Editor draft={draft} agents={agents} onCancel={() => setDraft(null)} onSaved={() => { setDraft(null); load(); }} />}

      {!draft && list.length === 0 && <Empty title="Aún no tienes workflows">Crea uno: por ejemplo Investigar → Aprobar → Redactar.</Empty>}
      {!draft && list.length > 0 && (
        <ul className="stack" role="list">
          {list.map((w) => (
            <li key={w.id} className="panel">
              <div className="pending-head">
                <div>
                  <h2 className="pending-title">{w.name}</h2>
                  <p className="muted small">{w.steps.map((s) => (s.type === "human" ? "👤 Humano" : s.agent)).join("  →  ")}</p>
                </div>
                <div className="actions">
                  <button className="btn btn-primary" onClick={() => run(w.id)}>Ejecutar</button>
                  <button className="btn" onClick={() => setDraft(w)}>Editar</button>
                  <button className="btn btn-danger" onClick={() => remove(w.id)}>Borrar</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      )}

      {!draft && merged.length > 0 && (
        <>
          <h2 className="section-title">Ejecuciones</h2>
          <ul className="stack" role="list">
            {merged.slice(0, 10).map((r) => (
              <RunCard key={r.id} run={r} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function RunCard({ run }: { run: WorkflowRun }) {
  const cancel = () => api(`/api/workflow-runs/${run.id}/cancel`, { method: "POST" }).catch(() => undefined);
  const active = run.status === "running" || run.status === "waiting_human";
  return (
    <li className="panel">
      <div className="pending-head">
        <div>
          <h3 className="pending-title">{run.workflow_name}</h3>
          <p className="muted small">{ago(run.created)} · {money(run.cost_usd)}</p>
        </div>
        <Pill tone={RUN_TONE[run.status] ?? "neutral"}>{RUN_LABEL[run.status] ?? run.status}</Pill>
      </div>
      <ol className="steps">
        {run.steps.map((s) => (
          <li key={s.index} className={`step step-${s.status}`}>
            <strong>{s.type === "human" ? "Decisión humana" : s.agent}</strong> <Pill tone={RUN_TONE[s.status] ?? "neutral"}>{RUN_LABEL[s.status] ?? s.status}</Pill>
            {s.output && (
              <details>
                <summary className="small">Resultado</summary>
                <pre className="code">{s.output}</pre>
              </details>
            )}
          </li>
        ))}
      </ol>
      {run.status === "waiting_human" && <p className="note note-warn">Hay una decisión pendiente en la <a href="#/bandeja">Bandeja</a>.</p>}
      {run.error && <p className="note note-warn">{run.error}</p>}
      {active && <button className="btn" onClick={cancel}>Cancelar ejecución</button>}
    </li>
  );
}

function Editor({ draft, agents, onCancel, onSaved }: { draft: Draft; agents: Resource[]; onCancel: () => void; onSaved: () => void }) {
  const [d, setD] = useState<Draft>(draft);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const setStep = (i: number, patch: Partial<WorkflowStep>) =>
    setD((cur) => ({ ...cur, steps: cur.steps.map((s, k) => (k === i ? { ...s, ...patch } : s)) }));
  const move = (i: number, dir: -1 | 1) =>
    setD((cur) => {
      const steps = [...cur.steps];
      const j = i + dir;
      if (j < 0 || j >= steps.length) return cur;
      [steps[i], steps[j]] = [steps[j] as WorkflowStep, steps[i] as WorkflowStep];
      return { ...cur, steps };
    });

  const save = async () => {
    setBusy(true);
    setError(null);
    const body = { name: d.name, goal: d.goal, steps: d.steps, max_total_budget_usd: d.max_total_budget_usd };
    try {
      if (d.id) await api(`/api/workflows/${d.id}`, { method: "PUT", body });
      else await api("/api/workflows", { method: "POST", body });
      onSaved();
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };

  return (
    <form className="panel stack" onSubmit={(e) => { e.preventDefault(); void save(); }}>
      <h2>{d.id ? "Editar workflow" : "Nuevo workflow"}</h2>
      <label className="field block"><span>Nombre</span><input value={d.name} onChange={(e) => setD({ ...d, name: e.target.value })} maxLength={80} required /></label>
      <label className="field block"><span>Objetivo (lo ven todos los agentes)</span><textarea rows={2} value={d.goal} onChange={(e) => setD({ ...d, goal: e.target.value })} /></label>
      <ol className="steps editor">
        {d.steps.map((s, i) => (
          <li key={i} className="step">
            <div className="row">
              <strong>Paso {i + 1}</strong>
              <label className="field"><span className="sr-only">Tipo</span>
                <select value={s.type} onChange={(e) => setStep(i, { type: e.target.value as "agent" | "human" })}>
                  <option value="agent">Agente</option>
                  <option value="human" disabled={i === 0}>Decisión humana</option>
                </select>
              </label>
              {s.type === "agent" && (
                <label className="field"><span className="sr-only">Agente</span>
                  <select value={s.agent ?? ""} onChange={(e) => setStep(i, { agent: e.target.value || null })} required>
                    <option value="">Elige un agente…</option>
                    {agents.map((a) => <option key={a.id} value={a.name}>{a.name}</option>)}
                  </select>
                </label>
              )}
              <span className="spacer" />
              <button type="button" className="btn btn-small" onClick={() => move(i, -1)} disabled={i === 0} aria-label={`Subir paso ${i + 1}`}>↑</button>
              <button type="button" className="btn btn-small" onClick={() => move(i, 1)} disabled={i === d.steps.length - 1} aria-label={`Bajar paso ${i + 1}`}>↓</button>
              <button type="button" className="btn btn-small btn-danger" onClick={() => setD({ ...d, steps: d.steps.filter((_, k) => k !== i) })} disabled={d.steps.length === 1} aria-label={`Quitar paso ${i + 1}`}>✕</button>
            </div>
            <label className="field block">
              <span className="small">{s.type === "agent" ? "Instrucción para este paso" : "Qué debe revisar la persona"}</span>
              <textarea rows={2} value={s.instruction} onChange={(e) => setStep(i, { instruction: e.target.value })} required={s.type === "agent"} />
            </label>
            {s.type === "agent" && (
              <div className="row">
                <label className="field"><span className="small">Permisos</span>
                  <select value={s.policy} onChange={(e) => setStep(i, { policy: e.target.value as "ask" | "readonly" })}>
                    <option value="readonly">Solo lectura</option><option value="ask">Preguntarme</option>
                  </select>
                </label>
                <label className="field"><span className="small">Máx. turnos</span><input type="number" min={1} max={50} value={s.max_turns} onChange={(e) => setStep(i, { max_turns: Number(e.target.value) })} /></label>
                <label className="field"><span className="small">Máx. $</span><input type="number" min={0.01} max={5} step={0.25} value={s.max_budget_usd} onChange={(e) => setStep(i, { max_budget_usd: Number(e.target.value) })} /></label>
              </div>
            )}
          </li>
        ))}
      </ol>
      <div className="actions">
        <button type="button" className="btn" onClick={() => setD({ ...d, steps: [...d.steps, blankStep("agent")] })} disabled={d.steps.length >= 12}>+ Agente</button>
        <button type="button" className="btn" onClick={() => setD({ ...d, steps: [...d.steps, blankStep("human")] })} disabled={d.steps.length >= 12}>+ Decisión humana</button>
      </div>
      <label className="field"><span>Presupuesto total del workflow ($, máx. 10)</span><input type="number" min={0.01} max={10} step={0.5} value={d.max_total_budget_usd} onChange={(e) => setD({ ...d, max_total_budget_usd: Number(e.target.value) })} /></label>
      {error && <ErrorBox message={error} />}
      <div className="actions">
        <button className="btn btn-primary" type="submit" disabled={busy}>Guardar</button>
        <button className="btn" type="button" onClick={onCancel}>Cancelar</button>
      </div>
    </form>
  );
}
