# Arquitectura

Resumen de alto nivel. El detalle de tecnologías, estructura de carpetas y despliegue está en [`stack-tecnico.md`](stack-tecnico.md).

## Piezas

```text
Claude Code
 ├─ Plugin agent-dex
 │   ├─ skills/   → /agent-dex:abrir, :capturar, :crear, :entrenar, :exportar
 │   ├─ agents/   → dex-guide, dex-trainer, dex-scout, dex-evaluator
 │   └─ hooks/    → reportan actividad de subagentes a la API local
 └─ Servicio local (Python, 127.0.0.1)
     ├─ API FastAPI: Dex, Glosario, Chat, Ejecuciones, Workflows, Bandeja, Gimnasio, Estudio
     ├─ UI React compilada (archivos estáticos servidos por la API)
     ├─ Adaptadores de cliente: .claude (prioritario), .codex, .github
     └─ Almacén local: ~/.agent-dex/ (SQLite, imágenes, memorias)
```

## Reutilizado del prototipo `agent-dex`

| Pieza | Uso |
|---|---|
| Componente de tarjetas, estilos pixel-art, sprites, fuente | Base de la UI web (`web/`) |
| Modelo de seguridad (loopback, Host/Origin, CSP, código de emparejamiento) | Se conserva la idea; el código de emparejamiento pasa a ser un **token de arranque** |
| Servicio Node | **No se reutiliza**: la API pasa a Python |

## Formato canónico del agente

Carpeta con formato Claude como base más metadatos propios:

```text
mi-agente/
  agent.md            # frontmatter (name, description, tools, model) + instrucciones
  skills/             # skills que lleva consigo
  dex.json            # origen, versión, compatibilidad, personalidad, arquetipo
  sprites/            # retrato y hojas de animación por estado
  memory/
    lessons.md        # lecciones curadas (lo único que se inyecta al agente)
    rounds/           # historial del gimnasio (JSONL)
```

## Flujos principales

- **Captura:** catálogo → descarga aislada → revisión automática → vista previa de archivos → confirmación → copia + registro con commit exacto.
- **Chat / tarea:** UI → API → sesión del cliente (SDK o modo sin pantalla) → eventos por WebSocket → UI; permisos y pausas se convierten en tarjetas y en la Bandeja.
- **Workflow:** el motor recorre el grafo; cada nodo agente produce un traspaso; un nodo humano crea una pausa persistente y el motor espera; al resolverla, continúa desde ese punto aunque la app se haya reiniciado.
- **Entrenamiento:** ver `gym.md`.
- **Imagen:** prompt compuesto → confirmación de coste → proveedor con la clave del usuario → recorte local → ficha.

## Modelo de estados de un agente

`trabajando · entrenando · descansando · tiempo libre · esperando · error`. Lo determina el motor de ejecución (tareas, workflows, gimnasio) y los eventos de hooks; sin actividad durante un tiempo pasa a descansando y de ahí a tiempo libre de forma rotativa.

## Decisiones abiertas

Se resuelven en la Fase 1 del roadmap (ADRs): control de Claude Code desde Python, eventos de hooks, empaquetado con `uvx`, esquema de datos, formato `workflow.yaml`, seguridad local, proveedores de imagen.
