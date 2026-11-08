# Migración Kinova Gen3 a ROS2 Jazzy + Unity Robotics Hub — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dejar en este repo `ROS/` (workspace ROS2 Jazzy con el control del Kinova Gen3 y el endpoint TCP) y `Unity/` (proyecto Unity sin ROS#, con ROS-TCP-Connector y URDF Importer).

**Architecture:** `kinova_controller` (rclpy) habla con el brazo por la Kortex API, publica `/joint_states` y escucha `/controller`. `ros_tcp_endpoint` puentea esos topics a Unity por TCP 10000. En Unity, `KinovaPosePublisher` publica la pose del pinch y `KinovaJointStateSubscriber` mueve las articulaciones del robot reimportado.

**Tech Stack:** ROS2 Jazzy (rclpy, ament_python, ament_cmake, launch_ros), Kortex API Python 2.6, ROS-TCP-Endpoint `main-ros2`, Unity 2022.3.22f1, ROS-TCP-Connector v0.7.0, URDF Importer v0.5.2.

**Spec:** `docs/superpowers/specs/2026-11-08-ros2-unity-migration-design.md`

**Fuentes de referencia (solo lectura; clonar fuera del repo al empezar):**
```bash
mkdir -p ~/kinova-ref && cd ~/kinova-ref
git clone --depth 1 https://github.com/slrac03/kinova-ros-noetic-slrac
git clone --depth 1 https://github.com/slrac03/Kinova-unity-digital-twin
export REF_ROS=~/kinova-ref/kinova-ros-noetic-slrac REF_UNITY=~/kinova-ref/Kinova-unity-digital-twin
```

## Global Constraints

- Distro: ROS2 **Jazzy**. Topics: `/joint_states` (`sensor_msgs/JointState`, rad), `kinova_current` (`std_msgs/String`), `/controller` (`geometry_msgs/PoseStamped`).
- Parámetros de `kinova_controller` y defaults: `robot_ip`=`192.168.1.10`, `username`=`admin`, `password`=`admin`, `publish_rate`=`10.0`, `home_action`=`Home`.
- Timeout de acciones Kortex: `15` s.
- Endpoint TCP: puerto `10000`, `ROS_IP` default `0.0.0.0`.
- Unity: `com.unity.robotics.ros-tcp-connector` en `https://github.com/Unity-Technologies/ROS-TCP-Connector.git?path=/com.unity.robotics.ros-tcp-connector#v0.7.0`; `com.unity.robotics.urdf-importer` en `https://github.com/Unity-Technologies/URDF-Importer.git?path=/com.unity.robotics.urdf-importer#v0.5.2`. Sin `com.siemens.ros-sharp`.
- No se copian a `Unity/`: `TempAssembly.dll`, `survey/`, `cuestionario_validacion_revisado.csv`, `.vscode/`.
- Nada de C# se porta a Python.
- Trabajo en la rama `feat/ros2-unity-migration` creada desde `main`; push a esa rama tras cada tarea. Commits con las líneas de atribución de la sesión.

## Entorno de ejecución

PC del usuario: **WSL Ubuntu 24.04 con ROS2 Jazzy instalado por apt** (red
mirrored), Unity 2022.3.22f1 en Windows, **MCP de Unity** (MCP for Unity,
HTTP `127.0.0.1:8080/mcp`). Preparación: `docs/setup/wsl-ros2-unity-mcp.md`.

- Repo en el disco de Windows, visto desde WSL en `/mnt/c/Users/<usuario>/Kinova-Twin-Work`.
- Cada shell: `source /opt/ros/jazzy/setup.bash` (y `source ROS/install/setup.bash` tras compilar).
- Sin `--symlink-install` (está en `/mnt/c`).
- Antes de Task 1: `ros2 --help`, `python3 -c "import kortex_api"` y
  `ping -c1 192.168.1.10`. Si Kortex no importa, arreglarlo primero
  (ver setup doc §2.5) o seguir y dejar Task 2 Step 6 como pendiente.
