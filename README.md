# RobotikProject – Pick-and-Place Simulation mit ROS2

Dieses Projekt wurde im Rahmen der Robotik-Vorlesung entwickelt. Ziel ist eine Pick-and-Place-Simulation mit einem UR-Roboterarm in Gazebo. Der Roboter erkennt farbige Würfel mit OpenCV, wählt ein gewünschtes Objekt aus, greift es virtuell über einen Magnet-Mechanismus und sortiert es in den passenden Ablagebereich.

## Projektziel

Der Roboter soll auf einen Befehl wie „sortiere den roten Würfel aus“ reagieren. Danach läuft automatisch folgender Ablauf:

1. Die Kamera erkennt farbige Würfel mit OpenCV.
2. Eine gewünschte Farbe wird über ein ROS2-Topic ausgewählt.
3. Die Pixelposition des Würfels wird in eine Weltkoordinate umgerechnet.
4. Der Pick-and-Place-Node plant eine Bewegungssequenz.
5. Der Roboter fährt zum Würfel.
6. Der Würfel wird virtuell magnetisiert.
7. Der Roboter transportiert den Würfel zum passenden Ablageort.
8. Der Würfel wird dort abgelegt.

## Verwendete Technologien

* Ubuntu 24.04
* ROS2 Jazzy
* Python 3.12
* Gazebo Sim
* ros2_control
* MoveIt-Konfiguration
* OpenCV
* cv_bridge
* UR-Roboterarm in Simulation

## Benötigte Pakete

Das Projekt wurde mit Ubuntu 24.04 und ROS2 Jazzy getestet.

### Systempakete installieren

```bash
sudo apt update
sudo apt install -y \
  git \
  wget \
  curl \
  python3-pip \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  python3-opencv \
  ros-jazzy-desktop \
  ros-jazzy-xacro \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-rviz2 \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-controller-manager \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-ros-gz \
  ros-jazzy-moveit \
  ros-jazzy-cv-bridge \
  ros-jazzy-image-transport \
  ros-jazzy-rqt-image-view \
  ros-jazzy-image-tools \
  ros-jazzy-tf2-tools \
  ros-jazzy-ur \
  ros-jazzy-ur-description
```

### Python-Pakete installieren

```bash
pip install opencv-python numpy
```

### rosdep verwenden

Falls noch Abhängigkeiten fehlen, können sie mit `rosdep` installiert werden:

```bash
cd ~/Documents/RobotikProject

sudo rosdep init 2>/dev/null || true
rosdep update

rosdep install --from-paths src --ignore-src -r -y
```

## Paketübersicht

```text
src/
├── robotik_gazebo          # Gazebo-Welt, Tisch, Würfel, Ablagebereiche, Kamera
├── robotik_vision          # OpenCV-Farberkennung und Zielkoordinaten
├── robotik_sorting         # Pick-and-Place-Algorithmus
├── robotik_control         # Controller-Konfiguration
├── robotik_description     # Roboterbeschreibung / URDF / Xacro
├── robotik_moveit_config   # MoveIt-Konfiguration
```

## Installation

Repository klonen:

```bash
cd ~/Documents
git clone https://github.com/maksmykha/RobotikProject.git
cd RobotikProject
```

ROS2-Umgebung laden:

```bash
source /opt/ros/jazzy/setup.bash
```

Workspace bauen:

```bash
colcon build --merge-install
source install/setup.bash
```

Falls bereits alte Build-Dateien vorhanden sind, kann der Workspace sauber neu gebaut werden:

```bash
rm -rf build install log

source /opt/ros/jazzy/setup.bash
colcon build --merge-install
source install/setup.bash
```

## Simulation starten

Für den Betrieb werden mehrere Terminals benötigt.

### Terminal 1: Gazebo starten

```bash
cd ~/Documents/RobotikProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 launch robotik_gazebo gazebo_world.launch.py
```

Danach warten, bis Gazebo vollständig geladen ist.

### Terminal 2: Vision starten

```bash
cd ~/Documents/RobotikProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run robotik_vision color_detector &
sleep 2
ros2 run robotik_vision manual_target_selector &
sleep 1
ros2 run robotik_vision target_pose
```

### Terminal 3: Pick-and-Place starten

```bash
cd ~/Documents/RobotikProject
source /opt/ros/jazzy/setup.bash
source install/setup.bash

ros2 run robotik_sorting pick_place
```

## Terminal 4: Bedienung

Eine Farbe kann über das Topic `/requested_color` angefordert werden.

### Gelben Würfel sortieren

```bash
ros2 topic pub /requested_color std_msgs/msg/String "data: 'yellow'" --once
```

