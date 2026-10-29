# Gimnasio de agentes

## Qué significa "entrenar"

Los pesos del modelo no cambian. Mejora lo que rodea al modelo: **instrucciones, skills y memoria de lecciones**. La mejora debe poder medirse.

## Ingredientes de un entrenamiento

| Ingrediente | Descripción |
|---|---|
| Agente | El agente a entrenar (versión inicial = ronda 0) |
| Contexto | Archivos o texto que el agente debe usar |
| Skills | Skills disponibles durante la tarea |
| Tarea | Prompt repetible, con entradas de ejemplo |
| Criterio | Cómo se puntúa: rúbrica, pruebas automáticas o comparación con una respuesta de referencia |
| Rondas | Número de iteraciones (por defecto 5) y presupuesto máximo |

## Ciclo de una ronda

1. **Ejecutar:** el agente hace la tarea con su instrucciones + memoria actual.
2. **Puntuar:** un evaluador independiente (otro agente, sin ver la memoria) aplica el criterio y da nota y motivos.
3. **Reflexionar:** el agente entrenador (`dex-trainer`) propone una lección concreta ("revisa X antes de Y").
4. **Decidir:** la lección se acepta solo si la nota sube o se mantiene en una repetición de control; si no, se descarta.
5. **Guardar:** lección aceptada → `memory/lessons.md`; ronda completa → `memory/rounds/*.jsonl`.

## Memoria

- `lessons.md`: lista corta y curada (máximo ~30 líneas); es lo único que se inyecta al agente. Si crece, el entrenador la resume.
- `rounds/`: historial completo (entrada, salida, nota, lección propuesta, aceptada o no). No se inyecta.
- Cada lección guarda de qué ronda salió, para poder revertir.

## Protecciones contra falsa mejora

- Evaluador separado del que ejecuta.
- Conjunto de tareas de control no usado para aprender (evita sobreajuste a un ejemplo).
- Tope de rondas y de coste; se detiene si no hay mejora en 3 rondas seguidas.
- Las lecciones nunca pueden ampliar permisos ni herramientas del agente.
- El usuario ve y aprueba el diff de instrucciones/memoria antes de fijar una nueva versión.

## Visualización

La Dex muestra: curva de nota por ronda, lecciones aceptadas/rechazadas, y comparación "ronda 0 vs actual" en la misma tarea.

## Pendiente de decidir

- Rúbrica por defecto cuando el usuario no define criterio.
- Cómo estimar y mostrar el coste de una sesión de entrenamiento antes de empezar.
