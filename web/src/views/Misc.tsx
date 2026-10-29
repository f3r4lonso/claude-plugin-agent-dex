import { useEffect, useState } from "react";
import { api, errorMessage } from "../api";
import { ErrorBox, Pill, Skeleton } from "../ui";
import type { Settings } from "../types";

const DOCS = "https://github.com/f3r4lonso/claude-plugin-agent-dex/blob/main/docs";

export const PLANNED: Record<string, { title: string; text: string; doc: string }> = {
  gimnasio: {
    title: "Gimnasio",
    text: "Entrenar un agente con tareas repetidas, un evaluador independiente y una memoria de lecciones que solo se guardan si mejoran el resultado.",
    doc: "gym.md",
  },
  estudio: {
    title: "Estudio de imagen",
    text: "Generar el personaje y las animaciones de tu agente con prompts prediseñados y tus propias claves de proveedor, mostrando el coste antes de cada generación.",
    doc: "prompts-imagen.md",
  },
  creador: {
    title: "Creador guiado",
    text: "Escribes una idea y un agente te entrevista (una pregunta a la vez) hasta crear tu agente con las skills que necesita.",
    doc: "proyecto.md",
  },
};

export function Planned({ id }: { id: string }) {
  const p = PLANNED[id];
  if (!p) return null;
  return (
    <section aria-labelledby="h-plan">
      <header className="view-head">
        <div>
          <h1 id="h-plan">{p.title} <Pill tone="neutral">En diseño</Pill></h1>
          <p className="muted">Todavía no está construido en esta beta.</p>
        </div>
      </header>
      <div className="panel">
        <p>{p.text}</p>
        <p>
          <a href={`${DOCS}/${p.doc}`} target="_blank" rel="noreferrer noopener">Leer el diseño en GitHub</a>
        </p>
      </div>
    </section>
  );
}

export function Ajustes() {
  const [s, setS] = useState<Settings | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    api<Settings>("/api/settings").then(setS).catch((e) => setError(errorMessage(e)));
  }, []);
  if (error) return <ErrorBox message={error} />;
  if (!s) return <Skeleton count={1} />;
  const tone = { disponible: "ok", beta: "warn", "en diseño": "neutral" } as const;
  return (
    <section aria-labelledby="h-set">
      <header className="view-head"><h1 id="h-set">Ajustes</h1></header>
      <div className="stack">
        <div className="panel">
          <h2>Tu entorno</h2>
          <dl className="stats wide">
            <div><dt>Versión</dt><dd>{s.version}</dd></div>
            <div><dt>Carpeta de Claude</dt><dd className="code-inline">{s.claude_home} {s.claude_home_exists ? "" : "(no existe)"}</dd></div>
            <div><dt>Proyecto actual</dt><dd className="code-inline">{s.project_dir}</dd></div>
            <div><dt>Datos de Agent Dex</dt><dd className="code-inline">{s.data_dir}</dd></div>
            <div><dt>Claude Code en PATH</dt><dd className="code-inline">{s.claude_cli ?? "no encontrado (se usa el incluido en el SDK)"}</dd></div>
            {s.model_override && <div><dt>Modelo forzado</dt><dd>{s.model_override}</dd></div>}
          </dl>
        </div>
        <div className="panel">
          <h2>Estado de las funciones</h2>
          <table className="table">
            <thead><tr><th>Función</th><th>Estado</th></tr></thead>
            <tbody>
              {s.features.map((f) => (
                <tr key={f.id}><td>{f.nombre}</td><td><Pill tone={tone[f.estado]}>{f.estado}</Pill></td></tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h2>Privacidad</h2>
          <p>Todo corre en tu ordenador. Agent Dex no tiene cuentas ni envía datos a ningún servidor propio. Solo accede a GitHub cuando capturas una entrada del Glosario. Los chats y tareas usan tu propia sesión de Claude Code.</p>
        </div>
      </div>
    </section>
  );
}
