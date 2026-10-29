# Seguridad

## Reportar una vulnerabilidad

Usa **Report a vulnerability** en la pestaña *Security* de este repositorio (aviso privado de GitHub). Por favor no abras un issue público con detalles explotables. Responderemos lo antes posible.

## Modelo de seguridad de la beta

- El servicio escucha solo en `127.0.0.1`.
- Cada arranque genera un **código aleatorio** que va en la dirección que se abre (`#t=…`). La API y el WebSocket lo exigen; sin él responden 401.
- Se valida estrictamente `Host` y `Origin`, para impedir que otras páginas web usen la API local.
- Cabeceras de seguridad y CSP estricta. El texto de agentes y skills se muestra siempre como texto escapado.
- Las acciones de los agentes pasan por permisos: chats y tareas «preguntar» esperan una decisión humana; las tareas «solo lectura» deniegan todo lo demás. Nada se aprueba solo.
- **Glosario:** cada entrada está fijada a un commit; los archivos se verifican por hash antes de escribirse; nunca se sobrescribe nada; nunca se ejecuta contenido capturado; «Liberar» borra solo lo que Agent Dex copió.
- El endpoint `/api/hook` (usado por los hooks del plugin) no lleva código, solo cambia el estado visual de un agente y exige JSON sin cabecera `Origin`.
- No hay cuentas ni telemetría. La única red saliente propia es hacia GitHub al capturar.

## Límites conocidos

- Cualquier proceso del mismo ordenador y usuario puede leer la dirección con el código si se la muestras o la imprimes en un terminal compartido.
- Los workflows y pendientes viven en memoria: al cerrar la app lo que esperaba queda «interrumpido».
- Claude, al ejecutar una skill capturada que incluya scripts, puede ejecutarlos si se lo pides: revisa los avisos «contiene código ejecutable».