### Roten Würfel sortieren

```bash
ros2 topic pub /requested_color std_msgs/msg/String "data: 'red'" --once
```

### Grünen Würfel sortieren

```bash
ros2 topic pub /requested_color std_msgs/msg/String "data: 'green'" --once
```

### Blauen Würfel sortieren

```bash
ros2 topic pub /requested_color std_msgs/msg/String "data: 'blue'" --once
```


Der Pick-and-Place-Node arbeitet immer nur ein Objekt gleichzeitig ab. Erst wenn der Status wieder `READY` ist, sollte der nächste Auftrag gesendet werden.

## Wichtige ROS2-Topics

```text
/color_detector/detections    # erkannte Objekte aus OpenCV
/requested_color              # gewünschte Farbe
/target_object                # ausgewähltes Objekt
/target_pose                  # Weltkoordinate des Zielobjekts
/pick_place/status            # Zustand des Pick-and-Place-Nodes
/joint_states                 # aktuelle Gelenkzustände
```

## Pick-and-Place-Ablauf

Der Algorithmus nutzt eine feste sichere Bewegungssequenz:

```text
HOME
→ APPROACH_PICK
→ DESCEND_PICK
→ Magnet EIN
→ LIFT
→ APPROACH_PLACE
→ DESCEND_PLACE
→ Magnet AUS
→ RETREAT
→ HOME
```

Dabei fährt der Roboter zuerst in eine sichere Startposition. Danach nähert er sich dem Würfel von oben, fährt zur Pick-Position, aktiviert den simulierten Magneten, hebt den Würfel an und transportiert ihn zum passenden Ablagebereich.

## Magnet-Simulation

Da kein echter Greifer verwendet wird, wird das Greifen durch einen Magnet-/Attach-Mechanismus simuliert.

Beim Greifen wird der Würfel virtuell an den Roboter gekoppelt. Während der Roboterarm fährt, folgt der Würfel dem berechneten Greiferbereich. Beim Ablageort wird die Kopplung gelöst und der Würfel wird im passenden Sortierbereich abgelegt.

## Farbsortierung

Die Würfel werden nach Farbe sortiert:

```text
red     → roter Ablagebereich
green   → grüner Ablagebereich
blue    → blauer Ablagebereich
yellow  → gelber Ablagebereich
```

Die Zielpositionen der Ablagebereiche sind im Pick-and-Place-Node hinterlegt.

## OpenCV-Erkennung

Die Objekterkennung erfolgt mit OpenCV. Der Vision-Teil erkennt farbige Würfel im Kamerabild und publiziert erkannte Objekte als Pixelpositionen. Danach wird aus der Pixelposition eine Weltkoordinate berechnet, die der Pick-and-Place-Node als Ziel verwendet.

Die Pipeline ist:

```text
Kamera
→ OpenCV-Farberkennung
→ erkannte Objekte
→ Auswahl nach gewünschter Farbe
→ Pixel-zu-Welt-Koordinate
→ Pick-and-Place
```

## Debugging

### Status beobachten

```bash
ros2 topic echo /pick_place/status
```

### Zielkoordinaten prüfen

```bash
ros2 topic echo /target_pose
```

Beispielausgabe:

```text
data: red,0.550,0.150,0.820,1441
```

### Erkannte Objekte prüfen

```bash
ros2 topic echo /color_detector/detections
```

### Ausgewähltes Zielobjekt prüfen

```bash
ros2 topic echo /target_object
```

### Controller prüfen

Aktive Controller anzeigen:

```bash
ros2 control list_controllers
```

Falls Controller nicht aktiv sind:

```bash
ros2 control load_controller --set-state active joint_state_broadcaster
ros2 control load_controller --set-state active arm_controller
```

Prüfen, ob der Trajectory-Controller verfügbar ist:

```bash
ros2 action list | grep trajectory
```

Erwartet wird:

```text
/arm_controller/follow_joint_trajectory
```

### Kamerabild prüfen

Falls `rqt_image_view` noch nicht installiert ist:

```bash
sudo apt install -y ros-jazzy-rqt-image-view
```

Kamera-Topics anzeigen:

```bash
ros2 topic list | grep image
```

Bild anzeigen:

```bash
ros2 run rqt_image_view rqt_image_view
```

Im Fenster das Kamera-Topic auswählen, zum Beispiel:

```text
/gripper_camera/image
```

Falls kein Bild sichtbar ist, alle Topics aus `ros2 topic list | grep image` ausprobieren.

## Manueller Arm-Test

