# Prompts de imagen prediseñados

Biblioteca de plantillas para que cada persona genere el personaje y las animaciones de su agente **con su propia clave** (ver F13). Viven en `prompts/` como archivos de datos; este documento define su diseño y los textos base.

## Principios

- La app **compone** el prompt desde plantillas + los datos del agente y **lo muestra** antes de enviar.
- Sin personajes, nombres ni estilos de franquicias existentes. Criaturas y personajes originales.
- Primero un **personaje base**; las animaciones lo usan como imagen de referencia.
- Salida predecible: una hoja con cuadrícula fija para recortar automáticamente.
- El texto del usuario se trata como dato: se inserta en campos delimitados.

## Variables

| Variable | Ejemplo | Origen |
|---|---|---|
| `{rol}` | revisor de contratos | Ficha |
| `{personalidad}` | meticuloso, curioso, tranquilo | Ficha |
| `{arquetipo}` | investigador, constructor, guardián, mensajero, artista | Selector |
| `{colores}` | azul petróleo y ámbar | Usuario |
| `{accesorio}` | lupa | Usuario |
| `{pasatiempo}` | lee libros | Según personalidad o usuario |

## Estilo base (se antepone a todo)

```text
Original character design in a clean pixel-art style, front-facing, solid flat
background of a single color (#00FF00) for easy removal, no text, no logos, no
watermark, no existing franchise characters or creatures, consistent proportions,
limited palette of 12 colors.
```

## Plantilla 1 — Personaje base

```text
{ESTILO BASE}
A friendly original character who is a {arquetipo} working as {rol}.
Personality: {personalidad}. Main colors: {colores}. Signature item: {accesorio}.
Full body, centered, neutral standing pose, 64x64 pixel look scaled up.
```

## Plantilla 2 — Hoja de animación por estado

Se usa la imagen del personaje base como referencia. Cuadrícula fija: **1 fila × 6 cuadros**, mismo tamaño y anclaje en cada cuadro.

```text
{ESTILO BASE}
Using the attached reference character exactly (same design, colors, proportions),
draw a sprite sheet of 6 equal frames in one horizontal row showing a looping
animation of: {accion_del_estado}. Keep the character in the same position and
scale in every frame; only the pose changes.
```

| Estado | `{accion_del_estado}` |
|---|---|
| Trabajando | typing quickly at a small desk, then looking at a paper, repeating |
| Entrenando | doing repeated exercise: jumping jacks or lifting a small weight |
| Descansando | sitting down and sleeping with a gentle breathing motion |
| Tiempo libre | `{pasatiempo}` (ver tabla siguiente) |
| Esperando | raising one hand, a question mark appearing above the head |
| Error | scratching head with a confused expression |

### Tiempo libre por personalidad

| Personalidad | Pasatiempo por defecto |
|---|---|
| Curioso | reading a book |
| Meticuloso | arranging small objects in order |
| Creativo | doodling on a sketchpad |
| Tranquilo | watering a small plant |
| Enérgico | stretching and bouncing |

## Plantilla 3 — Retrato de ficha

```text
{ESTILO BASE}
Bust portrait of the attached reference character, smiling, slightly larger
detail, centered, same palette.
```

## Plantilla 4 — Variaciones

Ajustes sobre el personaje base: otro color, accesorio distinto, versión "evolucionada" (más detalle) cuando el agente sube de nivel.

## Procesado local (después de generar)

1. Quitar el color de fondo (`#00FF00`) → transparente.
2. Cortar en 6 cuadros iguales; recentrar por el punto de anclaje.
3. Escalar con vecino más cercano.
4. Vista previa en bucle con control de velocidad.
5. Si la hoja sale desalineada, **reintentar** (mostrando coste) o editar manualmente.

## Reglas de coste y claves

- Antes de cada lote: "Esto generará N imágenes, coste estimado ≈ X".
- Orden recomendado y más barato: base → una animación para probar → el resto.
- La clave se guarda en el almacén del sistema y solo viaja al proveedor elegido.
- Alternativas sin coste: usar arquetipos incluidos o subir imagen propia.

## Pendiente de verificar

- Qué proveedores admiten **imagen de referencia** de forma fiable y a qué precio.
- Tamaño y calidad mínimos que dan cuadros limpios.
- Términos de uso del proveedor para personajes que se compartan públicamente.
