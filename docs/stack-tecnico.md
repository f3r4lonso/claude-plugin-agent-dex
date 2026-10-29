# Stack técnico y despliegue

> Versiones concretas: se fijan y verifican en la Fase 1 (ADR-001). Aquí van las decisiones y su razón. "Por verificar" = comprobar documentación vigente antes de usar.

## 1. Resumen de decisiones

| Capa | Decisión | Razón |
|---|---|---|
| UI | React + TypeScript + Vite (SPA) | Pedido; reutiliza el prototipo `agent-dex` |
| API | Python 3.12+, FastAPI + Uvicorn | Pedido; tipado, WebSocket/SSE, OpenAPI automática |
| Contratos | Pydantic v2 → OpenAPI → tipos TypeScript generados | Una sola fuente de verdad |
| Datos | SQLite (archivo local) + archivos en disco | Sin servidor; portable |
| Tiempo real | WebSocket (eventos) | Estados y chat en vivo |
| Ejecución de agentes | Claude Agent SDK de Python (interactivo) y `claude -p` (no interactivo), por verificar | Usa la sesión y permisos del usuario |
| Distribución | Paquete Python en PyPI, ejecutado con `uvx` | Una línea, sin instalar nada más que `uv` |
| Plugin | Carpeta de plugin de Claude Code con skills/comandos y hooks | Distribución por marketplace de GitHub |

## 2. Estructura del repositorio (monorepo)

```text
claude-plugin-agent-dex/
  .claude-plugin/          plugin.json, marketplace.json
  skills/                  abrir, capturar, crear, entrenar… (comandos del plugin)
  agents/                  dex-guide, dex-trainer, dex-scout, dex-evaluator
  hooks/                   hooks.json (reportan actividad al servicio local)
  api/                     paquete Python "agent_dex"
    src/agent_dex/
      main.py              app FastAPI y arranque
      routes/              dex, glossary, agents, chat, runs, workflows, gym, studio, settings
      core/                modelos, esquemas, configuración, seguridad local
      adapters/            claude.py (prioritario), codex.py, copilot.py
      engine/              ejecutor de agentes, motor de workflows, gimnasio
      studio/              proveedores de imagen, procesado de sprites
      store/               SQLite y archivos
    tests/
    pyproject.toml
  web/                     SPA React
    src/ (features/, components/, lib/api, styles/)
  tools/build_catalog.py   genera el glosario curado (api/src/agent_dex/data/catalog.json)
  prompts/                 prompts de imagen prediseñados
  docs/
```

El resultado de `web/` se compila y se **incluye dentro del paquete Python** como archivos estáticos; la API los sirve. El usuario final no necesita Node.

## 3. UI (web/)

| Pieza | Elección | Notas |
|---|---|---|
| Framework | React 19 + TypeScript estricto | |
| Build | Vite | Salida estática empaquetada en el wheel |
| Enrutado | React Router | Vistas: Dex, Sala, Ficha, Glosario, Gimnasio, Workflows, Bandeja, Estudio, Ajustes |
| Datos del servidor | TanStack Query | Caché y reintentos |
| Estado en vivo | Cliente WebSocket + store ligero (Zustand) | Estados de agentes y runs |
| Editor de grafos | React Flow (`@xyflow/react`) | Workflows; licencia a revisar |
| Estilos | CSS con variables (tokens) + CSS Modules | Pixel-art; se evalúa Tailwind en ADR |
| Animación de sprites | Hojas de sprites con CSS `steps()`; canvas si hace falta | Ligero, respeta `prefers-reduced-motion` |
| Tipos de API | Generados desde OpenAPI | Evita desajustes con Python |
| Pruebas | Vitest + Testing Library; Playwright (Chrome) | Heredado |
| Accesibilidad | Objetivo WCAG 2.2 AA | Teclado completo, contraste, foco visible |
| Idioma | Español; textos en un archivo de mensajes | Preparado para i18n |

**Reutilizable del prototipo:** componente de tarjetas, fuente pixel (Press Start 2P, licencia OFL), sprites, estilos aislados, pruebas de accesibilidad.

## 4. API (api/)

| Pieza | Elección |
|---|---|
| Servidor | FastAPI + Uvicorn, escucha solo en `127.0.0.1` |
| Modelos | Pydantic v2 |
| Persistencia | SQLite con SQLAlchemy 2 + Alembic (migraciones); por decidir si basta `sqlite3` |
| Tareas largas | `asyncio` en el mismo proceso (workflows, gimnasio); cola persistente en SQLite |
| Tiempo real | WebSocket `/ws` con eventos tipados |
| Archivos | `watchfiles` para detectar cambios en carpetas de clientes |
| Imágenes | Pillow para recorte de cuadros, transparencia y vista previa |
| Claves | `keyring` (almacén del sistema) con respaldo de variable de entorno; nunca en disco en claro |
| Proveedores de imagen | Interfaz `ImageProvider` con implementaciones intercambiables (OpenAI, Google, Stability, Replicate…; por verificar) |
| Calidad | pytest, ruff, mypy/pyright estricto |
| Gestión | `uv` (entorno y bloqueo de versiones) |

### Endpoints principales (borrador)