- Las tareas 1–4 no necesitan Unity. **Tras Task 4, parar** y pedir al
  usuario: abrir `Unity/` en Unity Hub, esperar la importación de paquetes,
  *Window → MCP for Unity → Start Server*, y en Claude Code `/mcp` para
  reconectar `UnityMCP`. Las tareas 5–7 usan el MCP.
- Brazo real: solo con permiso explícito del usuario en cada prueba que lo
  mueva (Task 7). Lecturas (`/joint_states`) sí sin preguntar.

## Review Focus

1. Arrancar `kinova_controller` sin robot / IP equivocada → un `[ERROR]` claro con la IP y salida con código ≠ 0, sin traceback. (Task 2 Step 6: `ros2 run kinova_mov kinova_controller --ros-args -p robot_ip:=192.168.1.250`.)
2. El robot reporta 7 articulaciones (Gen3 7DOF) → `/joint_states` con `joint_1..joint_7`, no truncado a 6. (Task 2, `test_make_joint_state_uses_reported_count`.)
3. Un `/controller` llega mientras el brazo aún se mueve → `/joint_states` sigue publicándose (grupos de callback separados). (Task 7, `ros2 topic hz /joint_states` durante un movimiento.)
4. Unity recibe `/joint_states` con nombres que no existen en el robot importado (p. ej. joints de la pinza) → se ignoran sin excepción. (Task 7: con `fake_joint_states` + un publicador de `left_finger_joint`, consola de Unity sin errores.)
5. ROS-TCP-Endpoint no compila/arranca en Jazzy → se parchea en el fork local o se documenta. (Task 3, `colcon build` + puerto 10000 escuchando.)

---

### Task 1: Paquete `kinova_gen3_description`

**Files:**
- Create: `ROS/src/kinova_gen3_description/{package.xml,CMakeLists.txt}`
- Create: `ROS/src/kinova_gen3_description/urdf/GEN3.urdf` (copia de `$REF_ROS/src/kinova_gen3_urdf/urdf/GEN3.urdf` con `package://kinova_gen3_urdf/` → `package://kinova_gen3_description/`)
- Create: `ROS/src/kinova_gen3_description/meshes/` (copia de `$REF_ROS/src/kinova_gen3_urdf/meshes/`)
- Create: `ROS/src/kinova_gen3_description/rviz/gen3.rviz` (copia; cambiar clases `rviz/…` a `rviz_default_plugins/…` si las tiene)
- Create: `ROS/src/kinova_gen3_description/scripts/fake_joint_states.py`
- Create: `ROS/src/kinova_gen3_description/launch/display.launch.py`
- Create: `ROS/.gitignore` (`build/`, `install/`, `log/`)

**Interfaces:**
- Produces: paquete `kinova_gen3_description` que instala `urdf/`, `meshes/`, `rviz/`, `launch/` en `share/` y `fake_joint_states.py` en `lib/kinova_gen3_description/`.
- Produces: `display.launch.py` con args `fake` (default `false`) y `rviz` (default `true`).

- [ ] **Step 1: Comprobar entorno** (sección "Entorno de ejecución") y clonar las referencias. Esperado: `ros2 --help` funciona, `$REF_ROS` y `$REF_UNITY` existen.
- [ ] **Step 2: Copiar URDF, mallas y rviz; reescribir rutas.** Verificación: todas las mallas referenciadas existen:
  ```bash
  cd ROS/src/kinova_gen3_description && grep -oE 'package://kinova_gen3_description/[^"]+' urdf/GEN3.urdf | sort -u | sed 's#package://kinova_gen3_description/##' | xargs -I{} test -f {} && echo OK
  ```
  Esperado: `OK`, y `grep -c kinova_gen3_urdf urdf/GEN3.urdf` → `0`.
