import { useEffect, useRef, useState } from "react";
import { api, errorMessage } from "../api";
import { seedSessionEvents, useLive } from "../live";
import { ago, Empty, ErrorBox, money, Pill, Skeleton, Sprite, sourceLabel, StateBadge, useNow, visibleState } from "../ui";
import { STATE_LABEL, type AgentState } from "../sprite";
import type { Resource, RunRow, SessionEvent, SessionInfo } from "../types";
import { Permission } from "./Bandeja";

const PREVIEW_STATES: AgentState[] = ["trabajando", "entrenando", "descansando", "libre", "esperando", "error"];
type Tab = "resumen" | "chat" | "tarea" | "historial";

export function ResourceView({ id }: { id: string }) {
  const [r, setR] = useState<Resource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("resumen");
  const [preview, setPreview] = useState<AgentState | null>(null);
  const statuses = useLive((s) => s.statuses);
  const now = useNow();

  useEffect(() => {
    setR(null);
    setError(null);
    api<Resource>(`/api/resources/${id}`)
      .then(setR)
      .catch((e) => setError(errorMessage(e)));
  }, [id]);

  if (error) return <ErrorBox message={error} />;
  if (!r) return <Skeleton count={1} />;
  const isAgent = r.kind === "agent";
  const real = visibleState(r.name, statuses[r.name.toLowerCase()] ?? r.status, now);
  const shown = preview ?? real;

  return (
    <section aria-labelledby="h-res">
      <p>
        <a href="#/dex">← Dex</a>
      </p>
      <header className="ficha-head">
        <div className="ficha-art">
          <Sprite name={r.name} archetype={r.archetype} state={isAgent ? shown : "libre"} size={4} />
        </div>
        <div>
          <h1 id="h-res">{r.name}</h1>
          <p className="meta">
            <Pill tone={isAgent ? "info" : "neutral"}>{isAgent ? "agente" : "skill"}</Pill> {sourceLabel(r)} · Claude Code
            {r.model && <> · modelo {r.model}</>}
          </p>
          {isAgent && <StateBadge state={real} />}
          {isAgent && (
            <fieldset className="state-picker">
              <legend className="small muted">Previsualizar animación</legend>
              {PREVIEW_STATES.map((s) => (
                <button
                  key={s}
                  className={`chip${shown === s ? " chip-on" : ""}`}
                  aria-pressed={shown === s}
                  onClick={() => setPreview(preview === s ? null : s)}
                >
                  {STATE_LABEL[s]}
                </button>
              ))}
            </fieldset>
          )}
        </div>
      </header>

      <div className="tabs" role="tablist">
        {(["resumen", ...(isAgent ? ["chat", "tarea", "historial"] : [])] as Tab[]).map((t) => (
          <button key={t} role="tab" aria-selected={tab === t} className={`tab${tab === t ? " tab-on" : ""}`} onClick={() => setTab(t)}>
            {{ resumen: "Resumen", chat: "Chat", tarea: "Tarea sin supervisión", historial: "Historial" }[t]}
          </button>
        ))}
      </div>

      {tab === "resumen" && <Summary r={r} />}
      {tab === "chat" && isAgent && <Chat r={r} />}
      {tab === "tarea" && isAgent && <Task r={r} />}
      {tab === "historial" && isAgent && <History r={r} />}
    </section>
  );
}

