import math

from obstacle_detector.front_distance import front_min_distance
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


class LaserScan_sub(Node):

    def __init__(self):
        super().__init__('LaserScan_sub')
        # /scan 구독: 메시지가 올 때마다 callback 호출, 큐 크기 10
        self.create_subscription(LaserScan, '/scan', self.callback, 10)

    def callback(self, msg):
        # 전방 최소 거리 계산은 obstacle_detector의 공통 함수를 쓴다 (정면 좌우 15도)
        dist = front_min_distance(msg)
        if dist is None:
            self.get_logger().warn('잘못된 스캔 (angle_increment <= 0)')
        elif math.isinf(dist):
            # 유효값이 하나도 없음 = 측정 범위 안에 장애물 없음
            self.get_logger().info('정면: 장애물 없음')
        else:
            self.get_logger().info(f'정면 :{dist:.2f} m')


def main():
    rclpy.init()
    node = LaserScan_sub()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
