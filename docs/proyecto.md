# Agent Dex — descripción del proyecto y funcionalidades

> Documento maestro. Reemplaza a `features.md`. Estado: diseño (nada construido).

## 1. Qué es

Agent Dex es un **plugin de Claude Code** que abre una **aplicación web local** para coleccionar, crear, entrenar, hacer hablar y poner a trabajar agentes de IA, solos o encadenados en **workflows**. Cada agente tiene una ficha con personaje animado, al estilo de una enciclopedia de criaturas coleccionables (numeración, siluetas de lo que aún no tienes, estadísticas, evolución), **sin temática Pokémon: solo el concepto**.

Prioridad de clientes: **Claude Code primero**; después Codex y GitHub Copilot, mediante adaptadores sobre sus carpetas (`.claude`, `.codex`, `.github`).

## 2. Cómo se usa (flujo de punta a punta)

1. Instalas el plugin en Claude Code.
2. Escribes `/agent-dex:abrir`. Se inicia el servicio local y se abre el navegador.
3. Ves tu **Dex**: los agentes y skills que ya tienes, con su estado en vivo.
4. Capturas nuevos desde el **Glosario**, o escribes una idea y el **Creador** te guía.
5. Generas la imagen y animaciones de tu agente con **tus propios tokens** de un proveedor de imágenes.
6. Lo entrenas en el **Gimnasio**, hablas con él, o lo encadenas con otros en un **Workflow** con puntos donde decides tú.
7. Desde la **Bandeja** ves qué está esperando por ti.

No hay login ni cuentas: todo corre en tu ordenador sobre tus carpetas.

## 3. Funcionalidades

Cada una indica **qué hace**, **cómo se ve/usa**, **reglas** y **criterios de aceptación (CA)**.

### F1. Dex (tu colección)

**Qué hace:** muestra todos tus agentes y skills como una colección numerada.

- Cuadrícula de tarjetas con sprite, nombre, número de registro, tipo (agente/skill/workflow), cliente(s) donde vive.
- Las entradas del Glosario que no tienes aparecen como **silueta** (con un "?"), invitando a capturarlas.
- Búsqueda, filtros (tipo, cliente, estado, categoría, "con entrenamiento") y orden (número, nivel, actividad reciente).
- Contador de progreso: "Tienes 14 de 60 entradas del Glosario".
- Descubrimiento automático leyendo `~/.claude/agents`, `~/.claude/skills`, plugins instalados y `.claude/` del proyecto abierto (y equivalentes de otros clientes).

**Reglas:** solo lectura salvo acciones explícitas; si un archivo no se puede interpretar, aparece con aviso, nunca se oculta.
**CA:** un agente creado o instalado fuera de la app aparece en menos de 5 s; un archivo inválido muestra su error.

### F2. Ficha de agente

**Qué hace:** página de detalle de un agente.

- Retrato grande animado (estado actual) y selector para previsualizar los demás estados.
- Datos: descripción, instrucciones (lectura y edición), herramientas permitidas, modelo, skills asignadas, origen (propio o capturado con su commit).
- **Estadísticas** derivadas de uso real: tareas hechas, tasa de éxito, nivel (por entrenamiento), última actividad. Nada inventado: si no hay datos se muestra "sin datos".
- **Versiones** (la "evolución"): cada cambio guardado de instrucciones/memoria es una versión; se compara y se revierte.
- Pestañas: Resumen · Chat · Entrenamiento · Memoria · Historial · Exportar.

**CA:** editar instrucciones guarda una versión y se puede volver atrás; las estadísticas coinciden con el historial registrado.

### F3. Estados y animaciones

Cada agente muestra una animación según lo que hace:

| Estado | Cuándo | Ejemplo visual |
|---|---|---|
| **Trabajando** | Ejecuta una tarea o workflow | Escribe, mueve papeles |
| **Entrenando** | Está en una sesión del Gimnasio | Hace ejercicio, repite movimientos |
| **Descansando** | Sin tareas por un rato | Duerme o se sienta |
| **Tiempo libre** | Inactivo; hace "lo suyo" | Lee, dibuja, estira; según su personalidad |
| **Esperando** (extra) | Detenido por una acción humana | Levanta la mano, signo de interrogación |
| **Error** (extra) | Falló una tarea | Gesto de confusión |

- Cada animación es una **hoja de sprites** (secuencia de cuadros) por estado.
- Si un agente no tiene animación propia, usa la de su arquetipo por defecto incluida en el plugin.
- La personalidad (campo de la ficha) elige qué hace en tiempo libre.
- Respeta "reducir movimiento" del sistema: muestra un cuadro fijo.

