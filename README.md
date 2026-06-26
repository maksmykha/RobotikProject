# RobotikProject

Im Rahmen der Robotik-Vorlesung im 4. Semester an der DHBW wurde eine vollständige industrielle Pick-&-Place-Simulation mit ROS2, Gazebo, MoveIt2 und YOLO entwickelt. Ziel des Projekts ist die automatisierte Erkennung, Verfolgung und Sortierung von Objekten auf einem Förderband mithilfe eines kollaborativen UR-Roboterarms.

Die gesamte Umgebung wurde in Gazebo Sim aufgebaut und umfasst:
- einen UR-Roboterarm,
- ein Tisch,
- virtuelle Kamerasysteme,
sowie unterschiedliche Ablagebereiche zur Sortierung der erkannten Objekte.

# Voraussetzungen

Getestet auf:

* Ubuntu 24.04
* ROS2 Jazzy
* Python 3.12

---

# Installation


## 1. Entwicklungswerkzeuge installieren

```bash
sudo apt install \
sudo apt install ros-jazzy-ros2-control ros-jazzy-ros2-controllers -y\
python3-colcon-common-extensions \
python3-rosdep \
python3-vcstool \
python3-venv \
python3-pip \
git \
wget \
curl -y
```

ROS Dependencies initialisieren:

```bash
sudo rosdep init
rosdep update
```

---

## 2. Repository klonen

```bash
cd ~/Dokumente

git clone https://github.com/maksmykha/RobotikProject.git
cd RobotikProject
```

Submodules laden:

```bash
git submodule update --init --recursive
```

---

## 3. Python Virtual Environment einrichten

Virtuelle Umgebung erstellen:

```bash
python3 -m venv .venv
```

Aktivieren:

```bash
source .venv/bin/activate
```

Prüfen:

```bash
which python
```

Die Ausgabe sollte auf:

```bash
RobotikProject/.venv/bin/python
```

zeigen.

---

## 4. ROS Umgebung laden

```bash
source /opt/ros/jazzy/setup.bash
```

Workspace bauen:

```bash
colcon build --symlink-install
```

Workspace sourcen:

```bash
source install/setup.bash
```

Optional dauerhaft:

```bash
echo "source ~/Dokumente/RobotikProject/install/setup.bash" >> ~/.bashrc
```

---

## 5. Python-Abhängigkeiten installieren

Wichtig für die Kombination aus ROS2 + Python Virtual Environment:

```bash
export PYTHONPATH=$VIRTUAL_ENV/lib/python3.12/site-packages:$PYTHONPATH
```

Pip aktualisieren:

```bash
pip install --upgrade pip
```

Benötigte Python-Libraries:

```bash
pip install typeguard
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install ultralytics
pip install numpy==1.26.4
pip install lap
```

Falls `lap` fehlschlägt:

```bash
pip install lapx
```

---


# Greifer steuern

Greifer öffnen (60 mm pro Finger):

```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  '{joint_names: [left_finger_joint, right_finger_joint], points: [{positions: [0.06, 0.06], time_from_start: {sec: 1}}]}'
```

Greifer schließen:

```bash
ros2 topic pub --once /gripper_controller/joint_trajectory trajectory_msgs/msg/JointTrajectory \
  '{joint_names: [left_finger_joint, right_finger_joint], points: [{positions: [0.0, 0.0], time_from_start: {sec: 1}}]}'
```

---

# Wichtige Links:

*Universal Robots ROS2 Driver*
https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver?utm_source=chatgpt.com
https://docs.universal-robots.com/Universal_Robots_ROS_Documentation/?utm_source=chatgpt.com


*Movelt 2*
https://moveit.picknik.ai/humble/?utm_source=chatgpt.com#


*YOLO ROS2*
https://github.com/mgonzs13/yolo_ros?utm_source=chatgpt.com


*Beispiel-Projekte / GitHub Suche*
https://github.com/marybayyouk/clair-pick-and-place-ros2
https://github.com/ninjamath3/ur5-simulation


*Gazebo Sim*
https://gazebosim.org/docs?utm_source=chatgpt.com
