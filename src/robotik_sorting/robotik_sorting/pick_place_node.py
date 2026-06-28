#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from std_msgs.msg import String
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class PickPlaceNode(Node):
    def __init__(self):
        super().__init__('pick_place_node')

        self._action_client = ActionClient(
            self,
            FollowJointTrajectory,
            '/arm_controller/follow_joint_trajectory'
        )

        self.target_sub = self.create_subscription(
            String, '/target_pose', self.target_callback, 10
        )
        self.status_pub = self.create_publisher(
            String, '/pick_place/status', 10
        )

        self.joints = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint',
        ]

        # Greif-Positionen: pan berechnet aus atan2(y, x) der Wuerfel
        # Wuerfel-Positionen in Gazebo:
        # yellow: (0.25, -0.15) -> pan=-0.54
        # red:    (0.55,  0.15) -> pan= 0.27
        # green:  (0.25,  0.15) -> pan= 0.54
        # blue:   (0.55, -0.15) -> pan=-0.27
        self.pick_positions = {
            'yellow': [-0.54, -1.30, 1.57, -1.80, -1.57, 0.0],
            'red':    [ 0.27, -1.30, 1.57, -1.80, -1.57, 0.0],
            'green':  [ 0.54, -1.30, 1.57, -1.80, -1.57, 0.0],
            'blue':   [-0.27, -1.30, 1.57, -1.80, -1.57, 0.0],
        }

        # Bin-Positionen aus SDF:
        # red_bin:    (-0.4,  0.20)
        # green_bin:  (-0.75, 0.20)
        # blue_bin:   (-0.75,-0.20)
        # yellow_bin: (-0.4, -0.20)
        self.place_positions = {
            'red':    [-2.68, -1.20, 1.20, -1.57, -1.57, 0.0],
            'green':  [-2.87, -1.20, 1.20, -1.57, -1.57, 0.0],
            'blue':   [ 2.87, -1.20, 1.20, -1.57, -1.57, 0.0],
            'yellow': [ 2.68, -1.20, 1.20, -1.57, -1.57, 0.0],
        }

        self.home = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]
        self.is_busy = False
        self.pending_color = None

        self.get_logger().info('Pick & Place Node gestartet!')
        self.get_logger().info('Warte auf /target_pose ...')

    def target_callback(self, msg):
        if self.is_busy:
            return
        try:
            parts = msg.data.split(',')
            color = parts[0]
            if color not in self.pick_positions:
                self.get_logger().warn(f'Unbekannte Farbe: {color}')
                return
            self.get_logger().info(f'Starte Pick & Place fuer: {color}')
            self.is_busy = True
            self.pending_color = color
            self.publish_status(f'PICKING {color}')
            self.send_trajectory(
                self.pick_positions[color], duration=5, on_done=self.step_place
            )
        except Exception as e:
            self.get_logger().error(f'Fehler: {e}')
            self.is_busy = False

    def step_place(self):
        color = self.pending_color
        self.get_logger().info(f'Lege {color} in Bin')
        self.publish_status(f'PLACING {color}')
        self.send_trajectory(
            self.place_positions[color], duration=5, on_done=self.step_home
        )

    def step_home(self):
        self.get_logger().info('Fahre zu Home')
        self.publish_status('HOME')
        self.send_trajectory(self.home, duration=4, on_done=self.step_done)

    def step_done(self):
        self.is_busy = False
        self.pending_color = None
        self.publish_status('READY')
        self.get_logger().info('Fertig! Bereit fuer naechstes Objekt.')

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
                lambda f: self.on_goal_response(f, on_done)
            )

    def on_goal_response(self, future, on_done):
        goal_handle = future.result()
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(lambda f: on_done())

    def publish_status(self, status):
        self.status_pub.publish(String(data=status))
        self.get_logger().info(f'Status: {status}')


def main(args=None):
    rclpy.init(args=args)
    node = PickPlaceNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
