# Ficha para la tienda de plugins de Claude

Material listo para enviar el plugin al directorio de plugins. **El envío lo hace la persona propietaria** desde su cuenta (el validador de Claude Code menciona un portal de desarrolladores); este documento solo prepara el contenido.

## Estado de preparación (2026-10-29)

| Requisito | Estado |
|---|---|
| `claude plugin validate .` | Pasa. Un aviso informativo: `CLAUDE.md` en la raíz no se carga como contexto (es para quienes contribuyen al repositorio) |
| Comprobaciones del directorio de plugins | Sin hallazgos (icono incluido) |
| Instalación limpia desde GitHub (`marketplace add` + `install`) | Verificada en una configuración aislada |
| Licencia | MIT |
| CI en Linux, macOS y Windows | Verde |
| Política de seguridad y reporte de vulnerabilidades | `SECURITY.md` |
| Icono | `.claude-plugin/icon.png` (1024 × 1024) |

## Ficha

**Nombre:** Agent Dex

**Descripción corta (≤ 120 caracteres):** Colecciona y pon a trabajar tus agentes y skills desde una interfaz web local, con permisos y workflows.

**Descripción larga:**
Agent Dex abre una interfaz web local donde ves tus agentes y skills de Claude Code como una colección viva: personajes animados que muestran si trabajan, descansan o esperan por ti. Habla con cualquier agente, dale tareas sin supervisión con límites de turnos y presupuesto, encadena agentes en workflows con pausas de aprobación humana y captura agentes y skills de un glosario revisado de GitHub (fijado a commits y verificado por hash). Todo corre en tu ordenador: sin cuentas ni telemetría.

**Categoría sugerida:** Productividad / Herramientas para desarrolladores

**Palabras clave:** agents, skills, workflows, catalog, claude-code

**Comando principal:** `/agent-dex:abrir`

**Capturas:** `docs/img/dex.jpg`, `docs/img/sala.jpg`, `docs/img/glosario.jpg`

**Enlaces:** repositorio https://github.com/f3r4lonso/claude-plugin-agent-dex · incidencias https://github.com/f3r4lonso/claude-plugin-agent-dex/issues · seguridad `SECURITY.md`

## Divulgación para revisión (qué hace y qué toca)

| Tema | Detalle |
|---|---|
| Componentes del plugin | 1 skill de usuario (`/agent-dex:abrir`, sin invocación automática) y 2 hooks (`SubagentStart`, `SubagentStop`) |
| Qué hacen los hooks | Envían por `curl`, a `127.0.0.1:8771`, el evento JSON del subagente (nombre e identificador) para animar la Sala. Si el servicio no está activo, fallan en silencio |
| Qué ejecuta `/agent-dex:abrir` | Inicia el servicio local con `uvx` desde este repositorio fijado a una etiqueta; no instala `uv` por su cuenta |
| Red saliente | Solo a GitHub, cuando la persona captura una entrada del Glosario. Sin telemetría |
| Lectura de archivos | `~/.claude` y `.claude/` del proyecto (agentes, skills, plugins instalados) para mostrarlos |
| Escritura de archivos | Solo al capturar o liberar una entrada del Glosario, con vista previa y confirmación; nunca sobrescribe; solo borra lo que copió. Datos propios en `~/.agent-dex/` |
| Credenciales | No lee ni guarda claves. Los chats usan la sesión de Claude Code de la persona |
| Superficie local | Solo `127.0.0.1`, código de arranque aleatorio, validación de Host y Origin, CSP |

## Cómo probarlo (para revisión)

1. `/plugin marketplace add f3r4lonso/claude-plugin-agent-dex` y `/plugin install agent-dex@agent-dex`.
2. Con `uv` instalado, `/agent-dex:abrir`. Se abre el navegador con la Dex.
3. Abrir un agente → pestaña **Chat** → pedirle crear un archivo: aparece una tarjeta de permiso; **Denegar** no crea nada.
4. **Glosario** → *Ver y capturar* → revisar los archivos que se escribirían → confirmar → **Liberar** deja todo como estaba.
5. Opcional: crear un workflow de un agente y una decisión humana; aparece en la **Bandeja**.

## Antes de enviar (lo que solo puede hacer la persona propietaria)

- [ ] Enviar desde la cuenta propietaria al portal/proceso de envío vigente.
- [ ] Confirmar la categoría y el texto final.
- [ ] Decidir si se publica como beta o se espera a la `0.1.0` estable (la ficha ya declara las limitaciones en `README.md`).
