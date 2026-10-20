# detector_node.py - /scan에서 전방 최소 거리를 계산해 /obstacle/front_distance로 발행
from obstacle_detector.front_distance import front_min_distance
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32


class DetectorNode(Node):

    def __init__(self):
        super().__init__('detector_node')
        # front_deg: 정면 기준 전체 폭(도). 30이면 좌우 15도
        self.declare_parameter('front_deg', 30.0)
        self.pub = self.create_publisher(Float32, '/obstacle/front_distance', 10)
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.get_logger().info('detector_node started (/scan -> /obstacle/front_distance)')

    def on_scan(self, msg):
        front_deg = float(self.get_parameter('front_deg').value)
        dist = front_min_distance(msg, front_deg)
        if dist is None:  # 잘못된 스캔은 발행하지 않는다 (구독측 타임아웃으로 안전 정지)
            return
        self.pub.publish(Float32(data=dist))


def main():
    rclpy.init()
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