- [ ] **Step 3: `package.xml` (format 3, `ament_cmake`, exec_depend `robot_state_publisher`, `rviz2`, `rclpy`, `sensor_msgs`, `launch_ros`) y `CMakeLists.txt`** que instala los directorios y `install(PROGRAMS scripts/fake_joint_states.py DESTINATION lib/${PROJECT_NAME})`.
- [ ] **Step 4: `fake_joint_states.py`**: port directo de `$REF_ROS/src/kinova_gen3_urdf/scripts/joint_state_pub.py` a rclpy (nodo `fake_joint_states`, timer 60 Hz, `position = sin(angle + i) * 0.5`, `angle += 0.05`, nombres `joint_1..joint_6`).
- [ ] **Step 5: `display.launch.py`**: `robot_state_publisher` con `robot_description` = contenido de `GEN3.urdf`; si `fake`, `fake_joint_states.py`; si `rviz`, `rviz2 -d gen3.rviz`.
- [ ] **Step 6: Compilar y probar**
  ```bash
  cd ROS && colcon build --packages-select kinova_gen3_description && source install/setup.bash
  timeout 8 ros2 launch kinova_gen3_description display.launch.py fake:=true rviz:=false &
  sleep 4 && ros2 topic echo /joint_states --once | grep -A6 '^name'; ros2 topic echo /tf --once | head -3
  ```
  Esperado: build sin errores; nombres `joint_1`…`joint_6`; `/tf` publica transforms.
- [ ] **Step 7: Commit** `feat(ros): add kinova_gen3_description package for ROS2 Jazzy`

### Task 2: Paquete `kinova_mov` (controlador)

**Files:**
- Create: `ROS/src/kinova_mov/{package.xml,setup.py,setup.cfg,resource/kinova_mov}`
- Create: `ROS/src/kinova_mov/kinova_mov/__init__.py`
- Create: `ROS/src/kinova_mov/kinova_mov/joint_state.py`
- Create: `ROS/src/kinova_mov/kinova_mov/utilities.py` (copia literal de `$REF_ROS/src/kinova_mov/scripts/utilities.py`)
- Create: `ROS/src/kinova_mov/kinova_mov/kinova_controller.py`
- Test: `ROS/src/kinova_mov/test/test_joint_state.py`

**Interfaces:**
- Produces: `make_joint_state(degrees: Sequence[float], stamp: builtin_interfaces.msg.Time) -> sensor_msgs.msg.JointState` en `kinova_mov/joint_state.py` (sin importar kortex). Nombres `joint_{i+1}`, posiciones en radianes.
- Produces: entry point `kinova_controller = kinova_mov.kinova_controller:main`.
- Consumes: `DeviceConnection(ipAddress, port=DeviceConnection.TCP_PORT, credentials=(user, pass))` de `utilities.py` (context manager → `RouterClient`).

- [ ] **Step 1: Test que falla** en `test/test_joint_state.py`:
  ```python
  import math
  from builtin_interfaces.msg import Time
  from kinova_mov.joint_state import make_joint_state

  def test_make_joint_state_converts_degrees_to_radians():
      js = make_joint_state([0.0, 90.0, 180.0, 360.0, -90.0, 45.0], Time(sec=3))
      assert js.name == [f"joint_{i}" for i in range(1, 7)]
      assert js.position == [0.0, math.pi / 2, math.pi, 2 * math.pi, -math.pi / 2, math.pi / 4]
      assert js.header.stamp.sec == 3

  def test_make_joint_state_uses_reported_count():
      js = make_joint_state([10.0] * 7, Time())
      assert js.name[-1] == "joint_7" and len(js.position) == 7
  ```
