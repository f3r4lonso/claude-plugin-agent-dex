# ADR-002: Controlar Claude Code desde Python con el Claude Agent SDK

- **Estado:** aceptada (2026-10-29)
- **Cierra:** tarea 1.1 de la Fase 1 (`docs/roadmap.md`)
- **Prueba:** `spikes/1.1-claude-control/spike.py`

## Pregunta

¿Puede la API de Python hacer chat y tareas con Claude Code mostrando los permisos en la interfaz, con streaming, límites de gasto y cancelación?

## Decisión

Usar el paquete oficial `claude-agent-sdk` (MIT, de Anthropic), versión fijada en `>=0.2.174,<0.3`. Cada chat o tarea es una sesión `ClaudeSDKClient` con:

- `can_use_tool`: callback que convierte cada permiso en un pendiente de la Bandeja y espera, sin tiempo máximo, la decisión de una persona.
- `allowed_tools=["Read","Glob","Grep"]` para lectura sin preguntar; todo lo demás pasa por el callback.
- `max_turns` y `max_budget_usd` obligatorios, con topes del servidor (50 turnos, 5 $ por sesión).
- `include_partial_messages` en chats para mostrar texto en vivo.
- `setting_sources=["user","project"]` para que el agente vea las skills y configuración de la persona.

## Resultados de la prueba (modelo `haiku`, coste total ≈ 0,01 $)

| Escenario | Resultado |
|---|---|
| Permiso concedido | El callback se invocó con la herramienta y sus datos; el archivo se creó |
| Permiso denegado | El agente recibió el motivo; el archivo no se creó; `permission_denials=1` |
| Tarea sin supervisión de solo lectura | La herramienta no permitida se denegó al instante, sin quedarse esperando |
| Streaming | 24 a 44 eventos parciales por respuesta |
| Cancelar a mitad | `interrupt()` terminó la respuesta con `terminal_reason=aborted_streaming` |
| Coste y turnos | `ResultMessage` trae `total_cost_usd` y `num_turns` |

## Consecuencias

- **Positivas:** una sola vía soportada oficialmente; permisos, cancelación y límites sin reimplementar el protocolo.
- **Peso:** el paquete trae el binario de Claude Code (≈ 297 MB en Windows). La primera instalación descarga eso; se avisa en el README y en `/agent-dex:abrir`.
- **Acoplamiento a versión:** el SDK incluye una versión concreta del CLI. Se fija el rango del SDK y se prueba al subirlo.
- **Autenticación:** se usa la sesión que la persona ya tiene en Claude Code; Agent Dex no guarda claves de modelos.
- **Por explorar (tarea 1.2):** el SDK expone mensajes de progreso de subagentes (`TaskStartedMessage` y similares) que podrían complementar los hooks para la Sala.

## Alternativas descartadas

- Reimplementar el protocolo de `claude -p --output-format stream-json`: frágil y sin soporte.
- Terminal incrustado: no permite tarjetas de permiso ni límites estructurados.
