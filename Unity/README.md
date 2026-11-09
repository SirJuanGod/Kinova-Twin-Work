%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


## Project structure
This project is organized into two complementary repositories:

#### Kinova Unity Digital Twin:
contains the Unity-based XR digital twin of the Kinova Gen3 robotic arm, including hand-tracking interaction with Meta Quest 3, inverse kinematics control, ROS communication, and the NLP-based virtual assistant.

#### Kinova ROS2 Jazzy Integration (`../ROS`):
contains the ROS2 workspace for the Kinova Gen3 robotic arm: Kortex integration (`kinova_mov`), robot description and the ROS-TCP-Endpoint used by Unity.

Both live in the same repository; see the root `README.md` (Spanish) for the full setup.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


# Digital Twin of the Kinova Gen3 Robotic Arm (Unity + Quest 3 + ROS)

This repository contains the Unity project used to build an interactive **XR digital twin** of the **Kinova Gen3 robotic arm**, featuring real-time manipulation through **hand-tracking gestures** on the Meta Quest 3 and optional interaction through an **NLP-based virtual assistant**.

The system was designed for **educational and training purposes**, allowing students to safely explore robotics concepts without directly operating the physical robot.

## Used with the ROS2 Jazzy workspace in `../ROS` (WSL Ubuntu 24.04)

## Features

- **Full digital twin** of the Kinova Gen3 (URDF-based kinematics).
- **Real-time XR manipulation** using hand-tracking (grab → move → release).
- **Inverse kinematics control** for safe and intuitive manipulation.
- **External ROS integration** (bidirectional communication).
- **NLP virtual assistant** to guide users inside XR.
- **Tutorial spanish scene** with narrated instructions and an interactive onboarding system.


##  Versions

- Windows 11
- [**Unity** v2022.3.22f1](https://unity.com/download)
- [**Meta XR All-In-One**](https://assetstore.unity.com/packages/tools/integration/meta-xr-all-in-one-sdk-269657?srsltid=AfmBOoq_KGW-tMJ287MBGtIBhsgGdB6YfXydnOWB1-GvhpkA8cPBzRze)
- [**ROS–Unity Communication: ROS-TCP-Connector v0.7.0**](https://github.com/Unity-Technologies/ROS-TCP-Connector) (ROS2 protocol)
- [**URDF Importer v0.5.2**](https://github.com/Unity-Technologies/URDF-Importer)

### UNITY
  - Clone ```https://github.com/SirJuanGod/Kinova-Twin-Work.git```
  - In Unity Hub **Add project from disk** and select the `Unity` folder (Unity 2022.3.22f1).
  - ROS connection: *Robotics → ROS Settings* — Protocol `ROS2`, ROS IP Address `127.0.0.1` in the editor (the IP of the ROS PC for a Quest 3 build), port `10000`.
  - Scene `ARM`: `ROS/RosConnectorObject` has `KinovaPosePublisher` (pinch / Home button → `/controller`); `Models/GEN3` has `KinovaJointStateSubscriber` (`/joint_states` → joints).

## [Connect your Quest 3](https://www.meta.com/es-es/help/quest/509273027107091/?srsltid=AfmBOoo5QAeN4tBAfz2ILFViQ5oa-l1PmqJ-EigVzK4WY6tlB7oNnlto) to your pc and make sure [developer mode](https://developers.meta.com/horizon/documentation/native/android/mobile-device-setup/) in the Meta Account is active

