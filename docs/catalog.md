# Glosario (catálogo curado)

## Fuente

Un archivo versionado en este repo: `api/src/agent_dex/data/catalog.json` (se regenera con `tools/build_catalog.py`). Cada entrada apunta a un repositorio público de GitHub **fijado a un commit**.

```json
{
  "id": "autor/repo/ruta",
  "tipo": "agente | skill",
  "nombre": "…",
  "descripcion": "…",
  "repo": "https://github.com/autor/repo",
  "commit": "sha-exacto",
  "ruta": "agents/revisor.md",
  "licencia": "MIT",
  "clientes": ["claude", "codex", "copilot"],
  "categorias": ["código", "escritura"],
  "revision": { "fecha": "2026-10-29", "resultado": "ok | aviso | bloqueado", "notas": "…" }
}
```

## Cómo entra algo al catálogo

1. Propuesta (issue o PR con la plantilla de entrada).
2. Revisión: licencia presente y compatible, sin secretos, sin instalación con scripts, hooks o permisos amplios no declarados, repo activo.
3. Se fija el commit revisado. Actualizar a un commit nuevo exige repetir la revisión.

## Criterios de selección

- Licencia clara que permita uso y redistribución del enlace.
- Documentación mínima y propósito concreto.
- Sin comportamiento oculto (red, hooks, ejecución de comandos no explicados).

## Captura

Ver flujo en `architecture.md`. Reglas:

- Nunca se ejecuta contenido del repo capturado durante la captura; solo se copian archivos de agente/skill.
- Los archivos con scripts o hooks se marcan "requiere atención" y muestran su contenido antes de confirmar.
- Se registra origen + commit. "Liberar" borra lo copiado y el registro.

## Semilla inicial

Primera tanda: 20 a 30 entradas (agentes y skills de repos oficiales y de alta reputación), incluida `find-skills`. Lista a definir en la Fase 2 (`roadmap.md`).
