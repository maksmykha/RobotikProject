import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TargetPoseNode(Node):
    def __init__(self):
        super().__init__("target_pose_node")

        self._sub = self.create_subscription(
            String, "/target_object", self._on_target, 10
        )
        self._status_sub = self.create_subscription(
            String, "/pick_place/status", self._on_status, 10
        )
        self._pub = self.create_publisher(String, "/target_pose", 10)

        self._waiting = False  # Blockiert weitere Publishes bis READY
        self.get_logger().info("Target pose node started")

    def _on_status(self, msg):
        if msg.data == 'READY':
            self._waiting = False

    def _on_target(self, msg):
        if self._waiting:
            return
        try:
            parts = msg.data.split(",")
            color = parts[0]
            px = float(parts[1])
            py = float(parts[2])
            area = float(parts[3])

            # Kalibrierte Pixel → World Transformation
            x = 0.55 + (py - 57)  * (0.25 - 0.55) / (157 - 57)
            y = 0.15 + (px - 270) * (-0.15 - 0.15) / (370 - 270)
            z = 0.82

            out = String()
            out.data = f"{color},{x:.3f},{y:.3f},{z:.3f},{int(area)}"
            self._pub.publish(out)
            self._waiting = True  # Blockiere bis Roboter READY meldet

            self.get_logger().info(f"Target pose: {out.data}")

        except Exception as e:
            self.get_logger().warn(f"Error: {e}")


def main(args=None):
    rclpy.init(args=args)
    node = TargetPoseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
