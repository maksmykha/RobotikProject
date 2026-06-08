# Useful Commands
---

# Daily Workflow

Diese Reihenfolge wird normalerweise genutzt:

1. Workspace öffnen
2. ROS + Python sourcen
3. Workspace bauen
4. Gazebo starten
5. Kamera Bridge starten
6. Kamera testen
7. YOLO prüfen
8. Debugging

---

# 1. Workspace öffnen

```bash
cd ~/Dokumente/RobotikProject
```

---

# 2. ROS + Python Environment laden (WICHTIG)

**Immer zuerst ausführen.**

```bash
source /opt/ros/jazzy/setup.bash
source .venv/bin/activate
source install/setup.bash

export PYTHONPATH=$VIRTUAL_ENV/lib/python3.12/site-packages:$PYTHONPATH
```

Prüfen:

```bash
which python
```

Sollte auf:

```txt
RobotikProject/.venv/bin/python
```

zeigen.

---

# 3. Workspace bauen

## Normal Build

Nach Codeänderungen:

```bash
colcon build --symlink-install
source install/setup.bash
```

## Clean Build

Falls Packages kaputt sind:

```bash
rm -rf build install log

colcon build --symlink-install

source install/setup.bash
```

---

# 4. Projekt starten

## Gazebo starten

```bash
ros2 launch robotik_gazebo gazebo_world.launch.py
```

Alternative:

```bash
gz sim worlds/pick_place_world.sdf
```

---


# 5. Kamera testen

## Kamera Topics prüfen

```bash
ros2 topic list | grep camera
```

## Bildtopic prüfen

```bash
ros2 topic echo /gripper_camera/image --once
```

## Kamerabild anzeigen

```bash
ros2 run rqt_image_view rqt_image_view
```

---

# 7. YOLO prüfen

## YOLO Topics anzeigen

```bash
ros2 topic list | grep yolo
```

## Detections prüfen

```bash
ros2 topic echo /yolo/detections
```

## Tracking prüfen

```bash
ros2 topic echo /yolo/tracking
```

## YOLO Bild prüfen

```bash
ros2 topic echo /yolo/dbg_image
```

---

# 8. Häufiges Debugging

## Topics anzeigen

```bash
ros2 topic list
```

## Nodes anzeigen

```bash
ros2 node list
```

## Topic Infos

```bash
ros2 topic info /topic_name
```

## Topic Frequenz prüfen

```bash
ros2 topic hz /topic_name
```

## Topic beobachten

```bash
ros2 topic echo /topic_name
```

---

# TF Debugging

## TF Topics

```bash
ros2 topic list | grep tf
```

## Einzelne TF Nachricht

```bash
ros2 topic echo /tf --once
```

## Statische TF

```bash
ros2 topic echo /tf_static --once
```

## Frames visualisieren

```bash
ros2 run tf2_tools view_frames
```

## Transformation prüfen

```bash
ros2 run tf2_ros tf2_echo world tool0
```

---

# RViz

## Start

```bash
rviz2
```

## UR5e anzeigen

```bash
ros2 launch robotik_description view_ur5e.launch.py
```

### Wichtige Einstellungen

```txt
Fixed Frame:
world

Add → RobotModel
Add → TF
```

---

# Gazebo

## Simulation starten

```bash
gz sim
```

## Welt direkt öffnen

```bash
gz sim worlds/pick_place_world.sdf
```

## Launchfile starten

```bash
ros2 launch robotik_gazebo gazebo_world.launch.py
```

---

# UR5e

## UR Pakete prüfen

```bash
ros2 pkg list | grep ur_
```

## UR5e Modell anzeigen

```bash
ros2 launch ur_description view_ur.launch.py ur_type:=ur5e
```

---

# Test Nodes

## Vision Test Node

```bash
ros2 run robotik_vision test_node
```

---

# ROS2 Basics

## Topics

```bash
ros2 topic list
```

## Nodes

```bash
ros2 node list
```

## Packages

```bash
ros2 pkg list
```

## Services

```bash
ros2 service list
```

## Actions

```bash
ros2 action list
```

---

# Häufige Fehler

## `ModuleNotFoundError`

Venv vergessen:

```bash
source .venv/bin/activate
```

oder:

```bash
export PYTHONPATH=$VIRTUAL_ENV/lib/python3.12/site-packages:$PYTHONPATH
```

---

## Package nicht gefunden

Workspace nicht gesourced:

```bash
source install/setup.bash
```

---

## YOLO erkennt nichts

Prüfen:

```bash
ros2 topic list | grep yolo
```

und:

```bash
ros2 topic echo /gripper_camera/image --once
```

Wenn kein Bildtopic kommt:

* Kamera prüfen
* Bridge prüfen
* Gazebo prüfen

---

## Änderungen werden nicht übernommen

Neu bauen:

```bash
colcon build --symlink-install
source install/setup.bash
```
