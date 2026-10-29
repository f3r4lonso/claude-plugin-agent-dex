# Publicación

## Objetivo

Que cualquiera instale el plugin desde tu GitHub:

```text
/plugin marketplace add f3r4lonso/claude-plugin-agent-dex
/plugin install agent-dex@agent-dex
```

El repo es a la vez **plugin** y **marketplace de un solo plugin**: `.claude-plugin/plugin.json` describe el plugin y `.claude-plugin/marketplace.json` lo lista.

## Lista antes de cada publicación

1. Licencia MIT (`LICENSE`). Las fuentes y el contenido del Glosario conservan su licencia propia.
2. El arte de los personajes es original de este proyecto (se dibuja en código, `web/src/sprite-data.ts`): no hay derechos de terceros que resolver.
3. Revisar el diff completo por secretos y rutas personales (`git grep` de claves y de rutas de usuario).
4. Probar el plugin en local: `/plugin marketplace add <ruta-local-del-repo>`.
5. Subir versión en `.claude-plugin/plugin.json`, `api/pyproject.toml`, `api/src/agent_dex/__init__.py` y `web/package.json`; actualizar `CHANGELOG.md`.
6. Compilar la interfaz (`cd web && npm run build`) y comprobar que `api/src/agent_dex/static` está al día.
7. Etiquetar (`vX.Y.Z-beta.N`) y crear el release en GitHub. La skill `/agent-dex:abrir` y el README fijan la etiqueta de la versión que instalan.
8. Verificar la instalación limpia desde GitHub en un entorno nuevo.

## Versionado

SemVer. `0.x` mientras el formato del agente canónico pueda cambiar.

## Repo

- Descripción y topics sugeridos: `claude-code`, `claude-plugin`, `agents`, `skills`, `ai-agents`.
- Plantillas de issue: "proponer entrada al catálogo" y "reporte de bug".
- Commit y push solo cuando el propietario lo pida.
