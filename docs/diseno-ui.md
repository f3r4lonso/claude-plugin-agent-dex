# Diseño UI / UX web

Diseño de todas las pantallas y estados. Los bocetos son esquemas de estructura (no arte final). Texto de interfaz en español. Objetivo de accesibilidad: WCAG 2.2 AA.

## 1. Principios de diseño

1. **Concepto de enciclopedia de criaturas, sin franquicia:** numeración, siluetas de lo no capturado, fichas con estadísticas, evolución por versiones. Personajes y nombres originales.
2. **Lo que necesita tu atención, primero.** Todo lo detenido se ve desde cualquier pantalla.
3. **Estado visible, siempre.** Cada agente comunica qué hace con su animación y una etiqueta de texto (la animación nunca es el único canal).
4. **Confirmar antes de escribir o gastar.** Vista previa para instalar y coste para generar.
5. **Honestidad:** lo no construido se marca "en diseño"; sin datos se dice "sin datos".
6. **Calma:** animación suave y pequeña; `prefers-reduced-motion` la detiene.

## 2. Sistema visual

| Elemento | Decisión |
|---|---|
| Estética | Pixel-art limpio sobre interfaz plana moderna (bordes de 2 px, esquinas escalonadas) |
| Tipografía | Titulares: Press Start 2P (OFL), pocos y cortos. Texto: fuente sans legible del sistema. Datos: monoespaciada |
| Color | Tokens en variables CSS; modo claro y oscuro; un color por **tipo** de entrada y otro por **estado** (siempre con icono y texto, no solo color) |
| Colores de estado | Trabajando (azul), Entrenando (naranja), Descansando (violeta suave), Tiempo libre (verde), Esperando (ámbar, destacado), Error (rojo) |
| Rejilla | Base de 8 px; tarjetas de 160×200 px; sprite 64×64 escalado ×2 o ×3 sin suavizado |
| Iconos | Conjunto único de líneas, 24 px |
| Movimiento | Sprites a 6–8 fps; transiciones de interfaz ≤ 150 ms |
| Contraste | Texto ≥ 4.5:1; elementos de interfaz ≥ 3:1 |
| Foco | Anillo visible de 3 px en todo control; navegación completa por teclado |

Tokens de ejemplo: `--color-fondo`, `--color-superficie`, `--color-texto`, `--estado-trabajando`, `--estado-esperando`, `--borde-pixel`.

## 3. Estructura general

```text
┌──────────────────────────────────────────────────────────────┐
│ ◉ Agent Dex   Dex  Sala  Glosario  Workflows  Gimnasio  Estudio │ 🔔 3  ⚙
├──────────┬───────────────────────────────────────────────────┤
│ Filtros  │                 Contenido de la vista             │
│ (según   │                                                   │
│  vista)  │                                                   │
├──────────┴───────────────────────────────────────────────────┤
│ Barra de estado: ● 2 trabajando  ◐ 1 entrenando  ⏸ 3 esperando │
└──────────────────────────────────────────────────────────────┘
```

- **🔔 Bandeja** accesible desde cualquier pantalla (contador de pendientes).
- **Barra de estado** inferior: resumen en vivo; clic filtra la Sala.
- **Móvil/estrecho:** navegación inferior con 5 destinos (Dex, Sala, Glosario, Workflows, Más); filtros en panel deslizable.

## 4. Pantallas

### 4.1 Dex (colección)

```text
 Tu Dex · 14/60 entradas                 [Buscar…] [Tipo ▾] [Cliente ▾] [Orden ▾]
 ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
 │ Nº 001 │ │ Nº 002 │ │ Nº 003 │ │ Nº 004 │
 │ [sprite]│ │ [sprite]│ │ [ ? ]  │ │ [sprite]│
 │ Revisor│ │ Escriba│ │ ?????  │ │ Mensajero│
 │ ●Trabaj│ │ ◌Descan│ │ Capturar│ │ ⏸Esperando│
 └────────┘ └────────┘ └────────┘ └────────┘
```

- Tarjeta: número, sprite animado según estado, nombre, estado (icono + texto), clientes (insignias).
- Silueta: gris con "?"; botón **Capturar** → Glosario.
- Estados de la vista: **vacía** ("Aún no tienes agentes. Captura uno o crea el tuyo"), **cargando** (esqueletos), **error** (mensaje y reintentar), **archivo inválido** (tarjeta con aviso).

### 4.2 Ficha de agente

```text
 ← Dex                                   Nº 001  Revisor de contratos
 ┌──────────────┐  Nivel 4 · ● Trabajando          [Hablar] [Entrenar] [Exportar]
 │  [sprite     │  Estados: (Trabajando)(Entrenando)(Descansando)(Libre)
 │   grande]    │  Personalidad: meticuloso
 └──────────────┘  Claude Code · v7 · origen: propio
 ── Resumen ─ Chat ─ Entrenamiento ─ Memoria ─ Historial ─ Exportar ──
 Descripción · Herramientas · Skills asignadas [+ añadir]
 Estadísticas: tareas 128 · éxito 91 % · última actividad hace 2 h
 Instrucciones  [Editar]   Versiones: v7 v6 v5 …  [Comparar] [Volver a esta]
```

