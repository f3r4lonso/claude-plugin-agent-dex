# Seguridad

Heredado del prototipo: solo loopback (`127.0.0.1`), códigos de emparejamiento de un solo uso, sesiones en memoria, comprobación exacta de Host/Origin, CSP estricta, texto de recursos siempre escapado.

> El modelo completo de seguridad local (token de arranque, Host/Origin, rutas permitidas) está en `stack-tecnico.md`, sección 5. En esta versión el servicio es Python (FastAPI), no Node.

## Riesgos nuevos de este proyecto

| Riesgo | Mitigación |
|---|---|
| Claves de imagen de los usuarios filtradas | Almacén seguro del sistema; nunca en logs, paquetes ni repo; solo viajan al proveedor elegido |
| Workflow que se queda en bucle o gasta sin control | Tope de pasos, tiempo y presupuesto; al excederlo, pausa en la Bandeja |
| Una pausa humana se aprueba sola | No existe vencimiento ni aprobación automática |

| Riesgo | Mitigación |
|---|---|
| Un agente o skill capturado contiene instrucciones maliciosas (inyección) | Es dato, no instrucción. Revisión automática + vista previa + confirmación. Nunca se ejecuta al capturar. |
| Hooks o scripts ocultos en lo capturado | Se detectan y se marcan "requiere atención"; se muestran completos antes de confirmar. |
| Catálogo apunta a un repo que cambia después | Commit fijado; actualizar exige nueva revisión. |
| El gimnasio ejecuta tareas con efectos reales | Las tareas de entrenamiento corren con herramientas de solo lectura por defecto; escribir/ejecutar exige permiso explícito por sesión. |
| Una "lección" amplía permisos del agente | Prohibido por diseño: las lecciones solo añaden texto de buenas prácticas. |
| Secretos en memoria o paquetes compartidos | Escaneo antes de guardar y antes de empaquetar; nunca se leen `.env`, claves ni tokens. |
| Coste descontrolado en entrenamiento | Presupuesto y tope de rondas obligatorios. |

## Reglas de implementación

- Nuevas dependencias: revisar licencia, scripts de instalación y avisos antes; instalar con `--ignore-scripts`.
- Nada de red saliente salvo a GitHub para el glosario y capturas, y siempre visible para el usuario.
- Reporte de vulnerabilidades: abrir un aviso privado de seguridad en GitHub (a configurar al publicar).
