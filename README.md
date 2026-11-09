# Kinova-Twin-Work

Gemelo digital del brazo **Kinova Gen3** en **ROS2 Jazzy + Unity**. Es la
migración del proyecto original en ROS1 Noetic + ROS# (repositorios
`slrac03/kinova-ros-noetic-slrac` y `slrac03/Kinova-unity-digital-twin`).

```
Unity (Windows / Quest 3)                 ROS2 Jazzy (WSL Ubuntu 24.04)
 KinovaPosePublisher ── /controller ──►  ros_tcp_endpoint :10000 ──► kinova_controller ──► Kinova Gen3
 KinovaJointStateSubscriber ◄── /joint_states ───────────────────── (Kortex API, 10 Hz)    192.168.1.10
```

## Estructura

| Carpeta | Contenido |
|---|---|
| `ROS/` | Workspace de ROS2. `ros2.repos` trae ROS-TCP-Endpoint (rama `main-ros2`). |
| `ROS/src/kinova_mov` | Nodo `kinova_controller`: Kortex API → `/joint_states` + `kinova_current`; `/controller` (`PoseStamped`) → IK en el robot → movimiento. Launch `kinova_unity.launch.py`. |
| `ROS/src/kinova_gen3_description` | URDF, mallas, RViz2 y `fake_joint_states.py` (seno para probar sin el robot). |
| `Unity/` | Proyecto de Unity 2022.3.22f1 (Meta XR, ROS-TCP-Connector v0.7.0, URDF Importer v0.5.2). Escena `Assets/Scenes/ARM.unity`. |
| `docs/` | Spec, plan y la guía para preparar el PC. |

## 1. Preparar el PC

Sigue [`docs/setup/wsl-ros2-unity-mcp.md`](docs/setup/wsl-ros2-unity-mcp.md):
WSL Ubuntu 24.04 con red *mirrored*, ROS2 Jazzy, Kortex API y (opcional) el MCP
de Unity.

**Kortex API:** en este PC funcionó tal cual lo describe el §2.5 de esa guía:
el wheel `kortex_api-2.6.0.post3` con `--no-deps` y `protobuf==3.20.3`
(`python3 -c "import kortex_api"` sin errores en Python 3.12).

**Descubrimiento DDS en WSL mirrored:** el multicast no funciona, así que hay
que limitar el descubrimiento a la máquina local (con SUBNET, `talker` y
`listener` no se ven):

```bash
echo 'export ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST' >> ~/.bashrc
```

Unity sigue llegando al endpoint porque usa TCP, no DDS.

## 2. Compilar

```bash
cd ROS
vcs import src < ros2.repos
rosdep install --from-paths src -y --ignore-src
colcon build          # sin --symlink-install si el repo está en /mnt/c o /mnt/d
source install/setup.bash
```

ROS-TCP-Endpoint `main-ros2` (v0.7.0) compila y funciona en Jazzy **sin
parches**. Solo saca un aviso de setuptools (`script-dir` → `script_dir`),
que no afecta.

## 3. Arrancar

Con el robot:

```bash
ros2 launch kinova_mov kinova_unity.launch.py robot_ip:=192.168.1.10
# args: ros_ip (0.0.0.0), tcp_port (10000)
```

> ⚠️ Al arrancar, `kinova_controller` **mueve el brazo** a la acción `Home`.

Si el robot no responde, el nodo lo dice y termina en unos 5 s:
`[ERROR] … No se pudo conectar al robot en <ip>: timed out`, con código 1.

Sin robot (prueba de Unity):

```bash
ros2 launch kinova_gen3_description display.launch.py fake:=true   # rviz:=false para no abrir RViz2
ros2 run ros_tcp_endpoint default_server_endpoint --ros-args -p ROS_IP:=0.0.0.0
```

Parámetros de `kinova_controller`: `robot_ip` (192.168.1.10), `username` /
`password` (admin/admin), `publish_rate` (10.0 Hz), `home_action` (`Home`).

## 4. Unity

Abre `Unity/` en Unity Hub con **2022.3.22f1** y espera a que se importen los
paquetes. La escena `ARM` ya viene migrada. Si hay que rehacerla a mano (sin el
MCP), estos son los pasos que se siguieron:

1. **Importar el robot:** clic derecho en `Assets/URDF/urdf/GEN3.urdf` →
   *Import Robot from Selected URDF file*, con **Axis Type = `Y Axis`** y
   **Mesh Decomposer = `Unity`**.
   - `Y Axis` porque estas mallas STL ya están en Y-up. Con `Z Axis`, cada
     malla del brazo sale girada 90°.
   - `Unity` y no `VHACD`, porque VHACD sobrescribe las submallas visuales
     `bracelet_with_vision_link_1/_2.asset` y la importación falla con una
     `NullReferenceException`.
   - Con Windows en español, el importador puede crear materiales con coma
     decimal (`rgba-0,75294-…`). Bórralos y usa los de punto.
