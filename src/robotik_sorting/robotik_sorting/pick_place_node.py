#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import String
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import math


class PickPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_place_node')

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory'
        )

        self.target_sub = self.create_subscription(
            String,
            '/target_pose',
            self.target_callback,
            10
        )

        self.status_pub = self.create_publisher(String, '/pick_place/status', 10)

        self.joints = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint',
        ]

        self.bin_positions = {
            'red':    [-1.5, -1.2, 1.0, -1.5, -1.57, 0.0],
            'green':  [-1.2, -1.2, 1.0, -1.5, -1.57, 0.0],
            'blue':   [1.2,  -1.2, 1.0, -1.5, -1.57, 0.0],
            'yellow': [1.5,  -1.2, 1.0, -1.5, -1.57, 0.0],
        }

        self.home_position = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]

        self.is_busy = False
        self.pending_color = None

        self.get_logger().info('Pick & Place Node gestartet! Warte auf /target_pose ...')

    def target_callback(self, msg):
        if self.is_busy:
            return

        try:
            parts = msg.data.split(',')
            color = parts[0]
            x = float(parts[1])
            y = float(parts[2])

            self.get_logger().info(f'Ziel erkannt: {color} bei ({x:.3f}, {y:.3f})')
            self.is_busy = True
            self.pending_color = color

            # Schritt 1: Annaeherung
            approach = self.compute_approach(x, y)
            self.get_logger().info(f'Fahre zu Objekt: {color}')
            self.publish_status(f'APPROACHING {color}')
            self.send_trajectory(approach, duration=5, on_done=self.step_place)

        except Exception as e:
            self.get_logger().error(f'Fehler: {e}')
            self.is_busy = False

    def step_place(self):
        color = self.pending_color
        if color not in self.bin_positions:
            self.get_logger().warn(f'Kein Bin fuer: {color}')
            self.is_busy = False
            return

        self.get_logger().info(f'Fahre zu {color} Bin')
        self.publish_status(f'PLACING {color}')
        self.send_trajectory(self.bin_positions[color], duration=5, on_done=self.step_home)

    def step_home(self):
        self.get_logger().info('Fahre zu Home')
        self.publish_status('HOME')
        self.send_trajectory(self.home_position, duration=4, on_done=self.step_done)

    def step_done(self):
        self.is_busy = False
        self.pending_color = None
        self.publish_status('READY')
        self.get_logger().info('Fertig! Bereit fuer naechstes Objekt.')

    def compute_approach(self, x, y):
        pan = math.atan2(y, x)
        return [pan, -1.0, 1.2, -1.8, -1.57, 0.0]

    def send_trajectory(self, positions, duration=4, on_done=None):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory = JointTrajectory()
        goal.trajectory.joint_names = self.joints

        point = JointTrajectoryPoint()
        point.positions = [float(p) for p in positions]
        point.velocities = [0.0] * 6
        point.time_from_start = Duration(sec=duration)
        goal.trajectory.points = [point]

        self._action_client.wait_for_server()
        future = self._action_client.send_goal_async(goal)

        if on_done:
            future.add_done_callback(
                lambda f: self.on_goal_accepted(f, on_done, duration)
            )

    def on_goal_accepted(self, future, on_done, duration):
        goal_handle = future.result()
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(
            lambda f: on_done()
        )

    def publish_status(self, status):
        self.status_pub.publish(String(data=status))


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
