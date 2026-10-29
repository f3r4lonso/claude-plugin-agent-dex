import { useState } from "react";
import { api, errorMessage } from "../api";
import { refreshInbox, useLive } from "../live";
import { ago, Empty, ErrorBox, Pill, useNow } from "../ui";
import type { InboxItem } from "../types";

export function Bandeja() {
  const inbox = useLive((s) => s.inbox);
  const now = useNow(30_000);
  const sorted = [...inbox].sort((a, b) => a.created - b.created);
  return (
    <section aria-labelledby="h-inbox">
      <header className="view-head">
        <div>
          <h1 id="h-inbox">Bandeja</h1>
          <p className="muted">Todo lo que está detenido esperando una decisión tuya. Nada se aprueba solo.</p>
        </div>
      </header>
      {sorted.length === 0 ? (
        <Empty title="No hay nada pendiente">Cuando un agente pida permiso o un workflow necesite tu aprobación, aparecerá aquí.</Empty>
      ) : (
        <ul className="stack" role="list">
          {sorted.map((item) => (
            <li key={item.id} className="panel pending">
              {item.kind === "permission" ? <Permission item={item} now={now} /> : <Approval item={item} now={now} />}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

function Head({ item, now }: { item: InboxItem; now: number }) {
  return (
    <div className="pending-head">
      <div>
        <h2 className="pending-title">{item.title}</h2>
        <p className="muted small">
          {item.agent} · {ago(item.created, now)}
        </p>
      </div>
      <Pill tone="warn">{item.kind === "permission" ? "Permiso" : "Aprobación"}</Pill>
    </div>
  );
}

export function Permission({ item, now }: { item: InboxItem; now: number }) {
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const resolve = async (allow: boolean) => {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/inbox/${item.id}/resolve`, {
        method: "POST",
        body: { allow, message: allow ? undefined : "La persona usuaria denegó esta acción." },
      });
      refreshInbox();
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };
  return (
    <>
      <Head item={item} now={now} />
      <p className="small">El agente quiere usar la herramienta <strong>{String(item.detail.tool)}</strong> con estos datos:</p>
      <pre className="code">{JSON.stringify(item.detail.input, null, 2)}</pre>
      {error && <ErrorBox message={error} />}
      <div className="actions">
        <button className="btn btn-primary" disabled={busy} onClick={() => resolve(true)}>
          Permitir
        </button>
        <button className="btn" disabled={busy} onClick={() => resolve(false)}>
          Denegar
        </button>
      </div>
    </>
  );
}

function Approval({ item, now }: { item: InboxItem; now: number }) {
  const original = String(item.detail.output ?? "");
  const [text, setText] = useState(original);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const send = async (decision: "approve" | "reject") => {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/inbox/${item.id}/resolve`, {
        method: "POST",
        body: {
          decision,
          note: note || undefined,
          edited_output: decision === "approve" && text !== original ? text : undefined,
        },
      });
      refreshInbox();
    } catch (e) {
      setError(errorMessage(e));
      setBusy(false);
    }
  };
  return (
    <>
      <Head item={item} now={now} />
      <p className="small">
        Workflow <strong>{String(item.detail.workflow)}</strong>, paso {String(item.detail.step)}. Resultado del paso anterior (puedes editarlo antes de continuar):
      </p>
      <label className="field block">
        <span className="sr-only">Resultado del paso anterior</span>
        <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} />
      </label>
      <label className="field block">
        <span className="small">Nota (opcional; al rechazar queda registrada)</span>
        <input value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
      </label>
      {error && <ErrorBox message={error} />}
      <div className="actions">
        <button className="btn btn-primary" disabled={busy} onClick={() => send("approve")}>
          {text !== original ? "Aprobar con mis cambios" : "Aprobar y continuar"}
        </button>
        <button className="btn btn-danger" disabled={busy} onClick={() => send("reject")}>
          Rechazar y detener
        </button>
      </div>
    </>
  );
}
