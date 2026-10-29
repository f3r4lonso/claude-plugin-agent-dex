# Hoja de ruta

Estimaciones para una persona trabajando con ayuda de IA; son orientativas y se revisan al cerrar cada fase. **Antes de escribir código de producto se cierra la Fase 1 (definición técnica).**

## Estado actual (2026-10-29)

**Beta `0.1.0-beta.1` publicada.** Se adelantó un recorte jugable de las Fases 2 a 6: plugin instalable con `uvx`, Dex y Sala en vivo, chat y tareas con permisos, Bandeja, workflows lineales y Glosario con captura. De la Fase 1 está cerrada la tarea 1.1 ([ADR-002](adr/002-control-de-claude-code-desde-python.md)) y la 1.7 en lo esencial (código de arranque, Host/Origin). Siguen abiertas 1.2 (eventos de subagentes más allá de los hooks), 1.4 (proveedores de imagen), 1.5/1.6 (esquema y `workflow.yaml` formales), 1.9 (formatos de Codex y Copilot) y 1.11 (pruebas con personas).

**Siguiente:** reanudar workflows tras reiniciar, Creador guiado, Estudio de imagen, Gimnasio, exportadores.

## Vista general

| Fase | Nombre | Duración aprox. | Salida clave |
|---|---|---|---|
| 0 | Documentación | hecha | Estos documentos |
| 1 | **Definición técnica** (pruebas de concepto y decisiones) | 1–2 semanas | ADRs aprobados; riesgos técnicos resueltos |
| 2 | Cimientos | 1–2 semanas | Plugin instalable; API + UI vacías servidas con `uvx`; CI |
| 3 | Dex y Sala | 2–3 semanas | Descubrimiento real, fichas, estados y animaciones de arquetipo |
| 4 | Glosario y captura | 2 semanas | Catálogo semilla; captura con revisión y confirmación |
| 5 | Chat y ejecución | 2–3 semanas | Chat interactivo y tareas no interactivas con límites |
| 6 | Bandeja y workflows | 3–4 semanas | Editor, motor, humano en el circuito, reanudación |
| 7 | Creador guiado y buscador de skills | 2 semanas | De idea a agente en ≤ 8 preguntas |
| 8 | Estudio de imagen | 2–3 semanas | Imagen y animaciones con claves propias |
| 9 | Gimnasio | 3 semanas | Rondas, evaluador, memoria, curva, revertir |
| 10 | Exportar (Codex, Copilot) y compartir | 2–3 semanas | Exportadores con informe de pérdidas; paquetes |
| 11 | Pulido y lanzamiento 1.0 | 2 semanas | Accesibilidad, instalación limpia en 3 sistemas, documentación |

Total orientativo: 5–7 meses. Un **v0.1 público** es posible tras la Fase 4 (Dex, Sala, Glosario).

## Fase 1 — Definición técnica (detalle)

Objetivo: eliminar incertidumbre antes de construir. Cada punto termina en un ADR corto (decisión, alternativas, razón) en `docs/adr/`.

| Nº | Tarea | Pregunta que responde | Resultado |
|---|---|---|---|
| 1.1 | Prueba: lanzar y controlar Claude Code desde Python (SDK y modo sin pantalla), con streaming y permisos | ¿Podemos hacer chat y tareas con permisos en la UI? | ADR-002 |
| 1.2 | Prueba: hooks de subagentes → API local | ¿Bastan los eventos para la Sala? | ADR-003 |
| 1.3 | Prueba: UI compilada dentro del wheel, servida por FastAPI, lanzada con `uvx` en Windows, macOS y Linux | ¿La instalación de una línea funciona? | ADR-004 |
| 1.4 | Prueba: generar personaje + 2 animaciones con 2 proveedores de imagen y recorte automático | ¿Hay coherencia suficiente? ¿Qué cuesta? | ADR-005, ajusta `prompts-imagen.md` |
| 1.5 | Esquema de datos: agente, versión, ejecución, nodo, pendiente, ronda, captura | ¿Qué se guarda y dónde? | ADR-006 |
| 1.6 | Formato `workflow.yaml` y de traspaso | ¿Cómo se describe un workflow portable? | ADR-007 |
| 1.7 | Seguridad local: token de arranque, Host/Origin, rutas permitidas | ¿Cómo evitamos que una web ajena use la API? | ADR-008 |
| 1.8 | Verificar formatos oficiales actuales de Claude (plugin, agentes, skills, hooks) | ¿Los manifiestos son válidos? | Manifiestos corregidos |
| 1.9 | Verificar formatos de Codex y Copilot | ¿Qué es exportable? | `compatibility.md` completado |
| 1.10 | Revisión de licencias y dependencias (React Flow, Pillow, etc.) | ¿Hay obstáculos de licencia? | `dependencias.md` |
| 1.11 | Prototipo de baja fidelidad de 4 pantallas + prueba con 3 personas | ¿La experiencia se entiende? | Cambios a `diseno-ui.md` |

