import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.executors import ExternalShutdownException

class LaserScan_sub(Node):
    def __init__(self):
        super().__init__('LaserScan_sub')
        self.create_subscription(LaserScan, '/scan',self.callback,10) # /scan 구독: 메시지가 올 때마다 callback 호출, 큐 크기 10

    def callback(self, msg):
        front = list(msg.ranges[-30:]) + list(msg.ranges[:31]) # 정면에서 +-5 도
        valid = [r for r in front if not math.isfinite(r) and msg.range_min <= r <= msg.range_max]
        # 유효값만 남김
        # math.isfinite: inf, NaN 제거
        # range_min ~ range_max: 센서 측정 범위 밖의 값 제거
        if valid:
            self.get_logger().info(f"정면 :{min(valid):.2f} m") # 유효값 중 최솟값 = 정면에서 가장 가까운 장애물 거리
        else: 
            self.get_logger().info("정면: 장애물 없음") # 유효값이 하나도 없음 = 측정 범위 안에 장애물 없음

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