- Selector de estados para previsualizar cada animación.
- Edición de instrucciones con vista de diferencias y guardado como nueva versión.

### 4.3 Sala (en vivo)

```text
 Sala                                  [Solo lo que requiere mi atención ▢]
 ⏸ ESPERANDO (2)  ─────────────────────────────────────────
   [sprite] Redactor · "Aprobar borrador"   desde hace 12 min   [Resolver]
   [sprite] Revisor  · "Permiso: ejecutar comando"             [Resolver]
 ● TRABAJANDO (3)    ◐ ENTRENANDO (1)    ☾ DESCANSANDO (4)    ☺ TIEMPO LIBRE (2)
   (escenario con los personajes animados en cada zona)
```

- Escenario con zonas por estado; los personajes se mueven a la zona al cambiar de estado.
- Vista alternativa **Lista** para lectores de pantalla y para muchos agentes.
- Cada cambio se anuncia en una región `aria-live` educada ("Redactor ahora espera tu aprobación").

### 4.4 Chat con un agente

```text
 ┌ Revisor de contratos ● ──── Modo: (Interactivo | No interactivo) ┐
 │ Tú: revisa el contrato adjunto                                   │
 │ Revisor: Leo el archivo…   ▸ Leer contrato.pdf  ▸ Buscar cláusulas│
 │ ┌ Permiso solicitado ─────────────────────────┐                  │
 │ │ Editar notas.md  [Ver cambio] [Permitir][Denegar]│              │
 │ └─────────────────────────────────────────────┘                  │
 ├──────────────────────────────────────────────────────────────────┤
 │ [📎] Escribe un mensaje…                         [Enviar][Detener]│
 └──────────────────────────────────────────────────────────────────┘
```

- Pasos de herramientas colapsables; tarjetas de permiso inline.
- **No interactivo:** el campo se convierte en "Describe la tarea" + límites (presupuesto, tiempo, pasos) obligatorios + botón **Lanzar**; al terminar, informe en el historial.

### 4.5 Glosario

```text
 Glosario                     [Buscar] [Categoría ▾] [Tipo ▾] [Cliente ▾] [No lo tengo ▢]
 ┌────────────────┐
 │ [sprite/ícono] │  Revisor de código · MIT · ★ activo · ✓ revisado
 │ Descripción…   │  Claude ✓  Codex ✓  Copilot ~
 │ [Ver] [Capturar]│
 └────────────────┘
```

**Captura (diálogo paso a paso):**
1. Detalle y resultado de revisión (✓ ok / ⚠ aviso / ⛔ bloqueado).
2. **Archivos que se escribirán** (ruta completa, tamaño); los que contienen scripts o hooks se marcan "requiere atención" y se muestran.
3. Confirmar → progreso → "Capturado: Nº 015 añadido a tu Dex" con opción de **Liberar**.

### 4.6 Creador guiado

```text
 Crear un agente
 ① Idea ② Entrevista ③ Propuesta ④ Imagen ⑤ Listo
 ┌ Guía ─────────────────────────────────────────┐
 │ ¿Qué debería producir este agente al terminar?  │
 │ [ Opciones sugeridas ] [ Escribe tu respuesta ] │
 └────────────────────────────────────────────────┘
 Progreso: pregunta 3 de ~8                 [Saltar] [Volver]
```

- Una pregunta por pantalla, con opciones sugeridas.
- **Propuesta:** vista previa editable (nombre, descripción, instrucciones, herramientas, skills sugeridas con motivo, tarea de prueba) y botón **Aprobar y crear**.
- Paso Imagen opcional → Estudio.

### 4.7 Buscador de skills

Panel lateral dentro del Creador y de la Ficha: campo con la idea → lista de resultados con "por qué aplica", licencia, revisión y **[Asignar]** (vista previa del cambio). Si falta `find-skills`: tarjeta "Captura find-skills para buscar más".

### 4.8 Gimnasio

```text
 Gimnasio
 [Nueva sesión]
 ┌ Sesión: Revisor · tarea "Contrato tipo A" · ronda 3/5 ──────────┐
 │ Nota por ronda:  ▁▂▄▆   (gráfico + tabla accesible)             │
 │ Lecciones: ✓ "Verifica fechas primero"  ✗ "Resume en 3 líneas"  │
 │ Inicio 62 → Ahora 78       Coste: 1,2 $ de 3 $                  │
 │ [Pausar] [Detener] [Fijar nueva versión] [Revertir a ronda…]    │
 └────────────────────────────────────────────────────────────────┘
```

**Asistente de nueva sesión (4 pasos):** agente → contexto y skills → tarea y criterio → rondas y presupuesto (muestra coste estimado). Durante la sesión, el personaje del agente se ve **Entrenando**.

### 4.9 Workflows

**Lista:** tarjetas con nombre, nº de nodos, estado de la última ejecución, **[Ejecutar]**, plantillas de inicio.

**Editor:**

