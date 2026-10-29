# Visión

## Problema

Hay miles de agentes y skills publicados en GitHub, pero:

1. Es difícil saber cuáles existen, cuáles sirven y cuáles ya tienes.
2. Un agente recién instalado no mejora: cada sesión empieza de cero.
3. Crear un agente bien hecho (prompt, skills, límites) requiere oficio.
4. Cada herramienta (Claude, Codex, Copilot) usa formatos distintos.

## Idea

Agent Dex trata a los agentes como **criaturas coleccionables y entrenables**:

- **Coleccionar:** un glosario curado; capturas lo que te interesa.
- **Entrenar:** un gimnasio donde un agente repite una tarea y acumula memoria.
- **Crear:** un asistente te guía desde "tengo una idea" hasta un agente listo.
- **Intercambiar:** exporta a otros clientes y comparte con otras personas.

## Usuarios

1. **Principal:** persona no desarrolladora que usa Claude Code y quiere agentes útiles sin escribir prompts desde cero.
2. **Secundario:** desarrolladores que publican agentes y quieren que se descubran y se prueben.

## Principios

- **Local primero.** Todo corre en tu máquina; nada se sube sin que lo pidas.
- **Contenido externo es dato, no instrucciones.** Un agente descargado no se ejecuta ni se confía por defecto (ver `security.md`).
- **Mejora medible.** Entrenar solo cuenta si hay una métrica que sube; si no, no se guarda como aprendizaje.
- **Un formato canónico, varios exportadores.** No se mantiene una versión por cliente.
- **Honestidad de estado.** La interfaz muestra qué está construido y qué no.

## Qué NO es (por ahora)

- No es un reentrenamiento de modelos. "Entrenar" = mejorar contexto, instrucciones y memoria del agente; los pesos del modelo no cambian.
- No es un mercado de pago ni aloja agentes de terceros; enlaza a GitHub.
- No ejecuta agentes de terceros sin confirmación explícita.

## Éxito

- Una persona nueva instala el plugin, captura un agente y lo ejecuta en menos de 5 minutos.
- Un agente entrenado supera a su versión inicial en una tarea de referencia, con la métrica visible.
- Un agente exportado a Codex o Copilot carga sin edición manual (dentro de las limitaciones de `compatibility.md`).