- [ ] **Step 2: Paquete mínimo (`package.xml` ament_python con deps `rclpy`, `sensor_msgs`, `geometry_msgs`, `std_msgs`, `builtin_interfaces`, test_depend `python3-pytest`; `setup.py` instala `launch/*.launch.py` y el entry point) y correr:** `colcon build --packages-select kinova_mov && colcon test --packages-select kinova_mov --pytest-args -k joint_state; colcon test-result --verbose`. Esperado: FAIL (`ModuleNotFoundError: kinova_mov.joint_state`).
- [ ] **Step 3: Implementar `make_joint_state`** (comprensiones con `math.radians`).
- [ ] **Step 4: Re-ejecutar.** Esperado: 2 passed.
- [ ] **Step 5: `kinova_controller.py`**, port de `$REF_ROS/src/kinova_mov/scripts/pruebas_api.py`:
  - `class KinovaController(Node)`: declara los 5 parámetros (Global Constraints). `start(base: BaseClient) -> None` guarda `base`, llama `move_to_home()`, crea publishers `/joint_states` y `kinova_current` (qos 10), timer `1/publish_rate` en un `MutuallyExclusiveCallbackGroup` y la suscripción `/controller` en **otro** `MutuallyExclusiveCallbackGroup`.
  - `move_to_home() -> bool`: igual que `example_move_to_home_position`, buscando la acción `home_action`.
  - `publish_state()`: `GetMeasuredJointAngles` + `ComputeForwardKinematics`; publica el texto actual (mismo formato) y `make_joint_state([ja.value for ja in angles.joint_angles], self.get_clock().now().to_msg())`. Excepciones → `get_logger().error`, sin relanzar.
  - `on_pose(msg: PoseStamped)`: lógica de `calc_ik` + `send_joint_angles` del original (posición de `msg.pose.position`, orientación actual `theta_*`, semilla = ángulos actuales, espera END/ABORT con `TIMEOUT_DURATION = 15`). `KServerException` → log error y return.
  - `check_for_end_or_abort(e)` igual que el original.
  - `main()`: `rclpy.init`; crea nodo; lee params; `try: with DeviceConnection(ip, credentials=(u, p)) as router:` → `node.start(BaseClient(router))`; `MultiThreadedExecutor().add_node(node)`; `spin()`. `except Exception as ex`: `node.get_logger().error(f"No se pudo conectar al robot en {ip}: {ex}")` y `sys.exit(1)`. `KeyboardInterrupt` → salida limpia. Siempre `node.destroy_node(); rclpy.try_shutdown()`.
  - Imports de kortex igual que el original (`BaseClient`, `KServerException`, `Base_pb2`).
- [ ] **Step 6: Comprobar arranque y fallo limpio:** `colcon build --packages-select kinova_mov && source install/setup.bash && ros2 pkg executables kinova_mov` → `kinova_mov kinova_controller`. Luego `ros2 run kinova_mov kinova_controller --ros-args -p robot_ip:=192.168.1.250; echo "exit=$?"` → una línea `[ERROR] … 192.168.1.250 …`, sin traceback, `exit=1`. (Si Kortex no importa en el entorno, dejar este paso marcado como pendiente y decirlo.)
- [ ] **Step 7: Commit** `feat(ros): port kinova_mov controller to rclpy`

### Task 3: ROS-TCP-Endpoint y launch para Unity

**Files:**
- Create: `ROS/ros2.repos`
- Create: `ROS/src/kinova_mov/launch/kinova_unity.launch.py`
- Modify: `ROS/.gitignore` (añadir `src/ROS-TCP-Endpoint/`)

**Interfaces:**
- Consumes: entry point `kinova_controller` (Task 2); paquete `ros_tcp_endpoint`, ejecutable `default_server_endpoint`, params `ROS_IP`, `ROS_TCP_PORT`.
- Produces: `ros2 launch kinova_mov kinova_unity.launch.py robot_ip:=… ros_ip:=… tcp_port:=…` (defaults `192.168.1.10`, `0.0.0.0`, `10000`).

- [ ] **Step 1: `ros2.repos`**
  ```yaml
  repositories:
    ROS-TCP-Endpoint:
      type: git
      url: https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git
      version: main-ros2
  ```
  y `cd ROS && git clone -b main-ros2 https://github.com/Unity-Technologies/ROS-TCP-Endpoint.git src/ROS-TCP-Endpoint` (equivalente a `vcs import src < ros2.repos`).
