# Dependencias (revisión de licencias y riesgos)

Revisadas el 2026-10-29. Regla: ninguna dependencia nueva sin revisar licencia, scripts de instalación y avisos conocidos; en npm siempre `--ignore-scripts`.

## API (Python)

| Paquete | Licencia | Uso | Notas |
|---|---|---|---|
| `claude-agent-sdk` | MIT | Control de Claude Code (ADR-002) | Trae el binario de Claude Code (≈ 297 MB). Arrastra `anyio`, `jsonschema`, `mcp` |
| `fastapi` | MIT | API HTTP y WebSocket | |
| `uvicorn` | BSD-3-Clause | Servidor | |
| `websockets` | BSD-3-Clause | WebSocket de uvicorn | Sin él el servidor rechaza las conexiones en vivo (cubierto por `test_live_server.py`) |
| `pyyaml` | MIT | Lectura de frontmatter con `safe_load` | Nunca `load` |
| Desarrollo: `pytest`, `pytest-asyncio`, `httpx`, `ruff` | MIT / Apache-2.0 | Pruebas y estilo | No se instalan para usuarios |

## Interfaz (npm)

| Paquete | Licencia | Notas |
|---|---|---|
| `react`, `react-dom` | MIT | Versiones fijadas |
| `vite`, `@vitejs/plugin-react`, `typescript`, `vitest` | MIT / Apache-2.0 | Solo desarrollo; el resultado compilado va dentro del paquete Python |

`npm audit --omit=dev`: 0 vulnerabilidades (2026-10-29). Sin fuentes ni imágenes de terceros: los personajes se dibujan en código (`web/src/sprite-data.ts`) y son originales de este proyecto.

## Contenido del Glosario

Cada entrada enlaza a un repositorio público con su propia licencia, fijado a un commit y verificado por hash de archivo. Agent Dex no redistribuye ese contenido: lo descarga en el equipo de la persona al capturar. Fuentes actuales: `anthropics/skills` (Apache-2.0 por skill) y `wshobson/agents` (MIT).
