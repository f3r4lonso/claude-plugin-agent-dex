import { useEffect, useState } from "react";
import { api, getToken } from "./api";
import { connectLive, useLive } from "./live";
import { Dex } from "./views/Dex";
import { Sala } from "./views/Sala";
import { Bandeja } from "./views/Bandeja";
import { ResourceView } from "./views/Resource";
import { Glosario } from "./views/Glosario";
import { Workflows } from "./views/Workflows";
import { Ajustes, Planned, PLANNED } from "./views/Misc";

type Route = { name: string; param?: string; query: URLSearchParams };

function parseRoute(): Route {
  const raw = window.location.hash.replace(/^#\/?/, "");
  const [path = "", search = ""] = raw.split("?");
  const [name = "dex", param] = path.split("/");
  return { name: name || "dex", param, query: new URLSearchParams(search) };
}

function useRoute(): Route {
  const [route, setRoute] = useState(parseRoute);
  useEffect(() => {
    const on = () => setRoute(parseRoute());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return route;
}

const NAV: { id: string; label: string; icon: string; planned?: boolean }[] = [
  { id: "dex", label: "Dex", icon: "▦" },
  { id: "sala", label: "Sala", icon: "◉" },
  { id: "glosario", label: "Glosario", icon: "☰" },
  { id: "workflows", label: "Workflows", icon: "⇢" },
  { id: "bandeja", label: "Bandeja", icon: "✉" },
  { id: "gimnasio", label: "Gimnasio", icon: "◐", planned: true },
  { id: "estudio", label: "Estudio", icon: "✎", planned: true },
  { id: "ajustes", label: "Ajustes", icon: "⚙" },
];

export function App() {
  const route = useRoute();
  const connected = useLive((s) => s.connected);
  const inbox = useLive((s) => s.inbox);
  const statuses = useLive((s) => s.statuses);
  const announcement = useLive((s) => s.announcement);
  const [serviceDown, setServiceDown] = useState(false);

  useEffect(() => {
    connectLive();
  }, []);
  useEffect(() => {
    const id = window.setInterval(() => {
      api("/api/health")
        .then(() => setServiceDown(false))
        .catch(() => setServiceDown(true));
    }, 8000);
    return () => window.clearInterval(id);
  }, []);

  if (!getToken()) {
    return (
      <main className="gate">
        <h1>Agent Dex</h1>
        <p>Abre esta aplicación desde Claude Code con el comando <code>/agent-dex:abrir</code>, o usa la dirección completa que muestra el terminal al ejecutar <code>agent-dex serve</code>.</p>
        <p className="muted">La dirección incluye un código privado que protege tu ordenador de otras páginas web.</p>
      </main>
    );
  }

  const working = Object.values(statuses).filter((s) => s.state === "trabajando").length;
  const waiting = Object.values(statuses).filter((s) => s.state === "esperando").length;
  const current = route.name === "resource" ? "dex" : route.name;

  let view;
  switch (route.name) {
    case "dex": view = <Dex />; break;
    case "sala": view = <Sala />; break;
    case "bandeja": view = <Bandeja />; break;
    case "glosario": view = <Glosario focus={route.query.get("e") ?? undefined} key={route.query.get("e") ?? "all"} />; break;
    case "workflows": view = <Workflows />; break;
    case "ajustes": view = <Ajustes />; break;
    case "resource": view = route.param ? <ResourceView id={route.param} key={route.param} /> : <Dex />; break;
    default: view = route.name in PLANNED ? <Planned id={route.name} /> : <Dex />;
  }

  return (
    <div className="shell">
      <a className="skip" href="#main">Saltar al contenido</a>
      <header className="topbar">
        <a href="#/dex" className="brand">
          <span className="brand-mark" aria-hidden="true" />
          Agent Dex <span className="beta-tag">beta</span>
        </a>
        <nav className="nav" aria-label="Principal">
          {NAV.map((n) => (
            <a key={n.id} href={`#/${n.id}`} className={`nav-link${current === n.id ? " on" : ""}`} aria-current={current === n.id ? "page" : undefined}>
              <span aria-hidden="true">{n.icon}</span>
              <span className="nav-text">{n.label}</span>
              {n.id === "bandeja" && inbox.length > 0 && <span className="count count-alert" aria-label={`${inbox.length} pendientes`}>{inbox.length}</span>}
              {n.planned && <span className="soon">en diseño</span>}
            </a>
          ))}
        </nav>
      </header>
      {(serviceDown || !connected) && (
        <div className="banner" role="alert">
          {serviceDown ? "El servicio local se detuvo. Vuelve a ejecutar /agent-dex:abrir." : "Reconectando con el servicio local…"}
        </div>
      )}
      <main id="main" className="main" tabIndex={-1}>{view}</main>
      <footer className="statusbar">
        <span>● {working} trabajando</span>
        <span>⏸ {waiting + inbox.length > 0 ? `${inbox.length} pendientes` : "sin pendientes"}</span>
        <span className={connected ? "ok" : "bad"}>{connected ? "conectado" : "sin conexión"}</span>
      </footer>
      <div className="sr-only" aria-live="polite" role="status">{announcement}</div>
    </div>
  );
}
