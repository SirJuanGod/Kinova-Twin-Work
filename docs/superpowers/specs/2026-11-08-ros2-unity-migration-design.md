# Migración del gemelo digital Kinova Gen3: ROS1 Noetic → ROS2 Jazzy + Unity (ROS-TCP-Connector)

Fecha: 2026-11-08

## Objetivo

Llevar el gemelo digital del Kinova Gen3 (proyecto de referencia
`slrac03/kinova-ros-noetic-slrac` + `slrac03/Kinova-unity-digital-twin`) a
**ROS2 Jazzy**, con Unity conectado por **ROS-TCP-Connector / ROS-TCP-Endpoint**
en vez de ROS# + rosbridge. Todo el sistema vive en este repo:

- `Unity/`: el proyecto de Unity completo.
- `ROS/`: el workspace de ROS2 completo.

**Éxito:** con el brazo real en `192.168.1.10`, un solo `ros2 launch` deja a
Unity recibiendo `/joint_states` (el robot virtual sigue al real) y enviando
poses a `/controller` (el robot real se mueve con IK), igual que en ROS1.

## Lo que existe hoy (ROS1)

| Pieza | Qué hace |
|---|---|
| `kinova_mov/scripts/pruebas_api.py` | Nodo principal. Conecta por Kortex API (TCP), va a "Home", publica `/joint_states` (6 joints, rad) y `kinova_current` (String) a 10 Hz, escucha `/controller` (`PoseStamped`) → IK del robot → `ExecuteAction`. |
| `kinova_mov/scripts/utilities.py` | Conexión/sesión Kortex. |
| `kinova_mov/scripts/publishing_topics.py` | Copia vieja e incompleta del nodo. |
| `file_server` + `ros_sharp_communication.launch` | rosbridge (9090) para ROS#. |
| `kinova_gen3_urdf` | URDF, mallas, RViz, publicador de prueba (seno). |
| Unity `KinovaPublisher.cs` | Pinch mano derecha → pose relativa a la base → `/controller`. Botón "Home" con pose fija. |
| Unity escena `ARM.unity` | `JointStateSubscriber` de ROS# mueve los `ArticulationBody`; `RosConnector` a `ws://192.168.1.11:9090`. |

## Estructura final

```
Kinova-Twin-Work/
├── README.md
├── docs/superpowers/specs/…
├── Unity/                      Assets/, Packages/, ProjectSettings/, .gitignore, README.md
└── ROS/
    ├── ros2.repos              ROS-TCP-Endpoint (rama main-ros2), para vcstool
    └── src/
        ├── kinova_mov/                 ament_python
        │   ├── kinova_mov/kinova_controller.py
        │   ├── kinova_mov/utilities.py
        │   └── launch/kinova_unity.launch.py
        └── kinova_gen3_description/    ament_cmake
            ├── urdf/GEN3.urdf, meshes/, rviz/gen3.rviz
            ├── scripts/fake_joint_states.py
            └── launch/display.launch.py
```

## Parte ROS2

### `kinova_controller` (port de `pruebas_api.py`)

- `rclpy`, nodo `kinova_controller`.
- Parámetros (sustituyen argparse): `robot_ip` (`192.168.1.10`),
  `username` (`admin`), `password` (`admin`), `publish_rate` (10.0 Hz),
  `home_action` (`Home`).
- Al arrancar: conecta con `DeviceConnection.createTcpConnection`, pone
  `SINGLE_LEVEL_SERVOING`, ejecuta la acción `home_action`.
- Timer a `publish_rate`: `GetMeasuredJointAngles` + `ComputeForwardKinematics`
  → publica `/joint_states` (nombres `joint_1..N` según lo que reporte el robot,
  posiciones en rad) y `kinova_current` (mismo texto que hoy).
- Suscripción `/controller` (`geometry_msgs/PoseStamped`): misma lógica de
  `calc_ik` + `send_joint_angles` (posición del mensaje, orientación actual
  del robot, semilla = ángulos actuales, espera END/ABORT hasta 15 s).
- `MultiThreadedExecutor` con timer y suscripción en grupos de callback
  distintos, para que `/joint_states` siga publicándose mientras se mueve
  (equivalente al hilo por callback de rospy).
- Se elimina la comparación fija `ip == "192.168.1.10"`; si la conexión falla
  se registra el error y el nodo termina.
- Errores Kortex (`KServerException`) en IK o lectura: se registran, el nodo
  sigue vivo.

### `kinova_unity.launch.py`

Lanza `ros_tcp_endpoint` (`default_server_endpoint`, `ROS_IP` arg, por
defecto `0.0.0.0`, puerto 10000) y `kinova_controller` con `robot_ip` como
argumento.