```text
 Paleta        ┌────────┐     ┌────────┐     ┌──────────┐     ┌──────┐
 ▢ Agente      │Inicio  │ ──▶ │Investig│ ──▶ │ Humano:  │ ──▶ │Redact│ ──▶ Fin
 ▢ Humano      │objetivo│     │ [sprite]│    │ ¿Aprobar?│     │[sprite]│
 ▢ Condición   └────────┘     └────────┘     └──────────┘     └──────┘
 ▢ Paralelo
 Propiedades del nodo seleccionado: agente, instrucciones del paso, entrada, salida esperada, límites
```

- Arrastrar para crear y conectar; validación en vivo (nodos sin salida, bucles sin tope).
- Teclado: añadir, mover y conectar nodos sin ratón.

**Ejecución (misma vista, modo "en vivo"):**
- Cada nodo muestra el personaje animado con su estado; las flechas muestran el **traspaso** (clic para ver el documento).
- Nodo humano detenido: parpadeo suave en ámbar + **[Resolver]**.
- Panel inferior con registro cronológico, coste acumulado y botones Pausar / Cancelar / Reanudar.

### 4.10 Bandeja de pendientes

```text
 Bandeja · 3 pendientes                                [Todos ▾] [Más antiguos ▾]
 ⏸ Aprobar borrador — Redactor · Workflow "Informe semanal" · hace 12 min
     [Ver borrador]  [Aprobar]  [Rechazar…]  [Editar y continuar]
 ⏸ Permiso: ejecutar `pytest` — Revisor · hace 3 min   [Permitir] [Denegar]
 ⏸ Límite de presupuesto alcanzado — Investigador      [Subir límite] [Detener]
```

- Cada tarjeta explica qué ocurrió y qué pasa con cada botón.
- Resolver reanuda desde el punto exacto; rechazar pide motivo (se pasa al agente).
- Notificación de escritorio opcional (se pide permiso al activarla).

### 4.11 Estudio de imagen

```text
 Estudio · Revisor de contratos
 ① Personaje   ② Animaciones   ③ Revisar y guardar
 Arquetipo (Investigador ▾) Colores [azul petróleo + ámbar] Accesorio [lupa]
 Prompt compuesto: ┌──────────────────────────────┐ [Editar]
                   │ Original character … {rol}…   │
                   └──────────────────────────────┘
 Proveedor (OpenAI ▾)  Clave: ✓ configurada      Coste estimado ≈ 0,20 $
 [Generar personaje]   o   [Subir imagen] / [Usar arquetipo incluido]
```

- Paso 2: una tarjeta por estado con vista previa en bucle y control de velocidad; **[Generar]** o **[Reintentar]** por estado (coste visible).
- Paso 3: todas las animaciones en cuadrícula; guardar en la ficha.
- Sin clave: banner "Configura tu clave en Ajustes para generar. Puedes seguir con un arquetipo".

### 4.12 Ajustes

Secciones: **Clientes** (rutas detectadas, editables) · **Claves de imagen** (añadir, probar, borrar; estado "guardada en el almacén seguro") · **Permisos por defecto** · **Presupuestos** · **Apariencia** (tema, reducir movimiento, tamaño de texto) · **Acerca de** (versión y estado de cada función).

### 4.13 Pantalla de bienvenida (primera vez)

Tres pasos: detectamos tus clientes → ¿quieres capturar un agente inicial? → tour breve (Dex, Sala, Bandeja). Se puede saltar.

## 5. Estados transversales

| Situación | Comportamiento |
|---|---|
| Cargando | Esqueletos; nunca pantalla en blanco |
| Vacío | Mensaje + acción principal |
| Error de red/API | Mensaje claro, causa probable, **Reintentar** |
| API caída | Banner "Servicio local detenido. Ejecuta /agent-dex:abrir de nuevo" |
| Función en diseño | Insignia "En diseño"; no clicable |
| Token de arranque inválido | Pantalla "Abre la app desde /agent-dex:abrir" |

## 6. Accesibilidad

- Todo operable con teclado; orden de foco lógico; atajos documentados (p. ej. `g d` Dex, `g s` Sala, `g b` Bandeja, `?` ayuda).
- Estados con icono + texto + color. Animaciones con alternativa textual.
- Regiones `aria-live` para cambios de estado y nuevas pendientes.
- Editor de grafo con alternativa en lista/tabla de nodos y conexiones.
- Zoom hasta 400 % sin pérdida de funciones; objetivos táctiles ≥ 44 px en estrecho.
- Pruebas: auditoría automatizada + revisión manual con lector de pantalla antes de cada versión.

## 7. Inventario de componentes

Tarjeta de agente · Insignia de estado · Sprite animado · Selector de estados · Diálogo de captura · Tarjeta de permiso · Tarjeta de pendiente · Editor de grafo y nodos · Gráfico de rondas (con tabla) · Asistente por pasos · Vista de diferencias · Panel de coste · Banner de estado de servicio.

## 8. Entregables de diseño siguientes

1. Prototipo navegable de baja fidelidad (Dex, Ficha, Sala, Bandeja) para validar con 3 personas.
2. Biblioteca de tokens y componentes en Storybook (o equivalente).
3. Arquetipos de personaje incluidos: 5 arquetipos × 6 estados.