- [ ] **Step 2: Compilar el endpoint en Jazzy:** `colcon build --packages-select ros_tcp_endpoint`. Esperado: éxito. Si falla, aplicar el parche mínimo, documentarlo en el README (sección "Notas Jazzy") y, si es un cambio de código, cambiar `ros2.repos` para que no dependa de él (p. ej. instrucción `sed` en README).
- [ ] **Step 3: `kinova_unity.launch.py`** con los tres args y dos `Node`: `ros_tcp_endpoint/default_server_endpoint` (`parameters=[{"ROS_IP": ros_ip, "ROS_TCP_PORT": tcp_port}]`) y `kinova_mov/kinova_controller` (`parameters=[{"robot_ip": robot_ip}]`, `output="screen"`).
- [ ] **Step 4: Probar endpoint escuchando:**
  ```bash
  colcon build && source install/setup.bash
  timeout 6 ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0 & sleep 3; (ss -ltn || netstat -ltn) | grep 10000
  ```
  Esperado: `LISTEN … :10000`. Además `ros2 launch kinova_mov kinova_unity.launch.py --show-args` lista `robot_ip`, `ros_ip`, `tcp_port`.
- [ ] **Step 5: Commit** `feat(ros): add Unity TCP endpoint launch`

### Task 4: Proyecto Unity migrado (sin ROS#)

**Files:**
- Create: `Unity/` ← `$REF_UNITY/{Assets,Packages,ProjectSettings,.gitignore,README.md}`
- Modify: `Unity/Packages/manifest.json` (quitar `com.siemens.ros-sharp`, añadir los dos paquetes de Global Constraints y `"com.coplaydev.unity-mcp": "https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.3.0"` para el MCP del editor)
- Modify: `Unity/Packages/packages-lock.json` (quitar el bloque `com.siemens.ros-sharp`)
- Delete: `Unity/Assets/URDF/{CMakeLists.txt,package.xml,launch,rviz,.vscode,scripts/joint_state_pub.py,scripts/KinovaPublisher.cs}` y sus `.meta`