**CA:** el estado en pantalla coincide con el estado real en menos de 2 s; con "reducir movimiento" no hay animación.

### F4. Sala (actividad en vivo)

**Qué hace:** vista tipo "sala común" donde ves a todos tus agentes a la vez con su animación.

- Agrupados por estado; los **Esperando** destacan arriba con un aviso.
- Clic en un agente abre su ficha o su chat.
- Filtro "solo los que requieren mi atención".
- La actividad llega por eventos en tiempo real (hooks de Claude Code + ejecuciones lanzadas desde la app).

**CA:** un subagente iniciado desde Claude Code aparece como "Trabajando" y vuelve a su estado previo al terminar.

### F5. Hablar con los agentes (chat)

**Qué hace:** conversación directa con un agente desde su ficha.

- Mensajes en streaming, con las herramientas que usa mostradas como pasos colapsables.
- Cuando el agente pide permiso para una acción (editar un archivo, ejecutar un comando), aparece una tarjeta **Permitir / Denegar** en el chat.
- Historial por agente; se puede reanudar una conversación.
- Adjuntar archivos o carpetas de contexto.

**Reglas:** el chat usa tu propia sesión de Claude Code; no se envía nada a servicios de Agent Dex.
**CA:** responder y cancelar a mitad de respuesta funcionan; ninguna acción con efectos se ejecuta sin la política de permisos elegida.

### F6. Modo interactivo y no interactivo

| | Interactivo | No interactivo |
|---|---|---|
| Cómo | Conversación en vivo, tú guías | Describes la tarea, el agente trabaja solo |
| Pide permisos | Sí, en el chat | No; solo usa lo permitido de antemano |
| Resultado | En el chat | Informe final en el historial + aviso |
| Límites | Los de tu sesión | Presupuesto, tiempo y pasos máximos obligatorios |

- Una tarea no interactiva que necesita una decisión humana **se detiene en "Esperando"** en lugar de adivinar.
- Cualquier tarea no interactiva puede repetirse programada (fase posterior).

**CA:** una tarea no interactiva respeta sus límites y deja un registro completo; al exceder un límite se detiene y lo explica.

### F7. Glosario y captura

**Qué hace:** catálogo curado de agentes y skills publicados en GitHub.

- Tarjetas con descripción, licencia, actividad del repo, clientes compatibles y resultado de revisión de seguridad.
- Filtros por categoría, tipo, cliente y "no lo tengo".
- **Capturar:** muestra exactamente qué archivos se escribirán y dónde; pide confirmación; instala; registra origen y commit.
- **Liberar:** desinstala lo capturado.
- Detalle en `catalog.md`.

**CA:** nada se escribe antes de confirmar; capturar y liberar deja el sistema como estaba.

### F8. Creador guiado

**Qué hace:** conviertes una idea en un agente.

1. Escribes la idea en una frase.
2. El agente guía (`dex-guide`) hace **una pregunta a la vez** (máximo 8): objetivo, entradas, salidas, límites, tono, herramientas.
3. Propone: nombre, descripción, instrucciones, herramientas, skills sugeridas (F9) y una tarea de prueba.
4. Ves el resultado en vista previa, lo editas y apruebas; solo entonces se escribe.
5. Opcional: sigues a F13 para darle imagen y animaciones.

**CA:** produce un agente válido; nada se escribe sin aprobación.

### F9. Buscador de skills

**Qué hace:** encuentra skills para tu idea o agente.

- Usa la skill `find-skills` si está instalada; si no, ofrece capturarla.
- Cruza resultados con el Glosario y con skills que ya tienes.
- Cada sugerencia explica **por qué aplica** y muestra licencia y revisión.
- Asignar una skill a un agente es un cambio con vista previa.

**CA:** ninguna skill se instala ni se asigna sin confirmar.

### F10. Gimnasio

Resumen aquí; diseño completo en `gym.md`.

- Eliges agente, contexto, skills, una **tarea repetible**, un criterio de puntuación y un número de rondas.
- Cada ronda: ejecutar → puntuar (evaluador independiente) → proponer lección → aceptar solo si mejora → guardar en memoria.
- Verás la curva de nota, las lecciones aceptadas y rechazadas, y la comparación "inicio vs ahora".
- El agente aparece **Entrenando** con su animación durante la sesión.
- Presupuesto y tope de rondas obligatorios; revertir a cualquier ronda.

**CA:** una lección solo se guarda si mejora en una tarea de control; se muestra el coste antes de empezar.

### F11. Workflows de agentes

**Qué hace:** encadena agentes que se pasan el trabajo hasta cumplir un objetivo.

