#!/usr/bin/env python3
"""
Pick & Place Node - Sauber, Callback-basiert, kein Thread-Konflikt
"""
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from std_msgs.msg import String
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import subprocess
import math


class PickPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_place_node')
        cb = ReentrantCallbackGroup()

        self._ac = ActionClient(
            self, FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory',
            callback_group=cb
        )
        self.create_subscription(
            String, '/target_pose', self._on_target, 10, callback_group=cb
        )
        self.create_subscription(
            JointState, '/joint_states', self._on_joints, 10, callback_group=cb
        )
        self._status_pub = self.create_publisher(String, '/pick_place/status', 10)

        self._jnames = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
        ]

        # Pick-Positionen (Pan kalibriert aus MoveIt Joints Tab)
        self._pick = {
            'yellow': [-1.012, -0.785, 2.025, -2.845, -1.571, 0.0],
            'red':    [ 0.035, -0.785, 2.025, -2.845, -1.571, 0.0],
            'green':  [ 0.087, -0.785, 2.025, -2.845, -1.571, 0.0],
            'blue':   [-0.541, -0.785, 2.025, -2.845, -1.571, 0.0],
        }

        # Place-Positionen (kalibriert)
        self._place = {
            'yellow': [2.143, -0.677, 3.274, -3.066, -1.574, 0.134],
            'red':    [2.150, -0.679, 2.466, -3.065, -1.552, -0.674],
            'green':  [0.867, -0.262, 2.756, -2.203, -1.559, -0.384],
            'blue':   [1.104, -0.362, 3.224, -2.342, -1.572, 0.084],
        }

        # Bin-Positionen in Gazebo
        self._bins = {
            'red':    (-0.40,  0.20, 0.83),
            'green':  (-0.75,  0.20, 0.83),
            'blue':   (-0.75, -0.20, 0.83),
            'yellow': (-0.40, -0.20, 0.83),
        }

        self._home = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]
        self._joints = [0.0] * 6
        self._color = None
        self._state = 'IDLE'
        self._cube_attached = False

        self.create_timer(0.1, self._track, callback_group=cb)
        self._status('READY')
        self.get_logger().info('Pick & Place bereit!')

    def _on_joints(self, msg):
        jmap = dict(zip(msg.name, msg.position))
        for i, n in enumerate(self._jnames):
            if n in jmap:
                self._joints[i] = jmap[n]

    def _track(self):
        """Wuerfel folgt Arm NUR wenn attached=True"""
        if not self._cube_attached or not self._color:
            return
        p, l, e = self._joints[0], self._joints[1], self._joints[2]
        r = 0.425 * math.cos(l) + 0.3922 * math.cos(l + e)
        x = r * math.cos(p)
        y = r * math.sin(p)
        z = 0.97 + 0.425 * math.sin(-l) + 0.3922 * math.sin(-(l + e))
        self._set_pose(f'obj_{self._color}', x, y, z + 0.05)

    def _on_target(self, msg):
        """Startet Pick & Place - NUR wenn IDLE"""
        if self._state != 'IDLE':
            return
        color = msg.data.split(',')[0]
        if color not in self._pick:
            return
        self._color = color
        self._state = 'BUSY'
        self.get_logger().info(f'=== Pick & Place: {color} ===')
        self._status(f'PICKING {color}')
        # Schritt 1: Zum Wuerfel fahren
        self._move(self._pick[color], 5, self._step_grip)

    def _step_grip(self):
        """Arm ist beim Wuerfel → Greifen"""
        self.get_logger().info(f'Greife {self._color}')
        self._cube_attached = True  # Tracking startet jetzt
        self._status(f'TRANSPORTING {self._color}')
        # Schritt 2: Zum Bin fahren (Wuerfel folgt)
        self._move(self._place[self._color], 6, self._step_release)

    def _step_release(self):
        """Arm ist beim Bin → Loslassen"""
        self.get_logger().info(f'Lasse {self._color} los')
        self._cube_attached = False  # Tracking stoppen
        bx, by, bz = self._bins[self._color]
        self._set_pose(f'obj_{self._color}', bx, by, bz)
        self._status('HOME')
        # Schritt 3: Home fahren
        self._move(self._home, 4, self._step_done)

    def _step_done(self):
        """Fertig → IDLE"""
        self.get_logger().info('=== Fertig! ===')
        self._state = 'IDLE'
        self._color = None
        self._status('READY')

    def _move(self, positions, duration, callback):
        """Sendet Trajectory Goal und ruft callback wenn fertig"""
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = self._jnames
        pt = JointTrajectoryPoint()
        pt.positions = [float(p) for p in positions]
        pt.velocities = [0.0] * 6
        pt.time_from_start = Duration(sec=duration)
        goal.trajectory.points = [pt]

        self._ac.wait_for_server()
        f = self._ac.send_goal_async(goal)
        f.add_done_callback(lambda fut: self._on_accepted(fut, callback))

    def _on_accepted(self, future, callback):
        gh = future.result()
        rf = gh.get_result_async()
        rf.add_done_callback(lambda f: callback())

    def _set_pose(self, name, x, y, z):
        cmd = [
            'gz', 'service', '-s', '/world/pick_place_world/set_pose',
            '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean',
            '--timeout', '200', '--req',
            f'name: "{name}" position: {{x: {x:.3f}, y: {y:.3f}, z: {z:.3f}}} orientation: {{w: 1.0}}'
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=0.3)
        except Exception:
            pass

    def _status(self, s):
        self._status_pub.publish(String(data=s))
        self.get_logger().info(f'[{s}]')


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    ex = MultiThreadedExecutor()
    ex.add_node(node)
    try:
        ex.spin()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
