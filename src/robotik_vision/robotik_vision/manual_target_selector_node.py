
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class ManualTargetSelectorNode(Node):
    def __init__(self):
        super().__init__("manual_target_selector_node")

        # Letzte erkannte Objekte, sortiert nach Farbe
        self.latest_detections = {}

        # Gewünschte Farbe, z. B. "red", "green", "blue", "yellow"
        self.requested_color = None

        # Abonniert alle Farberkennungen
        self.detection_sub = self.create_subscription(
            String,
            "/color_detector/detections",
            self.detection_callback,
            10
        )

        # Abonniert Konsolenbefehl: welche Farbe soll genommen werden?
        self.request_sub = self.create_subscription(
            String,
            "/requested_color",
            self.request_callback,
            10
        )

        # Publiziert das ausgewählte Zielobjekt
        self.target_pub = self.create_publisher(
            String,
            "/target_object",
            10
        )

        self.get_logger().info("Manual target selector node started")
        self.get_logger().info("Use: ros2 topic pub /requested_color std_msgs/msg/String \"data: 'red'\" --once")

    def detection_callback(self, msg):
        """
        Erwartetes Format:
        color,x_pixel,y_pixel,area

        Beispiel:
        red,270,58,1444
        """

        try:
            parts = msg.data.split(",")

            color = parts[0]
            x_pixel = int(parts[1])
            y_pixel = int(parts[2])
            area = int(parts[3])

            # Speichert pro Farbe immer die letzte Detection
            self.latest_detections[color] = {
                "color": color,
                "x": x_pixel,
                "y": y_pixel,
                "area": area,
            }

        except Exception as e:
            self.get_logger().warn(
                f"Could not parse detection: {msg.data}, error: {e}"
            )

    def request_callback(self, msg):
        """
        Wird aufgerufen, wenn über die Konsole eine Farbe angefordert wird.
        """

        requested = msg.data.strip().lower()

        self.get_logger().info(f"Requested color: {requested}")

        if requested not in self.latest_detections:
            self.get_logger().warn(
                f"No current detection for color '{requested}'"
            )
            return

        detection = self.latest_detections[requested]

        target_msg = String()
        target_msg.data = (
            f'{detection["color"]},'
            f'{detection["x"]},'
            f'{detection["y"]},'
            f'{detection["area"]}'
        )

        self.target_pub.publish(target_msg)

        self.get_logger().info(
            f"Published target object: {target_msg.data}"
        )


def main(args=None):
    rclpy.init(args=args)

    node = ManualTargetSelectorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()