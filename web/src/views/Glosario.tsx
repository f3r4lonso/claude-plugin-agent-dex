import { useEffect, useRef, useState } from "react";
import { api, errorMessage } from "../api";
import { useLive } from "../live";
import { ErrorBox, Pill, Skeleton } from "../ui";
import type { CapturePreview, GlossaryEntry } from "../types";

function reviewTone(r: GlossaryEntry["revision"]["resultado"]): "ok" | "warn" | "bad" {
  return r === "ok" ? "ok" : r === "aviso" ? "warn" : "bad";
}

export function Glosario({ focus }: { focus?: string }) {
  const [entries, setEntries] = useState<GlossaryEntry[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [q, setQ] = useState("");
  const [kind, setKind] = useState("all");
  const [onlyMissing, setOnlyMissing] = useState(false);
  const [open, setOpen] = useState<string | null>(focus ?? null);
  const bump = useLive((s) => s.dexVersion);

  const load = () => {
    api<GlossaryEntry[]>("/api/glossary")
      .then(setEntries)
      .catch((e) => setError(errorMessage(e)));
  };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(load, [bump]);

  if (error) return <ErrorBox message={error} onRetry={load} />;
  if (!entries) return <Skeleton />;
  const shown = entries.filter((e) => {
    if (kind !== "all" && e.tipo !== kind) return false;
    if (onlyMissing && e.instalada) return false;
    return !q || `${e.nombre} ${e.descripcion} ${e.categorias.join(" ")}`.toLowerCase().includes(q.toLowerCase());
  });

  return (
    <section aria-labelledby="h-glos">
      <header className="view-head">
        <div>
          <h1 id="h-glos">Glosario</h1>
          <p className="muted">Agentes y skills publicados en GitHub, revisados y fijados a un commit exacto. Capturar copia archivos a tu carpeta de Claude, siempre con vista previa y confirmación.</p>
        </div>
        <div className="toolbar">
          <label className="field"><span className="sr-only">Buscar</span><input type="search" placeholder="Buscar…" value={q} onChange={(e) => setQ(e.target.value)} /></label>
          <label className="field"><span className="sr-only">Tipo</span>
            <select value={kind} onChange={(e) => setKind(e.target.value)}>
              <option value="all">Todos</option><option value="agent">Agentes</option><option value="skill">Skills</option>
            </select>
          </label>
          <label className="check"><input type="checkbox" checked={onlyMissing} onChange={(e) => setOnlyMissing(e.target.checked)} />No lo tengo</label>
        </div>
      </header>
      <ul className="grid wide" role="list">
        {shown.map((e) => (
          <li key={e.slug} className="card">
            <div className="card-top">
              <Pill tone="info">{e.tipo === "agent" ? "agente" : "skill"}</Pill>
              {e.instalada ? <Pill tone="ok">Lo tienes</Pill> : <Pill>Sin capturar</Pill>}
            </div>
            <h3 className="card-name">{e.nombre}</h3>
            <p className="muted small clamp">{e.descripcion}</p>
            <p className="meta small">
              {e.licencia} · <Pill tone={reviewTone(e.revision.resultado)}>revisión: {e.revision.resultado}</Pill>
            </p>
            <p className="meta small">{e.categorias.join(" · ")}</p>
            <div className="actions">
              <button className="btn" onClick={() => setOpen(e.slug)}>
                {e.instalada ? "Ver detalle" : "Ver y capturar"}
              </button>
            </div>
          </li>
        ))}
      </ul>
      {shown.length === 0 && <p className="muted">Nada coincide con los filtros.</p>}
      {open && <CaptureDialog slug={open} entry={entries.find((e) => e.slug === open)} onClose={() => setOpen(null)} onChanged={load} />}
    </section>
  );
}

function CaptureDialog({ slug, entry, onClose, onChanged }: { slug: string; entry?: GlossaryEntry; onClose: () => void; onChanged: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const [preview, setPreview] = useState<CapturePreview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [agree, setAgree] = useState(false);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    ref.current?.showModal();
    api<CapturePreview>(`/api/glossary/${slug}/preview`)
      .then(setPreview)
      .catch((e) => setError(errorMessage(e)));
  }, [slug]);

  const capture = async () => {
    if (!preview) return;
    setBusy(true);
    setError(null);
    try {
      await api(`/api/glossary/${slug}/capture`, { method: "POST", body: { confirm: true, expected_commit: preview.commit } });
      setDone("Capturado. Ya aparece en tu Dex.");
      onChanged();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };
  const release = async () => {
    setBusy(true);
    setError(null);
    try {
      await api(`/api/glossary/${slug}/release`, { method: "POST" });
      setDone("Liberado: se borraron solo los archivos que Agent Dex había copiado.");
      onChanged();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setBusy(false);
    }
  };

  const attention = preview?.archivos.filter((a) => a.requiere_atencion) ?? [];
  return (
    <dialog ref={ref} className="dialog" onClose={onClose} aria-labelledby="dlg-title">
      <h2 id="dlg-title">{entry?.nombre ?? slug}</h2>
      {!preview && !error && <p aria-busy="true">Cargando vista previa…</p>}
      {error && <ErrorBox message={error} />}
      {done && <p className="note" role="status">{done}</p>}
      {preview && !done && (
        <>
          <p className="small">
            Repositorio <a href={preview.repo} target="_blank" rel="noreferrer noopener">{preview.repo.replace("https://github.com/", "")}</a> · commit <code>{preview.commit.slice(0, 10)}</code> · licencia {preview.licencia}
          </p>
          <p className="small"><Pill tone={reviewTone(preview.revision.resultado)}>revisión: {preview.revision.resultado}</Pill> {preview.revision.notas}</p>
          <h3>Archivos que se escribirán ({preview.archivos.length}, {(preview.total_bytes / 1024).toFixed(1)} KB)</h3>
          <ul className="files">
            {preview.archivos.map((a) => (
              <li key={a.destino}>
                <code>{a.destino}</code> {a.requiere_atencion && <Pill tone="warn">contiene código ejecutable</Pill>}
              </li>
            ))}
          </ul>
          {attention.length > 0 && (
            <p className="note note-warn">
              Esta entrada trae scripts. Agent Dex no los ejecuta, pero Claude podría hacerlo si se lo pides. Revísalos en GitHub antes de usarlos.
            </p>
          )}
          {preview.conflictos.length > 0 ? (
            <p className="note note-warn">Ya existe algo en el destino; no se sobrescribe nada. {entry?.capturada_por_dex ? "Puedes liberarlo primero." : "Elimínalo tú si quieres reemplazarlo."}</p>
          ) : (
            <label className="check">
              <input type="checkbox" checked={agree} onChange={(e) => setAgree(e.target.checked)} />
              Entiendo que se copiarán estos archivos a mi carpeta de Claude.
            </label>
          )}
        </>
      )}
      <div className="actions">
        {preview && !done && preview.conflictos.length === 0 && (
          <button className="btn btn-primary" disabled={!agree || busy} onClick={capture}>Capturar</button>
        )}
        {entry?.capturada_por_dex && !done && (
          <button className="btn btn-danger" disabled={busy} onClick={release}>Liberar (desinstalar)</button>
        )}
        <button className="btn" onClick={() => ref.current?.close()}>Cerrar</button>
      </div>
    </dialog>
  );
}
