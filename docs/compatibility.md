# Compatibilidad entre clientes

> Los formatos de Codex y Copilot cambian rápido. Antes de implementar cada exportador, verificar la documentación oficial vigente y anotar la fecha aquí.

## Mapa de conceptos (a verificar)

| Concepto | Claude Code | Codex CLI | GitHub Copilot |
|---|---|---|---|
| Instrucciones del proyecto | `CLAUDE.md` | `AGENTS.md` | `.github/copilot-instructions.md` / `AGENTS.md` |
| Agente / subagente | `agents/*.md` (frontmatter + prompt) | por verificar | `.github/agents/*.agent.md` (por verificar) |
| Skill | `skills/<n>/SKILL.md` | por verificar | por verificar |
| Distribución | Plugin + marketplace | por verificar | por verificar |

## Estrategia

- **Canónico = formato Claude** (ver `architecture.md`).
- Un **exportador por destino** convierte y genera un **informe de pérdidas**: qué campos no tienen equivalente (p. ej. herramientas, hooks, modelo).
- Lo que no se puede traducir se documenta en el archivo exportado como comentario, no se inventa.

## Destinos y entregables

| Destino | Entregable | Fase |
|---|---|---|
| Claude Code (plugin) | Carpeta con `.claude-plugin/plugin.json` | 4 |
| Claude Code (CLI) | Archivos en `~/.claude/agents` y `~/.claude/skills` | 2 |
| Codex | `AGENTS.md` + skills equivalentes | 5 |
| Copilot | Archivo de agente + instrucciones | 5 |

## Importación

`.agentdex` (zip de la carpeta canónica) o URL de repo GitHub. Se aplica el mismo flujo de revisión y confirmación de la captura.
