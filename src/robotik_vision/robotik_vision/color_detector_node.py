#!/usr/bin/env python3

import cv2
import numpy as np
import rclpy

from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import String
from cv_bridge import CvBridge


class ColorDetectorNode(Node):
    def __init__(self):
        super().__init__("color_detector_node")

        # Wandelt ROS2 Image-Nachrichten in OpenCV-Bilder um und zurück
        self.bridge = CvBridge()

        # Kamera-Topic 
        self.image_sub = self.create_subscription(
            Image,
            "/gripper_camera/image",
            self.image_callback,
            10
        )

       
        self.debug_image_pub = self.create_publisher(
            Image,
            "/color_detector/debug_image",
            10
        )

        # Erkannte Objektinformationen
        self.detection_pub = self.create_publisher(
            String,
            "/color_detector/detections",
            10
        )

        self.get_logger().info("Color detector node started")

    def image_callback(self, msg):
        # ROS2 Image -> OpenCV BGR-Bild
        frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # BGR -> HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # HSV-Farbbereiche f
        color_ranges = {
            "red": [
                ((0, 100, 100), (10, 255, 255)),
                ((170, 100, 100), (180, 255, 255)),
            ],
            "green": [
                ((40, 70, 70), (85, 255, 255)),
            ],
            "blue": [
                ((90, 70, 70), (130, 255, 255)),
            ],
            "yellow": [
                ((20, 100, 100), (35, 255, 255)),
            ],
        }

        # Farben im OpenCV-BGR
        draw_colors = {
            "red": (0, 0, 255),
            "green": (0, 255, 0),
            "blue": (255, 0, 0),
            "yellow": (0, 255, 255),
        }

        detected_objects = []

        for color_name, ranges in color_ranges.items():
            # maske für rot
            mask_total = None

            for lower, upper in ranges:
                lower_np = np.array(lower, dtype=np.uint8)
                upper_np = np.array(upper, dtype=np.uint8)

                mask = cv2.inRange(hsv, lower_np, upper_np)

                if mask_total is None:
                    mask_total = mask
                else:
                    mask_total = cv2.bitwise_or(mask_total, mask)

            mask_total = cv2.erode(mask_total, None, iterations=2)
            mask_total = cv2.dilate(mask_total, None, iterations=2)

            # Konturen der farbigen Bereiche finden
            contours, _ = cv2.findContours(
                mask_total,
                cv2.RETR_EXTERNAL,
                cv2.CHAIN_APPROX_SIMPLE
            )

            for contour in contours:
                area = cv2.contourArea(contour)
                #Erkennung nur die kleine Würfel
                if area < 500 or area > 3000:
                    continue

                x, y, w, h = cv2.boundingRect(contour)

                # Mittelpunkt in Pixelkoordinaten
                center_x = x + w // 2
                center_y = y + h // 2

                detected_objects.append(
                    f"{color_name},{center_x},{center_y},{int(area)}"
                )

                draw_color = draw_colors[color_name]

                # Rechteck um Objekt zeichnen
                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + w, y + h),
                    draw_color,
                    2
                )

                cv2.circle(
                    frame,
                    (center_x, center_y),
                    5,
                    draw_color,
                    -1
                )

                # Text ins Bild schreiben
                cv2.putText(
                    frame,
                    f"{color_name} ({center_x},{center_y})",
                    (x, max(y - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    draw_color,
                    2
                )

        # Erkannte Objekte als Text 
        for obj in detected_objects:
            self.detection_pub.publish(String(data=obj))

        # Debug-Bild wieder als ROS2 Image 
        debug_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        debug_msg.header = msg.header
        self.debug_image_pub.publish(debug_msg)


def main(args=None):
    rclpy.init(args=args)

    node = ColorDetectorNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()