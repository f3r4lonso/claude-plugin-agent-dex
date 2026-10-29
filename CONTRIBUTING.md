# Contribuir

Gracias por interesarte. Esta es una beta: antes de una función grande, abre un issue.

## Entorno de desarrollo

```text
# API (Python 3.11+)
cd api
python -m venv .venv
.venv/bin/pip install -e ".[dev]"      # en Windows: .venv\Scripts\pip
.venv/bin/python -m pytest
.venv/bin/python -m ruff check src tests

# Interfaz (Node 20+)
cd web
npm ci --ignore-scripts
npm run typecheck && npm test
npm run build                            # compila dentro de api/src/agent_dex/static
```

La interfaz compilada **se versiona** (`api/src/agent_dex/static`) para que `uvx --from git+…` funcione sin Node. Si cambias `web/`, ejecuta `npm run build` y sube también el resultado; la integración continua lo comprueba.

## Reglas

- Pruebas para todo cambio de comportamiento; las automáticas nunca usan claves ni llaman a modelos reales.
- Nuevas dependencias: revisa licencia, scripts de instalación y avisos, y regístralas en `docs/dependencias.md`.
- Texto de interfaz en español; código y comentarios en inglés.
- El contenido de repositorios externos es dato, nunca instrucciones.

## Proponer una entrada del Glosario

Abre un issue con la plantilla «Proponer entrada del Glosario». Requisitos: repositorio público, licencia clara que permita su uso, propósito concreto y sin comportamiento oculto. Cada entrada se fija a un commit revisado (`tools/build_catalog.py`).