- [ ] **Step 1: Copiar** con `rsync -a` las rutas listadas (sin `.git`).
- [ ] **Step 2: Editar `manifest.json` / `packages-lock.json`.** Verificación: `python -m json.tool` en ambos sin error; `grep -c ros-sharp Unity/Packages/*.json` → `0`; `grep -c 'robotics' Unity/Packages/manifest.json` → `2`; `grep -c unity-mcp Unity/Packages/manifest.json` → `1`.
- [ ] **Step 3: Borrar residuos ROS1.** Verificación: `grep -rl RosSharp Unity/Assets --include=*.cs` → vacío; `ls Unity/TempAssembly.dll Unity/survey 2>&1` → no existen; `du -sh Unity` ≈ 60 MB y ningún archivo > 50 MB (`find Unity -size +50M` vacío).
- [ ] **Step 4: Commit** `feat(unity): import Unity project, switch to Unity Robotics Hub packages`
- [ ] **Step 5: PARAR y pedir al usuario** que abra `Unity/`, espere los paquetes, arranque *Window → MCP for Unity → Start Server* (HTTP, 8080) y ejecute `/mcp` en Claude Code. Esperado: las herramientas `mcp__UnityMCP__*` disponibles. Si la consola de Unity ya muestra errores (scripts ROS# faltantes en la escena son esperados; errores de compilación no), anotarlos.

### Task 5: Scripts C# de comunicación

**Files:**
- Create: `Unity/Assets/URDF/scripts/KinovaPosePublisher.cs`
- Create: `Unity/Assets/URDF/scripts/KinovaJointStateSubscriber.cs`

**Interfaces:**
- Consumes: `Unity.Robotics.ROSTCPConnector.ROSConnection` (`GetOrCreateInstance`, `RegisterPublisher<T>`, `Publish`, `Subscribe<T>`), `RosMessageTypes.Geometry.PoseStampedMsg`, `RosMessageTypes.Sensor.JointStateMsg`, `Unity.Robotics.ROSTCPConnector.ROSGeometry` (`To<FLU>()`), `Unity.Robotics.UrdfImporter.UrdfJoint` (`jointName`), `Oculus.Interaction.Input.Hand` (`GetIndexFingerIsPinching()`).

- [ ] **Step 1: `KinovaPosePublisher : MonoBehaviour`** (sin namespace RosSharp). Campos públicos con los mismos nombres que `KinovaPublisher.cs` original para reasignar fácil: `poseText`, `RobotBaseTransform`, `FrameId="base_link"`, `RHand`, `RightHand`, más `topicName="/controller"`. Comportamiento idéntico al original: publicar una vez por flanco de pinch en `FixedUpdate`; `OnButtonClick()` publica `(0.5, 0.5, 0.5)` con orientación identidad y pone `poseText.text = "Home"`; `UpdateMessage()` usa `RobotBaseTransform.transform.InverseTransformPoint(RightHand.position).To<FLU>()`, orientación identidad, mismo texto en español (`"Posición relativa enviada:\n(x, y, z)"` con `F2`), y `Debug.LogError("RobotBaseTransform not asigned")` si falta. Header con `frame_id = FrameId` y stamp actual (`new TimeStamp(Clock.time)` de `Unity.Robotics.Core`). Se mantiene `[RequireComponent(typeof(Button))]`.
- [ ] **Step 2: `KinovaJointStateSubscriber : MonoBehaviour`**: campos `topicName="/joint_states"`, `robotRoot` (GameObject). En `Start`: diccionario `jointName → ArticulationBody` desde `robotRoot.GetComponentsInChildren<UrdfJoint>()`, y `Subscribe<JointStateMsg>`. En el callback: para cada `name[i]` con `TryGetValue`, `var d = ab.xDrive; d.target = (float)(position[i] * Mathf.Rad2Deg); ab.xDrive = d;`. Nombres desconocidos se ignoran.
- [ ] **Step 3: Verificación con el MCP de Unity:** refrescar assets / forzar recompilación y leer la consola del editor. Esperado: **0 errores de compilación** (CS####). `grep -n "RosSharp" Unity/Assets/URDF/scripts/*.cs` vacío.
- [ ] **Step 4: Commit** `feat(unity): ROS2 pose publisher and joint state subscriber`

### Task 6: Integración en la escena `ARM.unity` (vía MCP de Unity)

**Files:**
- Modify (desde el editor, vía MCP): `Unity/Assets/Scenes/ARM.unity`, `Unity/ProjectSettings/` (ROS Settings), assets generados por el URDF Importer bajo `Unity/Assets/URDF/urdf/`.

**Interfaces:**
- Consumes: `KinovaPosePublisher`, `KinovaJointStateSubscriber` (Task 5).

- [ ] **Step 1: Inventario antes de tocar:** con el MCP, listar en `ARM.unity` el robot viejo (GameObject raíz del GEN3), su posición/rotación/escala, su padre, la `Garra` y dónde cuelga, el objeto con el publisher viejo (Missing Script), el `RosConnector`, y quién referencia a quién (`RobotBaseTransform`, `RHand`, `RightHand`, `poseText`, `OnClick` del botón). Guardar ese inventario en la respuesta al usuario.
- [ ] **Step 2: Importar el robot:** `Assets/URDF/urdf/GEN3.urdf` con el URDF Importer (*Axis Type* `Z Axis`, *Mesh Decomposer* `VHACD`). Si la importación no se puede disparar por MCP (ventana modal), pedir al usuario que haga clic derecho → *Import Robot from Selected URDF file* y continuar.
- [ ] **Step 3: Sustituir en la escena:** poner el robot nuevo con el mismo transform/padre que el viejo; `ArticulationBody` de `base_link` → `Immovable = true`; volver a colgar la `Garra` del mismo link; borrar el robot viejo y el `RosConnector`; quitar componentes "Missing Script".
- [ ] **Step 4: Componentes nuevos:** `KinovaJointStateSubscriber` en el robot (`robotRoot` = robot nuevo); `KinovaPosePublisher` en el objeto del botón que tenía el publisher viejo, reasignando `RobotBaseTransform` (= `base_link` del robot nuevo), `RHand`, `RightHand`, `poseText`, y el `OnClick` del botón → `KinovaPosePublisher.OnButtonClick`.
- [ ] **Step 5: ROS Settings:** Protocol `ROS2`, `ROS IP Address` `127.0.0.1`, puerto `10000` (para el build de Quest 3 se cambia a la IP del PC; documentarlo en README).
- [ ] **Step 6: Verificación:** guardar escena; consola sin errores; con el MCP, buscar componentes "Missing" en la escena → 0.
- [ ] **Step 7: Commit** `feat(unity): wire ARM scene to ROS2 via ROS-TCP-Connector`

### Task 7: Prueba de extremo a extremo

- [ ] **Step 1: Sin robot:** WSL: `ros2 launch kinova_gen3_description display.launch.py fake:=true rviz:=false` y `ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0`. Unity (MCP): Play en `ARM.unity`. Esperado: el robot virtual oscila (leer con el MCP el `xDrive.target` de 2 joints en dos instantes distintos → valores diferentes); HUD de ROS-TCP-Connector en verde; consola sin errores.
- [ ] **Step 2: Nombres desconocidos (Review Focus 4):** con Play activo, `ros2 topic pub --once /joint_states sensor_msgs/msg/JointState "{name: [left_finger_joint, no_existe], position: [0.1, 0.2]}"`. Esperado: consola de Unity sin excepciones.
- [ ] **Step 3: Unity → ROS:** con Play activo, invocar por MCP `KinovaPosePublisher.OnButtonClick()` y en WSL `ros2 topic echo /controller --once`. Esperado: `position: {x: 0.5, y: 0.5, z: 0.5}`, `frame_id: base_link`. (Sin `kinova_controller` corriendo: no mueve nada.)
- [ ] **Step 4: Con robot (pedir permiso explícito antes de mover):** `ros2 launch kinova_mov kinova_unity.launch.py robot_ip:=192.168.1.10`. Esperado: el brazo va a `Home`, `/joint_states` a ~10 Hz (`ros2 topic hz`), el robot virtual imita al real. Luego, con permiso, `OnButtonClick` → el brazo se mueve a la pose Home de Unity y, **durante** el movimiento, `ros2 topic hz /joint_states` sigue ~10 Hz (Review Focus 3).
- [ ] **Step 5:** anotar resultados (pasó / pendiente / falló con salida) para el README y el resumen final.

### Task 8: README

**Files:**
- Modify: `README.md` (raíz, en español)

- [ ] **Step 1: Escribir**, en este orden:
  1. Qué es y estructura `ROS/` + `Unity/`.
  2. Preparar el PC: enlace a `docs/setup/wsl-ros2-unity-mcp.md` (WSL, Jazzy, Kortex API, MCP). Compilar: `cd ROS && vcs import src < ros2.repos && rosdep install --from-paths src -y --ignore-src && colcon build`. Arrancar: `ros2 launch kinova_mov kinova_unity.launch.py robot_ip:=192.168.1.10`. Prueba sin robot: `ros2 launch kinova_gen3_description display.launch.py fake:=true`. Notas Jazzy del Task 3 si hubo parche; resultado real de la instalación de Kortex (qué comandos funcionaron).
  3. Unity — lo que hizo la Task 6, como pasos manuales para quien no use el MCP: abrir `Unity/` con 2022.3.22f1 → esperar paquetes; clic derecho `Assets/URDF/urdf/GEN3.urdf` → *Import Robot from Selected URDF file* (*Axis Type* `Z Axis`, *Mesh Decomposer* `VHACD`); en `ARM.unity` borrar el robot viejo (Missing Scripts) y el `RosConnector`, colocar el nuevo en la misma posición, marcar `Immovable` en el `ArticulationBody` de `base_link`, volver a montar la `Garra`; *Robotics → ROS Settings*: Protocol `ROS2`, IP del PC con ROS, puerto `10000`; añadir `KinovaJointStateSubscriber` (robotRoot = robot) y `KinovaPosePublisher` en el objeto del botón (reasignar `RobotBaseTransform`, `RHand`, `RightHand`, `poseText`, y el `OnClick` del botón a `OnButtonClick`).
  4. Build para Quest 3: en *Robotics → ROS Settings* poner la IP del PC (no `127.0.0.1`) y la regla Hyper-V del setup doc.
  5. Resultados de la Task 7 (qué se probó y qué quedó pendiente).
- [ ] **Step 2: Commit** `docs: README for ROS2 + Unity setup` y `git push -u origin feat/ros2-unity-migration`. Preguntar al usuario si quiere fusionar a `main`.