2. En `ARM`, borra el robot viejo `Models/GEN3` (el de ROS#, con "Missing
   Script") y pon el nuevo con el mismo padre y transform: `Models`, local
   (0.793, −0.919, −0.163).
   - En el `ArticulationBody` de `base_link`, marca **Immovable**.
   - Pasa a la raíz nueva el `Rigidbody` (cinemático, sin gravedad), el
     `BoxCollider` (trigger) y los hijos `ISDK_HandGrabInteraction` y `Sphere`.
     Reasigna en `Grabbable` / `HandGrabInteractable` / `GrabInteractable` /
     `HandGrabPose` las referencias al robot nuevo.
   - Pon el **`SphereCollider` de `Sphere` como trigger.** Si es sólido,
     envuelve los links y la física explota.
   - Vuelve a colgar la **Garra** (`2F-140_Assy_Open_20191022`) de
     `end_effector_link`, en local (−0.21, 0, 0), rotación (0, 0, 270),
     escala 0.001.
3. **Quita el componente `Controller`** que añade el importador (es un teleop
   por teclado que pisa los targets). En los `xDrive` de las articulaciones
   no fijas pon **stiffness 10000, damping 100, force limit 1000**; el
   importador los deja a 0 y el brazo cae.
4. *Robotics → ROS Settings*: Protocol **ROS2**, ROS IP Address `127.0.0.1`,
   puerto **10000**. El símbolo `ROS2` debe estar en *Player → Scripting
   Define Symbols* tanto de **Standalone** como de **Android**.
5. Componentes:
   - `KinovaJointStateSubscriber` en `Models/GEN3`, con `robotRoot` =
     `Models/GEN3`.
   - `KinovaPosePublisher` en `ROS/RosConnectorObject`; quítale antes los
     "Missing Script" de ROS#. Asigna `RobotBaseTransform` = `base_link`,
     `RHand` = `OVRHands/RightHand` (`Hand`) y `RightHand` = `OculusHand_R`.
     `poseText` puede quedar vacío.
   - `ManipulationCanvas/HomeButton` → *On Click* →
     `KinovaPosePublisher.OnButtonClick`.

`KinovaJointStateSubscriber` ignora los nombres de `/joint_states` que no
existen en el robot. `KinovaPosePublisher` publica en `/controller` la mano
derecha relativa a `base_link` en cada pinch (ROS FLU, orientación
identidad), y el botón Home publica (0.5, 0.5, 0.5).

## 5. Build para Quest 3

En *Robotics → ROS Settings* pon la **IP del PC con ROS** (no `127.0.0.1`).
Permite conexiones entrantes a WSL con la regla Hyper-V del §1.2 de la guía
de setup.

## 6. Estado de las pruebas (2026-11-08)

| Prueba | Resultado |
|---|---|
| `colcon build` de los 3 paquetes en Jazzy | ✅ |
| Tests unitarios `kinova_mov` (`make_joint_state`, 6 y 7 articulaciones) | ✅ 2 passed |
| `kinova_controller` con IP inalcanzable → `[ERROR]` con la IP, sin traceback, exit 1 | ✅ (~6 s) |
| `display.launch.py fake:=true` → `/joint_states` `joint_1..6` a 60 Hz, `/tf` | ✅ |
| `ros_tcp_endpoint` escuchando en 10000; el launch de Unity acepta `robot_ip/ros_ip/tcp_port` | ✅ |
| Scripts C# compilan (0 errores, mensajes en variante ROS2) | ✅ |
| Escena: 0 Missing Scripts; mallas del robot nuevo = las del original (error 0) | ✅ |
| Unity en Play recibe el seno: los `xDrive.target` cambian y las articulaciones lo siguen (≤ ~9° de retraso) | ✅ * |
| `/joint_states` con `[left_finger_joint, no_existe]` → sin errores en consola; `left_finger_joint` = 5.73° | ✅ * |
| `OnButtonClick` → `/controller`: `frame_id: base_link`, posición (0.5, 0.5, 0.5), orientación (0, 0, 0, 1) | ✅ * |
| Con el brazo real (Home, `/joint_states` a 10 Hz, mover con `/controller`, `/joint_states` sigue a 10 Hz durante el movimiento) | ⏳ **Pendiente**: el brazo no estaba en la red (no había interfaz en 192.168.1.x) |

\* Probado con un *harness* que ejecutaba en un solo proceso el endpoint TCP,
el seno y un suscriptor de `/controller`, porque dentro del sandbox de la
sesión de Claude Code el DDS entre procesos no funcionaba. El ajuste de
drives, `Controller` y `Sphere` se validó en caliente durante ese Play, y la
escena se guardó después con los mismos valores; tras guardarla no se ha
vuelto a entrar en Play. Fuera del sandbox, el DDS entre procesos sí
funciona con `LOCALHOST` (ver §1).