Mit diesem Befehl kann geprüft werden, ob der Roboterarm über den Controller bewegt werden kann:

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory \
  '{
    trajectory: {
      joint_names: ["shoulder_pan_joint","shoulder_lift_joint","elbow_joint","wrist_1_joint","wrist_2_joint","wrist_3_joint"],
      points: [{
        positions: [0.0, -1.57, 0.0, -1.57, 0.0, 0.0],
        velocities: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        time_from_start: {sec: 5}
      }]
    }
  }'
```

Wenn der Arm in die Home-Position fährt, funktioniert der Controller.

## Manueller Pick-and-Place-Test ohne Kamera

Der Pick-and-Place-Node kann auch direkt ohne OpenCV getestet werden. Dazu wird ein Ziel manuell auf `/target_pose` publiziert.

### Roter Würfel

```bash
ros2 topic pub /target_pose std_msgs/msg/String \
"data: 'red,0.55,0.15,0.82,1400'" --once
```

### Grüner Würfel

```bash
ros2 topic pub /target_pose std_msgs/msg/String \
"data: 'green,0.25,0.15,0.82,1400'" --once
```

### Blauer Würfel

```bash
ros2 topic pub /target_pose std_msgs/msg/String \
"data: 'blue,0.55,-0.15,0.82,1400'" --once
```

### Gelber Würfel

```bash
ros2 topic pub /target_pose std_msgs/msg/String \
"data: 'yellow,0.25,-0.15,0.82,1400'" --once
```

## TF prüfen

TF-Frames anzeigen:

```bash
ros2 topic list | grep tf
```

Einmalige TF-Ausgabe:

```bash
ros2 topic echo /tf --once
ros2 topic echo /tf_static --once
```

Frames als PDF erzeugen:

```bash
ros2 run tf2_tools view_frames
```

Beispiel für einen TF-Check:

```bash
ros2 run tf2_ros tf2_echo world tool0
```

## Typische Fehler und Lösungen

### Workspace wurde früher mit anderem Install-Layout gebaut

Fehlermeldung:

```text
The install directory 'install' was created with the layout 'merged'
```

Lösung:

```bash
colcon build --merge-install
```

Oder komplett sauber neu bauen:

```bash
rm -rf build install log
source /opt/ros/jazzy/setup.bash
colcon build --merge-install
source install/setup.bash
```

### Pick-and-Place-Node startet, aber Roboter bewegt sich nicht

Controller prüfen:

```bash
ros2 action list | grep trajectory
```

Falls `/arm_controller/follow_joint_trajectory` nicht erscheint, ist der Arm-Controller noch nicht aktiv oder Gazebo ist nicht vollständig gestartet.

### Objekt wird leicht ungenau gegriffen

Die Pick-Position kann pro Farbe leicht kalibriert werden. Dafür befinden sich im Pick-and-Place-Node Pick-Offsets. Damit können kleine Abweichungen zwischen Kamera, Weltkoordinaten und simulierter Greiferposition korrigiert werden.

### Kein Kamerabild sichtbar

Kamera-Topics prüfen:

```bash
ros2 topic list | grep camera
ros2 topic list | grep image
```

Danach mit `rqt_image_view` das passende Topic auswählen:

```bash
ros2 run rqt_image_view rqt_image_view
```

## Bekannte Einschränkungen

* Der Greifer ist kein physischer Greifer, sondern wird durch einen Magnet-/Attach-Mechanismus simuliert.
* Die Pick-Position kann je nach Farbe leicht kalibriert werden.
* Die aktuelle Simulation ist für eine stabile Demo optimiert.
* Die Kinematik im Pick-and-Place-Node ist für die Projekt-Demo ausgelegt und kein vollständiger industrieller Robotercontroller.

## Projektstatus

Aktuell funktioniert:

* Gazebo-Simulation
* OpenCV-Farberkennung
* Farbauswahl über ROS2-Topic
* Umrechnung von Pixelkoordinaten in Weltkoordinaten
* Bewegung des UR-Roboterarms
* Virtuelles Greifen über Magnet-Simulation
* Ablegen der Würfel in Sortierbereichen
* Sortierung nach Farbe
* Manueller Test über `/target_pose`
* Automatischer Test über `/requested_color`

## Projekt sauber neu bauen

Nach größeren Änderungen sollte immer ein sauberer Build durchgeführt werden:

```bash
cd ~/Documents/RobotikProject

rm -rf build install log

source /opt/ros/jazzy/setup.bash
colcon build --merge-install
source install/setup.bash
```

## Autoren

RobotikProject – Pick-and-Place Simulation mit ROS2, Gazebo und OpenCV.
