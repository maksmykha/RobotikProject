
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class TargetPoseNode(Node):
    def __init__(self):
        super().__init__("target_pose_node")

        # Bildgröße der Kamera
        self.image_width = 640.0
        self.image_height = 480.0

        # Erste einfache Kalibrierung der Arbeitsfläche in Metern
        # Diese Werte müssen später an eure echte Gazebo-Szene angepasst werden.
        self.world_x_min = -0.30
        self.world_x_max = 0.30

        self.world_y_min = -0.40
        self.world_y_max = 0.40

        # Höhe der Objektoberfläche / Greifebene
        self.world_z = 0.0

        # Subscriber: ausgewähltes Objekt in Pixelkoordinaten
        self.target_sub = self.create_subscription(
            String,
            "/target_object",
            self.target_callback,
            10
        )

        # Publisher: Zielobjekt in Tischkoordinaten
        self.pose_pub = self.create_publisher(
            String,
            "/target_pose",
            10
        )

        self.get_logger().info("Target pose node started")

    def pixel_to_world(self, pixel_x, pixel_y):
        """
        Wandelt Pixelkoordinaten in einfache Tischkoordinaten um.

        pixel_x:
            links = 0
            rechts = 640

        pixel_y:
            oben = 0
            unten = 480

        Welt:
            x von -0.30 bis 0.30
            y von  0.40 bis -0.40
        """

        x_world = (
            self.world_x_min
            + (pixel_x / self.image_width)
            * (self.world_x_max - self.world_x_min)
        )

        # y wird umgedreht, weil Bild-y nach unten wächst
        y_world = (
            self.world_y_max
            - (pixel_y / self.image_height)
            * (self.world_y_max - self.world_y_min)
        )

        return x_world, y_world, self.world_z

    def target_callback(self, msg):
        """
        Erwartetes Format:
        color,x_pixel,y_pixel,area

        Beispiel:
        red,270,57,1441
        """

        try:
            parts = msg.data.split(",")

            color = parts[0]
            pixel_x = float(parts[1])
            pixel_y = float(parts[2])
            area = float(parts[3])

            x_world, y_world, z_world = self.pixel_to_world(
                pixel_x,
                pixel_y
            )

            pose_msg = String()
            pose_msg.data = (
                f"{color},"
                f"{x_world:.3f},"
                f"{y_world:.3f},"
                f"{z_world:.3f},"
                f"{int(area)}"
            )

            self.pose_pub.publish(pose_msg)

            self.get_logger().info(
                f"Target pose: {pose_msg.data}"
            )

        except Exception as e:
            self.get_logger().warn(
                f"Could not parse target object: {msg.data}, error: {e}"
            )


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