- **Editor visual** de grafo: nodos y flechas.
- Tipos de nodo:
  - **Agente:** hace una parte y entrega un resultado.
  - **Humano:** aprobar/rechazar, aportar un dato o editar la salida (F12).
  - **Condición:** decide el camino según el resultado.
  - **Paralelo / unión:** varios agentes a la vez y luego se combinan.
  - **Inicio / Fin:** con el objetivo y el criterio de "terminado".
- **Traspaso:** lo que un agente entrega al siguiente es un documento (texto o archivos) con formato definido; se ve entre nodos.
- **Ejecución:** estados por nodo (pendiente, trabajando, esperando humano, hecho, fallido) con los personajes animados sobre el grafo.
- **Protecciones:** máximo de pasos, presupuesto, tiempo y detección de bucles; al excederlos se detiene en "Esperando".
- Un workflow es un archivo (`workflow.yaml`) portable y versionado.
- Plantillas de inicio: Investigar → Redactar → Revisar; Código → Pruebas → Revisión.

**CA:** un workflow de 3 agentes con una aprobación humana se ejecuta, se detiene en la aprobación, continúa tras aprobar y deja el historial completo; se puede reanudar si se cierra la app a mitad.

### F12. Humano en el circuito y Bandeja

**Qué hace:** asegura que las decisiones importantes las tomas tú.

- Tipos de pausa: **aprobar/rechazar**, **aportar información**, **editar la salida**, **permiso de herramienta**, **límite excedido**.
- **Bandeja de pendientes:** lista de todo lo detenido, con el agente, el workflow, qué se necesita y desde cuándo.
- Acciones en la propia tarjeta: aprobar, rechazar con motivo, editar y continuar.
- Avisos: contador en la barra, notificación de escritorio opcional.
- Una pausa no vence sola ni se aprueba sola.

**CA:** todo workflow detenido aparece en la Bandeja y se puede resolver desde ahí; reanuda desde el punto exacto.

### F13. Estudio de imagen (con tus tokens)

**Qué hace:** genera el retrato y las animaciones del agente con **tu propia clave** de un proveedor de imágenes.

- **Prompts prediseñados** (`prompts-imagen.md`): estilo base, retrato, hoja de animación por estado, variaciones y arquetipos.
- Tú rellenas pocos datos (rol, personalidad, colores, accesorio); la app compone el prompt final y te lo muestra antes de enviarlo.
- Muestra el **coste estimado** y pide confirmación antes de cada generación.
- Genera primero el personaje base; las animaciones usan esa imagen como referencia para mantener coherencia.
- Procesado local: recorte de cuadros, fondo transparente, vista previa de la animación y ajuste de velocidad.
- Puedes **subir tu propia imagen** o usar el arquetipo incluido en lugar de generar.
- Tus claves se guardan en el almacén seguro del sistema y **solo se envían al proveedor elegido**; el proyecto no usa ni ve las claves de nadie.

**CA:** sin clave configurada, todo lo demás funciona con arquetipos; ninguna generación se lanza sin mostrar coste y confirmar.

### F14. Clientes y exportación

- Adaptadores por cliente: **Claude Code** (prioritario), Codex, Copilot (ver `compatibility.md`).
- Exportar un agente a otro cliente con **informe de pérdidas**.
- Importar desde repo de GitHub o paquete `.agentdex`.

**CA:** el informe lista lo conservado y lo perdido en cada destino.

### F15. Compartir

- Empaquetar un agente (instrucciones, skills, memoria curada, imagen y animaciones) para publicar en GitHub.
- Escaneo previo de secretos y rutas personales; nunca incluye historiales de chat ni claves.

**CA:** el paquete generado pasa el escaneo y se importa limpio en otra máquina.

### F16. Ajustes

- Rutas de los clientes detectadas (editables).
- Claves de proveedores de imagen (almacén seguro) y presupuestos por defecto.
- Política de permisos por defecto para tareas no interactivas.
- Tema, reducir movimiento, idioma de la interfaz (español primero).
- "Acerca de": versión y estado de cada función (construida / en diseño).

## 4. Fuera de alcance (por ahora)

Cuentas y sincronización en la nube · reentrenar modelos · mercado de pago · ejecutar agentes de terceros sin confirmar · gestión de claves de modelos de lenguaje (se usa la sesión de cada cliente).

## 5. Glosario de términos

| Término | Significado |
|---|---|
| Dex | La colección y la app |
| Ficha | Página de detalle de un agente |
| Captura | Instalar una entrada del Glosario |
| Liberar | Desinstalar una captura |
| Versión | Estado guardado de un agente (su "evolución") |
| Ronda | Una iteración del Gimnasio |
| Bandeja | Lista de acciones humanas pendientes |
| Traspaso | Entrega de resultados entre nodos de un workflow |