function Summary({ r }: { r: Resource }) {
  const s = r.stats;
  return (
    <div className="stack">
      {!r.valid && <ErrorBox message={`Este archivo tiene un problema: ${r.error}`} />}
      <div className="panel">
        <h2>Descripción</h2>
        <p>{r.description || "Sin descripción."}</p>
      </div>
      {r.kind === "agent" && (
        <div className="panel">
          <h2>Estadísticas</h2>
          {s && s.runs > 0 ? (
            <dl className="stats">
              <div><dt>Tareas y chats registrados</dt><dd>{s.runs}</dd></div>
              <div><dt>Terminados bien</dt><dd>{s.done}</dd></div>
              <div><dt>Tasa de éxito</dt><dd>{s.success_rate === null ? "sin datos" : `${Math.round(s.success_rate * 100)} %`}</dd></div>
              <div><dt>Gasto acumulado</dt><dd>{money(s.cost_usd)}</dd></div>
              <div><dt>Última actividad</dt><dd>{ago(s.last)}</dd></div>
            </dl>
          ) : (
            <p className="muted">Sin datos todavía. Las estadísticas salen de lo que ejecutes desde Agent Dex.</p>
          )}
        </div>
      )}
      <div className="panel">
        <h2>Herramientas</h2>
        <p>{r.tools.length ? r.tools.join(", ") : "Las que el cliente permita por defecto."}</p>
      </div>
      <div className="panel">
        <h2>Ubicación</h2>
        <p className="code-inline">{r.path}</p>
      </div>
      {r.body && (
        <details className="panel">
          <summary>Instrucciones (solo lectura)</summary>
          <pre className="code">{r.body}</pre>
        </details>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- transcript

export function Transcript({ sessionId, events }: { sessionId: string; events: SessionEvent[] }) {
  const delta = useLive((s) => s.deltas[sessionId]);
  const inbox = useLive((s) => s.inbox);
  const now = useNow(30_000);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [events.length, delta]);
  const pending = inbox.filter((i) => i.session_id === sessionId);
  return (
    <div className="transcript" role="log" aria-live="polite" aria-label="Conversación">
      {events.map((e, i) => {
        switch (e.type) {
          case "user":
            return <div key={i} className="msg msg-user">{e.text}</div>;
          case "assistant":
            return <div key={i} className="msg msg-agent">{e.text}</div>;
          case "tool":
            return (
              <details key={i} className="tool">
                <summary>Usó la herramienta {e.name}</summary>
                <pre className="code">{JSON.stringify(e.input, null, 2)}</pre>
              </details>
            );
          case "permission_resolved":
            return <div key={i} className="note">{e.allow ? "Permitiste" : "Denegaste"} «{e.tool}».</div>;
          case "result":
            return (
              <div key={i} className={`note${e.limit || e.is_error ? " note-warn" : ""}`}>
                {e.limit ?? (e.is_error ? "El turno terminó con un error." : "Turno completado.")} · {money(e.cost_usd)} · {e.turns} turnos
              </div>
            );
          case "error":
            return <ErrorBox key={i} message={e.message ?? "Error"} />;
          default:
            return null;
        }
      })}
      {delta && <div className="msg msg-agent msg-live">{delta}</div>}
      {pending.map((p) => (
        <div key={p.id} className="panel pending">
          <Permission item={p} now={now} />
        </div>
      ))}
      <div ref={end} />
    </div>
  );
}

// ---------------------------------------------------------------------- chat

const lastChat = new Map<string, string>();

function Chat({ r }: { r: Resource }) {
  const [sid, setSid] = useState<string | null>(lastChat.get(r.id) ?? null);
  const [text, setText] = useState("");
  const [error, setError] = useState<string | null>(null);
  const events = useLive((s) => (sid ? s.events[sid] : undefined)) ?? [];
  const info = useLive((s) => (sid ? s.sessions[sid] : undefined));

  useEffect(() => {
    if (!sid) return;
    api<SessionInfo>(`/api/sessions/${sid}`)
      .then((s) => seedSessionEvents(sid, s.events ?? [], s))
      .catch(() => {
        lastChat.delete(r.id);
        setSid(null);
      });
  }, [sid, r.id]);

  const ended = info && ["done", "limit", "error", "cancelled"].includes(info.status);
  const busy = info?.status === "running";

  const send = async () => {
    const message = text.trim();
    if (!message) return;
    setError(null);
    try {
      let id = sid;
      if (!id || ended) {
        const created = await api<SessionInfo>("/api/sessions", { method: "POST", body: { agent_id: r.id, kind: "chat" } });
        id = created.id;
        lastChat.set(r.id, id);
        seedSessionEvents(id, [], created);
        setSid(id);
      }
      await api(`/api/sessions/${id}/message`, { method: "POST", body: { text: message } });
      setText("");
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const stop = () => sid && api(`/api/sessions/${sid}/interrupt`, { method: "POST" }).catch((e) => setError(errorMessage(e)));
  const finish = () => {
    if (!sid) return;
    api(`/api/sessions/${sid}/close`, { method: "POST" }).catch(() => undefined);
    lastChat.delete(r.id);
    setSid(null);
  };

  return (
    <div className="chat">
      <p className="muted small">
        Modo interactivo: el agente te pedirá permiso para editar archivos o ejecutar comandos. Usa tu sesión de Claude Code.
      </p>
      {sid ? (
        <Transcript sessionId={sid} events={events} />
      ) : (
        <Empty title={`Habla con ${r.name}`}>Escribe tu primer mensaje abajo.</Empty>
      )}
      {error && <ErrorBox message={error} />}
      {info && (
        <p className="small muted">
          Estado: {info.status} · {money(info.cost_usd)} de {money(info.max_budget_usd)} · máx. {info.max_turns} turnos
        </p>
      )}
      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <label className="field grow">
          <span className="sr-only">Mensaje</span>
          <textarea
            rows={2}
            value={text}
            placeholder="Escribe un mensaje…"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
          />
        </label>
        <div className="composer-actions">
          <button className="btn btn-primary" type="submit" disabled={busy || !text.trim()}>
            Enviar
          </button>
          {busy && (
            <button className="btn" type="button" onClick={stop}>
              Detener
            </button>
          )}
          {sid && (
            <button className="btn" type="button" onClick={finish}>
              Terminar chat
            </button>
          )}
        </div>
      </form>
    </div>
  );
}

// ---------------------------------------------------------------------- task

function Task({ r }: { r: Resource }) {
  const [prompt, setPrompt] = useState("");
  const [policy, setPolicy] = useState<"readonly" | "ask">("readonly");
  const [turns, setTurns] = useState(10);
  const [budget, setBudget] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [sid, setSid] = useState<string | null>(null);
  const events = useLive((s) => (sid ? s.events[sid] : undefined)) ?? [];
  const info = useLive((s) => (sid ? s.sessions[sid] : undefined));

  useEffect(() => {
    if (!sid) return;
    api<SessionInfo>(`/api/sessions/${sid}`)
      .then((s) => seedSessionEvents(sid, s.events ?? [], s))
      .catch(() => undefined);
  }, [sid]);

  const launch = async () => {
    setError(null);
    try {
      const created = await api<SessionInfo>("/api/sessions", {
        method: "POST",
        body: { agent_id: r.id, kind: "task", prompt, policy, max_turns: turns, max_budget_usd: budget },
      });
      seedSessionEvents(created.id, [], created);
      setSid(created.id);
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const running = info && ["starting", "running", "idle"].includes(info.status);
  return (
    <div className="stack">
      <div className="panel">
        <p className="muted small">
          El agente trabaja solo, con límites obligatorios. En modo «solo lectura» deniega cualquier cambio sin esperar; en modo «preguntar»
          se detiene en la Bandeja hasta que decidas.
        </p>
        <label className="field block">
          <span>Describe la tarea</span>
          <textarea rows={4} value={prompt} onChange={(e) => setPrompt(e.target.value)} maxLength={20000} disabled={!!running} />
        </label>
        <div className="row">
          <label className="field">
            <span>Permisos</span>
            <select value={policy} onChange={(e) => setPolicy(e.target.value as typeof policy)} disabled={!!running}>
              <option value="readonly">Solo lectura (recomendado)</option>
              <option value="ask">Preguntarme cada acción</option>
            </select>
          </label>
          <label className="field">
            <span>Máx. turnos</span>
            <input type="number" min={1} max={50} value={turns} onChange={(e) => setTurns(Number(e.target.value))} disabled={!!running} />
          </label>
          <label className="field">
            <span>Presupuesto máx. ($)</span>
            <input type="number" min={0.01} max={5} step={0.25} value={budget} onChange={(e) => setBudget(Number(e.target.value))} disabled={!!running} />
          </label>
        </div>
        {error && <ErrorBox message={error} />}
        <div className="actions">
          <button className="btn btn-primary" onClick={launch} disabled={!prompt.trim() || !!running}>
            Lanzar tarea
          </button>
          {running && sid && (
            <button className="btn" onClick={() => api(`/api/sessions/${sid}/interrupt`, { method: "POST" }).catch(() => undefined)}>
              Detener
            </button>
          )}
        </div>
      </div>
      {sid && (
        <div className="panel">
          <h2>
            Resultado <Pill tone={info?.status === "done" ? "ok" : info?.status === "error" || info?.status === "limit" ? "bad" : "info"}>{info?.status ?? "…"}</Pill>
          </h2>
          <Transcript sessionId={sid} events={events} />
          {info && <p className="small muted">{money(info.cost_usd)} · {info.turns} turnos</p>}
        </div>
      )}
    </div>
  );
}

// ------------------------------------------------------------------- history

function History({ r }: { r: Resource }) {
  const [rows, setRows] = useState<RunRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<RunRow[]>("/api/runs")
      .then((all) => setRows(all.filter((x) => x.agent.toLowerCase() === r.name.toLowerCase())))
      .catch((e) => setError(errorMessage(e)));
  }, [r.name]);
  if (error) return <ErrorBox message={error} />;
  if (!rows) return <Skeleton count={1} />;
  if (rows.length === 0) return <Empty title="Sin historial">Aquí aparecerán los chats y tareas que ejecutes desde Agent Dex.</Empty>;
  return (
    <table className="table">
      <thead>
        <tr><th>Cuándo</th><th>Tipo</th><th>Estado</th><th>Gasto</th><th>Resultado</th></tr>
      </thead>
      <tbody>
        {rows.map((x) => (
          <tr key={x.id}>
            <td>{ago(x.created)}</td>
            <td>{x.kind === "chat" ? "Chat" : "Tarea"}</td>
            <td>{x.status}</td>
            <td>{money(x.cost_usd)}</td>
            <td className="clamp">{x.result || x.prompt || "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
