# Preparar el PC: WSL + ROS2 Jazzy + MCP de Unity + Claude Code

Objetivo: que Claude Code corra **dentro de WSL** (Ubuntu 24.04 con ROS2 Jazzy)
y pueda controlar **Unity en Windows** a través del MCP de Unity
([MCP for Unity, CoplayDev](https://github.com/CoplayDev/unity-mcp)).

```
Windows ─────────────────────────────┐      WSL (Ubuntu 24.04) ───────────────┐
 Unity 2022.3.22f1                   │       ROS2 Jazzy                       │
  ├─ MCP for Unity  :8080 ◄──────────┼────── Claude Code (claude)             │
  └─ ROS-TCP-Connector ──────────────┼────► ros_tcp_endpoint :10000           │
                                     │       kinova_controller ──► 192.168.1.10 (brazo)
```

Con **red mirrored** de WSL, Windows y WSL se ven por `127.0.0.1` y WSL ve
la red del brazo directamente. Es lo que se usa aquí.

Fuentes: docs.ros.org (Jazzy, Ubuntu debs), learn.microsoft.com (WSL
networking), coplaydev.github.io/unity-mcp (install + troubleshooting WSL2).

---

## Parte 1 — Windows (PowerShell como administrador)

### 1.1 Instalar Ubuntu 24.04 en WSL

Jazzy solo tiene paquetes para **Ubuntu 24.04 (Noble)**.

```powershell
wsl --update
wsl --install -d Ubuntu-24.04
```

Crea tu usuario Linux cuando lo pida.

### 1.2 Activar red mirrored (requiere Windows 11 22H2 o superior)

Crea o edita `C:\Users\<TU_USUARIO>\.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

Permite conexiones entrantes a WSL (necesario para que las Quest 3 lleguen al
endpoint de ROS en el puerto 10000):

```powershell
Set-NetFirewallHyperVVMSetting -Name '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -DefaultInboundAction Allow
```

Aplica los cambios:

```powershell
wsl --shutdown
```

> Si tienes Windows 10 (sin mirrored), mira el **Anexo A** al final.

### 1.3 Instalar `uv` (lo necesita el servidor del MCP de Unity)

```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

También necesitas **git** en Windows (el Package Manager de Unity lo usa para
paquetes por URL): <https://git-scm.com/download/win>.

---

## Parte 2 — WSL: ROS2 Jazzy

Abre la terminal de Ubuntu 24.04 y ejecuta en orden.

### 2.1 Locale

```bash
locale  # comprobar UTF-8
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### 2.2 Repositorios

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe

sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F'"' '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

Comprueba que `noble-updates` y `noble-backports` estén en las fuentes (si no,
`ros-dev-tools` da conflictos):

```bash
grep Suites /etc/apt/sources.list.d/ubuntu.sources
# debe decir: Suites: noble noble-updates noble-backports
# si no, edita el archivo y luego:
# sudo apt clean && sudo apt update && sudo apt full-upgrade -y
```

### 2.3 Instalar ROS2 Jazzy + herramientas

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ros-dev-tools ros-jazzy-desktop
sudo rosdep init
rosdep update
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 2.4 Probar

Terminal 1: `ros2 run demo_nodes_cpp talker` · Terminal 2:
`ros2 run demo_nodes_py listener` → debe imprimir `I heard: ...`.

### 2.5 Kortex API (Python) para el brazo

El nodo `kinova_controller` usa la Kortex API 2.6 de Kinova. Ubuntu 24.04
trae Python 3.12 y el wheel pide un `protobuf` muy viejo, así que se instala
sin dependencias y con un protobuf 3.20:

```bash
cd ~ && curl -LO https://artifactory.kinovaapps.com/artifactory/generic-public/kortex/API/2.6.0/kortex_api-2.6.0.post3-py3-none-any.whl
pip install --break-system-packages --no-deps ./kortex_api-2.6.0.post3-py3-none-any.whl
pip install --break-system-packages "protobuf==3.20.3"
python3 -c "from kortex_api.autogen.client_stubs.BaseClientRpc import BaseClient; print('kortex OK')"
```

> ⚠️ Esto no se pudo probar en la sesión anterior (servidor de Kinova bloqueado).
> Si el `python3 -c` falla, prueba con
> `export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python` y, si sigue fallando,
> la sesión de Claude lo resuelve (está en el plan, Task 2).

### 2.6 Red hacia el brazo

Pon la tarjeta Ethernet de **Windows** conectada al brazo en `192.168.1.X`
(p. ej. `192.168.1.11`, máscara `255.255.255.0`). Con red mirrored WSL la usa
tal cual:

```bash
ping -c 3 192.168.1.10
```

---

## Parte 3 — WSL: Claude Code y el repo

```bash
curl -fsSL https://claude.ai/install.sh | bash
claude doctor

sudo apt install -y git
```

**Un solo clon, en el disco de Windows** (Unity no trabaja bien con proyectos
en rutas `\\wsl$`). Desde WSL se ve en `/mnt/c/...`:

```bash
cd /mnt/c/Users/<TU_USUARIO_WINDOWS>
git clone https://github.com/SirJuanGod/Kinova-Twin-Work.git
cd Kinova-Twin-Work
git config core.autocrlf input   # evita cambios de fin de línea entre Windows y WSL
```

En Unity Hub: *Add → Add project from disk* →
`C:\Users\<TU_USUARIO_WINDOWS>\Kinova-Twin-Work\Unity`.

> colcon en `/mnt/c` es algo más lento; el workspace es pequeño, así que va
> bien. No uses `--symlink-install` ahí.

---

## Parte 4 — MCP de Unity

El proyecto `Unity/` del repo aparece cuando Claude termina la **Task 4** del
plan. Esa tarea también añade el paquete del MCP (`com.coplaydev.unity-mcp`,
`v10.3.0`) al `manifest.json`, así que **no hay que instalarlo a mano** en
este proyecto. Lo que sí haces ahora es registrar el MCP en Claude Code:

### 4.1 Registrar el MCP en Claude Code (en WSL, ahora)

```bash
cd /mnt/c/Users/<TU_USUARIO_WINDOWS>/Kinova-Twin-Work
claude mcp add --transport http UnityMCP http://127.0.0.1:8080/mcp
```

(Si en Unity usas otro puerto, p. ej. 8090 porque el 8080 está ocupado,
cámbialo aquí también.) Hasta que Unity esté abierto saldrá desconectado: es
normal.

### 4.2 Cuando Claude te lo pida (tras la Task 4)

1. Unity Hub → *Add → Add project from disk* →
   `C:\Users\<TU_USUARIO_WINDOWS>\Kinova-Twin-Work\Unity` → abrir con
   **Unity 2022.3.22f1**. Espera a que importe los paquetes (la escena
   `ARM.unity` mostrará el robot con "Missing Script": es esperado, Claude lo
   rehace después).
2. Se abre el asistente de MCP for Unity: **Python 3.10+** y **uv** en verde →
   **Done**. No uses "Configure All Detected Clients" (detecta clientes de
   Windows; Claude Code está en WSL y ya lo registraste en 4.1).
3. *Window → MCP for Unity*: transporte **HTTP**, puerto **8080** → **Start
   Server**. El panel debe decir `Connected`.
4. En Claude Code escribe `/mcp` y reconecta `UnityMCP`. Desde WSL puedes
   comprobar con `claude mcp list` (debe salir conectado).

### 4.3 (Opcional) Probar el MCP antes

Si quieres comprobarlo ya, crea un proyecto vacío de Unity, añade el paquete
por *Window → Package Manager → + → Add package from git URL…*:

```text
https://github.com/CoplayDev/unity-mcp.git?path=/MCPForUnity#v10.3.0
```

arranca el servidor (paso 4.2.3), abre `claude` en WSL y pide: *"Usa el MCP de
Unity y dime qué objetos hay en la escena abierta."* Cierra ese proyecto
antes de seguir (el MCP se confunde con dos editores abiertos).

---

## Parte 5 — Arrancar la sesión de implementación

1. En WSL:
   ```bash
   cd /mnt/c/Users/<TU_USUARIO_WINDOWS>/Kinova-Twin-Work
   git checkout main && git pull
   claude
   ```
2. Pega el prompt de `docs/superpowers/NEXT_SESSION_PROMPT.md`.

---

## Anexo A — Sin red mirrored (Windows 10 / NAT)

Guía oficial de MCP for Unity para WSL2 en modo NAT:

1. En *Window → MCP for Unity* cambia el puerto a **8090**.
2. PowerShell admin:
   ```powershell
   netsh interface portproxy add v4tov4 listenport=8090 listenaddress=0.0.0.0 connectport=8090 connectaddress=127.0.0.1
   New-NetFirewallRule -DisplayName "Unity MCP Server" -Direction Inbound -LocalPort 8090 -Protocol TCP -Action Allow
   ```
3. En WSL, IP de Windows: `cat /etc/resolv.conf | grep nameserver | awk '{print $2}'`
4. `claude mcp add --transport http UnityMCP http://<ESA_IP>:8090/mcp`

En NAT, Unity (Windows) llega al endpoint ROS de WSL por `localhost:10000`,
pero el brazo (`192.168.1.10`) y las Quest 3 **no** ven WSL directamente:
hay que hacer otro `portproxy` para el 10000 y el brazo puede no ser
alcanzable desde WSL. Por eso se recomienda mirrored.

## Anexo B — Problemas comunes

| Síntoma | Arreglo |
|---|---|
| `Error when executing git command` en Package Manager | Instalar git en Windows y reiniciar Unity Hub. |
| `claude mcp list` → UnityMCP falla | Unity abierto, servidor en *Start*, mismo puerto; `curl -s http://127.0.0.1:8080/mcp` desde WSL debe responder algo (no "connection refused"). |
| Cambiaste HTTP↔stdio en el panel | Reinicia Claude Code. |
| `ros-dev-tools` con conflictos | Paso 2.2: añadir `noble-updates noble-backports`. |
| Quest 3 no conecta al 10000 | Regla Hyper-V del paso 1.2; IP del PC en *Robotics → ROS Settings*. |
