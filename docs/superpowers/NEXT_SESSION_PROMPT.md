# Prompt para continuar en la sesión de WSL

Copia y pega todo lo que hay dentro del bloque en Claude Code (abierto en
WSL, en la carpeta del repo, en `main`).

```text
Vamos a ejecutar la migración del gemelo digital Kinova Gen3 de ROS1 Noetic a ROS2 Jazzy + Unity (ROS-TCP-Connector). El diseño y el plan ya están aprobados; no hay que volver a discutirlos.

Lee primero, completos:
1. docs/superpowers/specs/2026-11-08-ros2-unity-migration-design.md (spec aprobado)
2. docs/superpowers/plans/2026-11-08-ros2-unity-migration.md (plan aprobado, 8 tareas)
3. docs/setup/wsl-ros2-unity-mcp.md (cómo está montado este PC)

Contexto del entorno:
- Estás en WSL Ubuntu 24.04 con ROS2 Jazzy instalado por apt (red mirrored). El repo está en el disco de Windows (/mnt/c/...). Unity 2022.3.22f1 corre en Windows.
- Tienes el MCP de Unity registrado como "UnityMCP" (HTTP 127.0.0.1:8080/mcp). Hasta la Task 4 no existe el proyecto Unity/ en el repo, así que estará desconectado; tras la Task 4 me pides que abra Unity y arranque el servidor (Task 4 Step 5).
- El brazo Kinova Gen3 está en 192.168.1.10. Leer su estado está permitido; NUNCA lo muevas sin pedirme permiso explícito justo antes (Task 7 Step 4).

Cómo trabajar:
- Ejecuta el plan tú mismo, tarea por tarea, en esta sesión (modo directo: usa la skill superpowers:executing-plans si la tienes; si no, sigue el plan tal cual). Al final, una revisión de toda la rama.
- Crea la rama feat/ros2-unity-migration desde main y haz commit + push al terminar cada tarea.
- Antes de la Task 1, haz las comprobaciones de la sección "Entorno de ejecución" del plan (ros2, import kortex_api, ping al brazo) y dime el resultado. Si kortex_api no importa, intenta arreglarlo con lo del setup doc §2.5 y dime qué funcionó.
- Si algo del plan no cuadra con la realidad (p. ej. ROS-TCP-Endpoint no compila en Jazzy, una API de C# distinta, el URDF Importer no se puede lanzar por MCP), arréglalo con el cambio mínimo, apúntalo y sigue; si cambia el diseño, para y pregúntame.
- Cada vez que digas que algo funciona, que sea con la salida del comando o de la consola de Unity delante. Si algo no se pudo probar, dilo claramente.
- Respóndeme en español.

Empieza.
```