### `kinova_gen3_description`

URDF y mallas copiadas; las rutas `package://kinova_gen3_urdf/` pasan a
`package://kinova_gen3_description/`. `display.launch.py` lanza
`robot_state_publisher` + RViz2 (opción `fake:=true` lanza
`fake_joint_states.py`, port del publicador de seno a 60 Hz).

### Fuera de alcance

`publishing_topics.py`, `file_server`, rosbridge, `devel/`/`build/`
commiteados, la carpeta `Kin/` (importación de Unity dentro del paquete ROS).

## Parte Unity

- Copiar `Assets/`, `Packages/`, `ProjectSettings/`, `.gitignore`, `README.md`.
  **No** se copian `TempAssembly.dll`, `survey/`,
  `cuestionario_validacion_revisado.csv`.
- `Packages/manifest.json`: **quitar** `com.siemens.ros-sharp` y añadir
  `com.unity.robotics.ros-tcp-connector`
  (`https://github.com/Unity-Technologies/ROS-TCP-Connector.git?path=/com.unity.robotics.ros-tcp-connector`)
  y `com.unity.robotics.urdf-importer`
  (`https://github.com/Unity-Technologies/URDF-Importer.git?path=/com.unity.robotics.urdf-importer`).
  Todo Unity queda en un solo stack (Unity Robotics Hub).
- **Modelo del robot:** se reimporta con el URDF Importer de Unity desde
  `Assets/URDF/urdf/GEN3.urdf` (ya es idéntico al de ROS y sus mallas están
  en `Assets/URDF/urdf/kinova_gen3_urdf/meshes/`, que es donde el importador
  resuelve `package://kinova_gen3_urdf/…`; no hace falta tocarlo). La
  importación se hace en el editor (clic derecho en `GEN3.urdf` → *Import
  Robot from Selected URDF file*, *Axis Type* = `Z Axis` porque el URDF es de
  ROS, *Mesh Decomposer* = `VHACD`) y la hace el usuario. Al quitar ROS#, el
  robot viejo de la escena queda con scripts faltantes: se borra y se pone el
  nuevo en su lugar, reasignando `RobotBaseTransform` y la pinza (`Garra`).
- Basura de ROS1 dentro de `Assets/URDF/` (`CMakeLists.txt`, `package.xml`,
  `launch/`, `rviz/`, `.vscode/`, `scripts/joint_state_pub.py`) se elimina: no
  la usa Unity.
- `Assets/URDF/scripts/KinovaPosePublisher.cs`: misma lógica que
  `KinovaPublisher.cs` (pinch → posición de la mano relativa a
  `RobotBaseTransform`, orientación identidad; botón Home con pose fija
  0.5/0.5/0.5), publicando `PoseStampedMsg` con `ROSConnection`. Conversión
  Unity→ROS con `To<FLU>()`.
- `Assets/URDF/scripts/KinovaJointStateSubscriber.cs`: suscribe
  `/joint_states`, busca cada `UrdfJoint` del robot importado por `jointName`
  y pone `xDrive.target` de su `ArticulationBody` en grados.
- `KinovaPublisher.cs` original se elimina (lo sustituye el nuevo).
- La escena no se edita a mano (YAML frágil); el README explica los pasos en
  el editor: reimportar el robot, quitar `RosConnector` y los componentes
  ROS# que queden como "Missing Script"; *Robotics → ROS Settings* → protocolo
  ROS2, IP del PC con ROS; añadir los dos componentes nuevos y reasignar
  referencias.
- No se porta nada de C# a Python: Unity (Quest 3 / Android) solo ejecuta C#,
  y la IK ya se calcula en el robot. IK local con numpy queda fuera de alcance.

## Riesgos

- ROS-TCP-Endpoint `main-ros2` está probado en Humble, no en Jazzy; puede
  necesitar un parche pequeño. Se verifica compilando.
- Sin editor de Unity aquí: los scripts C# no se compilan en este entorno y
  la reimportación del robot la hace el usuario. Hasta hacerla, la escena
  `ARM.unity` abre con el robot roto (scripts ROS# faltantes).
- Sin brazo real aquí: la conexión Kortex no se prueba; solo que el nodo
  arranca y falla limpio sin robot.

## Pruebas

- `colcon build` del workspace en Jazzy (si se puede instalar aquí).
- `fake_joint_states` publica en `/joint_states`.
- `kinova_controller` sin robot: registra error de conexión y termina sin traza
  sin manejar.
- Test unitario de la conversión ángulos (grados) → `JointState`.
- `ros_tcp_endpoint` arranca y escucha en 10000.
