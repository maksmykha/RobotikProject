import math
import subprocess
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

import rclpy
from builtin_interfaces.msg import Duration
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import String
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint


@dataclass
class Target:
    color: str
    x: float
    y: float
    z: float
    area: int = 0


class PickPlaceNode(Node):
    # UR5e-nahe Laengen; dieselben Werte wurden schon im alten Tracking benutzt.
    L1 = 0.425
    L2 = 0.3922
    SHOULDER_Z = 0.97

    # Tuning-Werte fuer Simulation.
    # Falls der Magnet zu hoch/tief ist: zuerst PICK_Z_OFFSET anpassen.
    PICK_Z_OFFSET = 0.08       # target.z ist Wuerfel-Mitte; TCP soll ueber den Wuerfel
    APPROACH_HEIGHT = 0.18     # Sicherheitsabstand ueber Pick/Place
    LIFT_HEIGHT = 0.23         # Hoehe nach dem Greifen
    PLACE_Z_OFFSET = 0.11      # TCP-Hoehe ueber Ablagepunkt vor dem Loslassen
    TRACK_PERIOD = 0.08

    # Joint-Grenzen grob absichern, damit IK keine unsinnigen Ziele sendet.
    JOINT_LIMITS = [
        (-math.pi, math.pi),        # shoulder_pan
        (-2.6, 0.4),                # shoulder_lift
        (-0.2, 2.8),                # elbow
        (-3.2, 0.3),                # wrist_1
        (-2.2, 0.2),                # wrist_2
        (-math.pi, math.pi),        # wrist_3
    ]

    def __init__(self):
        super().__init__("pick_place_node")
        cb = ReentrantCallbackGroup()

        self._jnames = [
            "shoulder_pan_joint",
            "shoulder_lift_joint",
            "elbow_joint",
            "wrist_1_joint",
            "wrist_2_joint",
            "wrist_3_joint",
        ]

        self._ac = ActionClient(
            self,
            FollowJointTrajectory,
            "/arm_controller/follow_joint_trajectory",
            callback_group=cb,
        )

        self.create_subscription(String, "/target_pose", self._on_target, 10, callback_group=cb)
        self.create_subscription(JointState, "/joint_states", self._on_joints, 10, callback_group=cb)
        self._status_pub = self.create_publisher(String, "/pick_place/status", 10)

        self._bins: Dict[str, Tuple[float, float, float]] = {
            "red": (-0.40, 0.20, 0.83),
            "green": (-0.75, 0.20, 0.83),
            "blue": (-0.75, -0.20, 0.83),
            "yellow": (-0.40, -0.20, 0.83),
        }

        self._home = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]
        self._joints = list(self._home)
        self._state = "IDLE"
        self._target: Optional[Target] = None
        self._cube_attached = False
        self._step_index = 0
        self._program: List[Tuple[str, List[float], Optional[Callable[[], None]]]] = []

        self.create_timer(self.TRACK_PERIOD, self._track_attached_cube, callback_group=cb)
        self._status("READY")
        self.get_logger().info("Pick & Place Node bereit: dynamische Zielpositionen aktiv.")

    # ------------------------- ROS callbacks -------------------------

    def _on_joints(self, msg: JointState) -> None:
        jmap = dict(zip(msg.name, msg.position))
        for i, name in enumerate(self._jnames):
            if name in jmap:
                self._joints[i] = float(jmap[name])

    def _on_target(self, msg: String) -> None:
        if self._state != "IDLE":
            self.get_logger().warn(f"Ignoriere Ziel, Roboter ist busy: {msg.data}")
            return

        target = self._parse_target(msg.data)
        if target is None:
            return
        if target.color not in self._bins:
            self.get_logger().warn(f"Unbekannte Farbe: {target.color}")
            return

        try:
            self._program = self._build_program(target)
        except ValueError as exc:
            self.get_logger().error(f"Kann Programm nicht erstellen: {exc}")
            self._status("ERROR_IK")
            self._status("READY")
            return

        self._target = target
        self._cube_attached = False
        self._state = "BUSY"
        self._step_index = 0

        self.get_logger().info(
            f"=== Pick & Place: {target.color} bei "
            f"x={target.x:.3f}, y={target.y:.3f}, z={target.z:.3f} ==="
        )
        self._status(f"PICKING {target.color}")
        self._run_next_step()

    # ------------------------- Programm / Algorithmus -------------------------

    def _build_program(self, t: Target) -> List[Tuple[str, List[float], Optional[Callable[[], None]]]]:
        pick_z = t.z + self.PICK_Z_OFFSET
        pick_approach_z = pick_z + self.APPROACH_HEIGHT
        lift_z = pick_z + self.LIFT_HEIGHT

        bx, by, bz = self._bins[t.color]
        place_z = bz + self.PLACE_Z_OFFSET
        place_approach_z = place_z + self.APPROACH_HEIGHT

        return [
            ("HOME", self._home, None),
            ("APPROACH_PICK", self._ik(t.x, t.y, pick_approach_z), None),
            ("DESCEND_PICK", self._ik(t.x, t.y, pick_z), self._attach_cube),
            ("LIFT", self._ik(t.x, t.y, lift_z), None),
            ("APPROACH_PLACE", self._ik(bx, by, place_approach_z), None),
            ("DESCEND_PLACE", self._ik(bx, by, place_z), self._release_cube),
            ("RETREAT", self._ik(bx, by, place_approach_z), None),
            ("HOME", self._home, self._finish),
        ]

    def _run_next_step(self) -> None:
        if self._step_index >= len(self._program):
            self._finish()
            return

        name, joints, after_motion = self._program[self._step_index]
        self._step_index += 1
        self._status(name)
        self._move(joints, name, after_motion)

    def _attach_cube(self) -> None:
        if not self._target:
            return
        self.get_logger().info(f"Magnet EIN: obj_{self._target.color}")
        self._cube_attached = True
        # Sofort an TCP ziehen, damit der Wuerfel nicht hinterherhinkt.
        self._track_attached_cube()
        self._status(f"TRANSPORTING {self._target.color}")

    def _release_cube(self) -> None:
        if not self._target:
            return
        color = self._target.color
        self.get_logger().info(f"Magnet AUS: obj_{color}")
        self._cube_attached = False
        bx, by, bz = self._bins[color]
        # Finale Ablage exakt im Bin, damit die Demo stabil aussieht.
        self._set_pose(f"obj_{color}", bx, by, bz)
        self._status(f"PLACED {color}")

    def _finish(self) -> None:
        self.get_logger().info("=== Pick & Place fertig ===")
        self._cube_attached = False
        self._target = None
        self._program = []
        self._state = "IDLE"
        self._status("READY")

    # ------------------------- Bewegung -------------------------

    def _move(
        self,
        positions: List[float],
        step_name: str,
        after_motion: Optional[Callable[[], None]],
    ) -> None:
        duration = self._estimate_duration(self._joints, positions)

        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = self._jnames

        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in positions]
        point.velocities = [0.0] * 6
        point.accelerations = [0.0] * 6
        point.time_from_start = Duration(sec=int(duration), nanosec=int((duration % 1.0) * 1e9))
        goal.trajectory.points = [point]

        if not self._ac.wait_for_server(timeout_sec=2.0):
            self.get_logger().error("arm_controller/follow_joint_trajectory nicht erreichbar")
            self._abort()
            return

        future = self._ac.send_goal_async(goal)
        future.add_done_callback(lambda f: self._on_goal_response(f, step_name, after_motion))

    def _on_goal_response(self, future, step_name: str, after_motion: Optional[Callable[[], None]]) -> None:
        try:
            goal_handle = future.result()
        except Exception as exc:
            self.get_logger().error(f"Goal Fehler bei {step_name}: {exc}")
            self._abort()
            return

        if not goal_handle.accepted:
            self.get_logger().error(f"Goal abgelehnt: {step_name}")
            self._abort()
            return

        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda f: self._on_motion_done(f, step_name, after_motion))

    def _on_motion_done(self, future, step_name: str, after_motion: Optional[Callable[[], None]]) -> None:
        try:
            _ = future.result()
        except Exception as exc:
            self.get_logger().error(f"Bewegung fehlgeschlagen bei {step_name}: {exc}")
            self._abort()
            return

        self.get_logger().info(f"Step fertig: {step_name}")
        if after_motion is not None:
            after_motion()
        self._run_next_step()

    def _abort(self) -> None:
        self._cube_attached = False
        self._target = None
        self._program = []
        self._state = "IDLE"
        self._status("ERROR")
        self._status("READY")

    def _estimate_duration(self, current: List[float], target: List[float]) -> float:
        max_delta = max(abs(a - b) for a, b in zip(current, target))
        # Langsam genug fuer Gazebo/Controller; aber nicht ewig.
        return max(2.5, min(7.0, max_delta / 0.55 + 1.5))

    # ------------------------- IK / FK -------------------------

    def _ik(self, x: float, y: float, z: float) -> List[float]:
        """
        Einfache 3D->Joint Naeherung fuer eure Demo.
        Sie ist kein vollstaendiger UR5e-IK-Solver, aber passt zu eurem bisherigen FK-Tracking.
        """
        r = math.hypot(x, y)
        dz = self.SHOULDER_Z - z

        # Workspace pruefen.
        dist = math.hypot(r, dz)
        if dist > (self.L1 + self.L2 - 0.02) or dist < abs(self.L1 - self.L2) + 0.02:
            raise ValueError(f"Ziel ausserhalb Workspace: x={x:.3f}, y={y:.3f}, z={z:.3f}")

        cos_elbow = (r * r + dz * dz - self.L1 * self.L1 - self.L2 * self.L2) / (2.0 * self.L1 * self.L2)
        cos_elbow = max(-1.0, min(1.0, cos_elbow))

        elbow = math.acos(cos_elbow)
        shoulder = math.atan2(dz, r) - math.atan2(
            self.L2 * math.sin(elbow),
            self.L1 + self.L2 * math.cos(elbow),
        )
        pan = math.atan2(y, x)

        # TCP nach unten ausrichten, aehnlich wie eure alten Pick-Joints.
        wrist_1 = -shoulder - elbow - math.pi / 2.0
        wrist_2 = -math.pi / 2.0
        wrist_3 = 0.0

        joints = [pan, shoulder, elbow, wrist_1, wrist_2, wrist_3]
        return self._clamp_joints(joints)

    def _clamp_joints(self, joints: List[float]) -> List[float]:
        clamped = []
        for value, (lo, hi) in zip(joints, self.JOINT_LIMITS):
            clamped.append(max(lo, min(hi, value)))
        return clamped

    def _tcp_estimate(self) -> Tuple[float, float, float]:
        pan, shoulder, elbow = self._joints[0], self._joints[1], self._joints[2]
        r = self.L1 * math.cos(shoulder) + self.L2 * math.cos(shoulder + elbow)
        x = r * math.cos(pan)
        y = r * math.sin(pan)
        z = self.SHOULDER_Z - self.L1 * math.sin(shoulder) - self.L2 * math.sin(shoulder + elbow)
        return x, y, z

    def _track_attached_cube(self) -> None:
        if not self._cube_attached or self._target is None:
            return
        x, y, z = self._tcp_estimate()
        # Der Wuerfel sitzt unter dem Magnet/TCP.
        self._set_pose(f"obj_{self._target.color}", x, y, z - self.PICK_Z_OFFSET)

    # ------------------------- Gazebo / Utils -------------------------

    def _set_pose(self, model_name: str, x: float, y: float, z: float) -> None:
        cmd = [
            "gz",
            "service",
            "-s",
            "/world/pick_place_world/set_pose",
            "--reqtype",
            "gz.msgs.Pose",
            "--reptype",
            "gz.msgs.Boolean",
            "--timeout",
            "250",
            "--req",
            (
                f'name: "{model_name}" '
                f"position: {{x: {x:.4f}, y: {y:.4f}, z: {z:.4f}}} "
                "orientation: {w: 1.0}"
            ),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=0.35, check=False)
        except Exception as exc:
            self.get_logger().debug(f"Gazebo set_pose fehlgeschlagen: {exc}")

    def _parse_target(self, data: str) -> Optional[Target]:
        try:
            parts = [p.strip() for p in data.split(",")]
            if len(parts) < 4:
                raise ValueError("Format muss color,x,y,z[,area] sein")
            color = parts[0].lower()
            x = float(parts[1])
            y = float(parts[2])
            z = float(parts[3])
            area = int(float(parts[4])) if len(parts) >= 5 else 0
            return Target(color=color, x=x, y=y, z=z, area=area)
        except Exception as exc:
            self.get_logger().warn(f"Kann /target_pose nicht lesen: '{data}', Fehler: {exc}")
            return None

    def _status(self, text: str) -> None:
        self._status_pub.publish(String(data=text))
        self.get_logger().info(f"[{text}]")


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
