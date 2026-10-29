# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/). Versionado [SemVer](https://semver.org/lang/es/).

## [0.1.0-beta.1] - 2026-10-29

Primera beta jugable.

### Añadido
- **Dex:** colección numerada de tus agentes y skills (usuario, proyecto y plugins), con filtros y siluetas de lo que aún no tienes del Glosario.
- **Sala en vivo:** personajes animados según estado (trabajando, entrenando, descansando, tiempo libre, esperando, error). Los hooks del plugin reportan subagentes de Claude Code.
- **Ficha de agente:** resumen, estadísticas reales, instrucciones en solo lectura, previsualización de animaciones.
- **Chat interactivo** con streaming y tarjetas de permiso; **tareas sin supervisión** con permisos de solo lectura o «preguntar», y límites de turnos y presupuesto obligatorios.
- **Bandeja:** permisos y aprobaciones de workflow pendientes; nada vence ni se aprueba solo.
- **Workflows lineales** con pasos de agente y decisiones humanas (aprobar, editar y continuar, rechazar).
- **Glosario** con 12 entradas fijadas a un commit, vista previa de archivos, verificación de integridad, captura y liberación.
- **Seguridad local:** código de arranque, validación de Host y Origin, CSP.
- Comando `/agent-dex:abrir` y marketplace de un plugin.

### Limitaciones conocidas
- Workflows solo lineales; lo que estaba en curso al cerrar la app queda «interrumpido».
- Gimnasio, Estudio de imagen, Creador guiado y exportación a Codex y Copilot siguen en diseño.
- Primera instalación de unos 300 MB (incluye el SDK de Claude Code).
- Probado en Windows; macOS y Linux solo en integración continua.