**Criterio de salida:** los 8 ADRs aprobados, `uvx` funcionando de punta a punta con una página vacía, y la prueba de Claude Code (1.1) funcionando con permisos en pantalla. Si 1.1 o 1.3 fallan, se rediseña antes de continuar.

## Detalle de fases siguientes

### Fase 2 — Cimientos
Estructura del monorepo, `pyproject.toml` y `web/` con tipos generados desde OpenAPI, `/agent-dex:abrir`, token de arranque, CI (pruebas, build, prueba de instalación limpia), publicación automática a PyPI en rama de pruebas.
**Salida:** `/plugin install` + `/agent-dex:abrir` abre una página "Hola" servida por la API.

### Fase 3 — Dex y Sala
Adaptador Claude (lectura), descubrimiento y vigilancia de carpetas, Dex, Ficha (lectura y edición con versiones), sistema visual, sprites de arquetipo, Sala con eventos en vivo.
**Salida:** ves tus agentes reales con su estado en vivo.

### Fase 4 — Glosario y captura
`catalog/index.json` semilla (20–30 entradas, incluida `find-skills`), revisión automática, diálogo de captura, liberar.
**Salida:** capturar y liberar sin efectos secundarios. **Candidato a v0.1 público.**

### Fase 5 — Chat y ejecución
Chat con streaming, tarjetas de permiso, modo no interactivo con límites, historial.

### Fase 6 — Bandeja y workflows
Modelo de pausas, Bandeja, editor de grafo, motor con reanudación tras reinicio, plantillas, protecciones de bucle y coste.

### Fase 7 — Creador guiado y buscador de skills
`dex-guide`, integración con `find-skills`, vista previa y aprobación.

### Fase 8 — Estudio de imagen
Interfaz de proveedores, claves en almacén seguro, composición de prompts, recorte y vista previa, coste y confirmación, arquetipos incluidos.

### Fase 9 — Gimnasio
Ciclo de rondas, evaluador independiente, control contra sobreajuste, memoria y reversión (ver `gym.md`).

### Fase 10 — Exportar y compartir
Adaptadores Codex y Copilot con informe de pérdidas, paquetes `.agentdex`, escaneo de secretos.

### Fase 11 — Pulido y 1.0
Auditoría de accesibilidad con lector de pantalla, pruebas de instalación en Windows/macOS/Linux, documentación de usuario, política de seguridad, plantilla de contribución al catálogo.

## Orden de valor (si hay que recortar)

1. Dex + Sala + Glosario (v0.1)
2. Chat + Bandeja + workflows
3. Estudio de imagen
4. Gimnasio
5. Exportar a Codex/Copilot

## Riesgos y respuesta

| Riesgo | Respuesta |
|---|---|
| Claude Code no permite el control necesario desde Python | Resuelto o replanteado en Fase 1.1; alternativa: ejecutar en terminal incrustado |
| Cambios de formato en los clientes | Adaptadores aislados y pruebas con carpetas de ejemplo; verificación documental por fase |
| Animaciones generadas incoherentes | Arquetipos incluidos como respaldo; edición manual; subir imagen propia |
| Costes inesperados de los usuarios | Estimación obligatoria, topes y confirmación |
| "Entrenar" percibido como más de lo que es | UI siempre muestra métrica real y qué cambia |
| Instalación difícil en otras máquinas | Prueba temprana (1.3) y CI en 3 sistemas |
| Alcance excesivo | Orden de valor y v0.1 tras Fase 4 |

## Decisiones ya tomadas

- Licencia **MIT**.
- UI en React; API en Python (FastAPI).
- Sin login; todo local; prioridad Claude Code.
- Claves de imagen: las de cada usuario, nunca las del autor.

## Siguiente acción

Arrancar la Fase 1 con 1.1 (control de Claude Code desde Python), porque es el riesgo que más condiciona el diseño.
