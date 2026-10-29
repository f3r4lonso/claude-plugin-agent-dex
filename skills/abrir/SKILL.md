---
name: abrir
description: Abre Agent Dex, la interfaz web local para coleccionar, crear y poner a trabajar agentes y skills. Úsalo cuando la persona escriba /agent-dex:abrir o pida abrir su Dex.
disable-model-invocation: true
allowed-tools: Bash
---

# Abrir Agent Dex

Inicia el servicio local de Agent Dex y abre la interfaz en el navegador. Responde en el idioma de la persona. Informa resultados, no código.

## Pasos

1. Comprueba si ya está en marcha: `curl -s -m 2 http://127.0.0.1:8771/api/health`.
   - Si responde `{"ok":true,...}`, dile que ya está abierto y que use la pestaña existente o la dirección del terminal donde lo inició. No inicies otro.
2. Comprueba que `uv` existe: `uv --version`.
   - Si no existe, **no lo instales tú**. Explica que Agent Dex necesita `uv` y muestra la guía oficial: https://docs.astral.sh/uv/getting-started/installation/ . Alternativa con Python 3.11+: `pip install "git+https://github.com/f3r4lonso/claude-plugin-agent-dex@v0.1.0-beta#subdirectory=api"` y luego `agent-dex serve --open`. Detente aquí.
3. Inicia el servicio **en segundo plano** (Bash con `run_in_background: true`) desde la carpeta del proyecto actual:

   ```text
   uvx --from "git+https://github.com/f3r4lonso/claude-plugin-agent-dex@v0.1.0-beta#subdirectory=api" agent-dex serve --open
   ```

   La primera vez descarga unos 300 MB (incluye el SDK de Claude); avísalo. Las siguientes veces es inmediato.
4. Espera unos segundos y lee la salida del proceso en segundo plano. Debe mostrar una dirección `http://127.0.0.1:PUERTO/#t=…`.
5. Dile a la persona: el navegador se abrió solo; si no, que copie esa dirección. **El código `#t=…` es privado: no lo pegues en ningún otro lugar ni lo guardes en archivos.**

## Notas para ti

- Para detenerlo, la persona puede cerrar el proceso en segundo plano (`/tasks`) o pulsar Ctrl+C en su terminal.
- Si el puerto 8771 está ocupado, el servicio usa el siguiente libre; en ese caso la Sala en vivo (hooks del plugin) no recibirá eventos y conviene avisarlo.
- Agent Dex no tiene cuentas ni envía datos a servidores propios. Los chats usan la sesión de Claude Code de la persona.