| Área | Ejemplos |
|---|---|
| Dex | `GET /api/dex`, `GET /api/agents/{id}` |
| Glosario | `GET /api/glossary`, `POST /api/glossary/{id}/capture` (con `preview` y `confirm`) |
| Chat | `WS /ws/chat/{agent}` |
| Ejecuciones | `POST /api/runs`, `GET /api/runs/{id}`, `POST /api/runs/{id}/cancel` |
| Workflows | `GET/PUT /api/workflows/{id}`, `POST /api/workflows/{id}/run` |
| Bandeja | `GET /api/inbox`, `POST /api/inbox/{id}/resolve` |
| Gimnasio | `POST /api/gym/sessions`, `GET /api/gym/sessions/{id}/rounds` |
| Estudio | `POST /api/studio/estimate`, `POST /api/studio/generate` |
| Eventos | `WS /ws` (estado de agentes, runs, bandeja) |

### Adaptadores de cliente

Interfaz común: `discover()`, `read(id)`, `install(plan)`, `export(agent, destino)`. **Claude** completo primero; Codex y Copilot después, con formatos verificados.

### Cómo se ejecutan los agentes

- **Interactivo:** sesión mediante el SDK de Claude Code; los permisos que pide el agente se convierten en tarjetas de la UI.
- **No interactivo:** ejecución sin pantalla con límites obligatorios; si necesita decisión humana, se registra una pausa en la Bandeja.
- Los **hooks** del plugin envían a la API local los eventos de inicio/fin de subagentes para la Sala.
- Se usa la autenticación que el usuario ya tiene en su cliente; Agent Dex no almacena claves de modelos de lenguaje.

## 5. Seguridad local (sin login, pero no sin protección)

Aunque no hay cuentas, cualquier página web abierta en el navegador puede intentar hablar con `127.0.0.1`. Por eso:

1. Solo `127.0.0.1`; puerto fijo configurable.
2. **Token de arranque aleatorio** que `/agent-dex:abrir` incluye en la URL que abre; la API lo exige en cada petición y WebSocket (se guarda en memoria del navegador).
3. Validación estricta de `Host` y `Origin` (contra ataques de reenlace DNS).
4. Cabeceras de seguridad y CSP estricta; texto de recursos siempre escapado.
5. Acciones de escritura en carpetas de clientes: vista previa + confirmación; solo dentro de rutas permitidas.
6. Claves de imagen en el almacén del sistema; nunca en logs ni en paquetes compartidos.

## 6. Despliegue en los ordenadores de otras personas

### Requisitos para el usuario

- Claude Code instalado.
- `uv` instalado (un comando, funciona en Windows, macOS y Linux). Si no está, `/agent-dex:abrir` explica cómo instalarlo.
- Un navegador moderno.

### Flujo de instalación

```text
/plugin marketplace add f3r4lonso/claude-plugin-agent-dex
/plugin install agent-dex@agent-dex
/agent-dex:abrir
```

`/agent-dex:abrir` ejecuta `uvx agent-dex serve --open`: `uv` descarga la versión publicada en PyPI en un entorno aislado, arranca la API, genera el token y abre el navegador.

### Rutas y datos

| Qué | Dónde |
|---|---|
| Datos de la app (SQLite, caché, imágenes) | Carpeta de datos del usuario (`~/.agent-dex/`) |
| Agentes y skills de Claude | `~/.claude/…` y `.claude/` del proyecto (solo con confirmación para escribir) |
| Equivalentes Codex / Copilot | `~/.codex/…`, `.github/…` (fases posteriores) |

### Versionado y actualización

- Plugin y paquete PyPI comparten versión (SemVer). El plugin fija la versión mínima del paquete.
- Publicación automatizada con GitHub Actions: pruebas → build de la UI → wheel → PyPI (con publicación de confianza, sin tokens en el repo) → etiqueta de versión.
- Migraciones de la base de datos automáticas al arrancar, con copia de seguridad previa.

### Alternativas evaluadas

| Opción | Pro | Contra | Decisión |
|---|---|---|---|
| `uvx` desde PyPI | Una línea, actualizable | Requiere `uv` | **Elegida** |
| `pipx` | Conocido | Menos reproducible | Alternativa documentada |
| Ejecutable único (PyInstaller) | Sin Python/uv | Pesado, falsos positivos de antivirus | Más adelante, si hace falta |
| Docker | Aislado | No puede leer bien carpetas `.claude` del usuario | Descartada |

## 7. Pruebas y calidad

- API: pytest con contratos, adaptadores contra carpetas de ejemplo, motor de workflows con agentes simulados (sin gastar tokens).
- UI: Vitest + Playwright con la API en modo de datos de prueba.
- Prueba de instalación limpia en Windows, macOS y Linux en CI.
- Regla: ninguna prueba automática usa claves ni llama a modelos reales.

## 8. Riesgos técnicos a resolver primero

| Riesgo | Cómo se despeja (ver roadmap, Fase 1) |
|---|---|
| Control fiable de sesiones de Claude Code desde Python (permisos, streaming) | Prueba de concepto con el SDK y modo sin pantalla |
| Eventos de subagentes por hooks suficientes para la Sala | Prueba con hooks reales |
| Coherencia de personajes entre animaciones generadas | Prueba con 2 proveedores y prompts de referencia |
| Empaquetar UI dentro del wheel y servirla | Prueba de punta a punta con `uvx` |
| Formatos de Codex y Copilot | Verificación documental antes de la Fase 6 |
