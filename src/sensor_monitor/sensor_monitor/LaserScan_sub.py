import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.executors import ExternalShutdownException

class LaserScan_sub(Node):
    def __init__(self):
        super().__init__('LaserScan_sub')
        self.create_subscription(LaserScan, '/scan',self.callback,10)

    def callback(self, msg):
        front = list(msg.ranges[-5:]) + list(msg.ranges[:6]) # 정면에서 +-5 도
        valid = [r for r in front if not math.isinf(r) and msg.range_min <= r <= msg.range_max]

        if valid:
            self.get_logger().info(f"정면 :{min(valid):.2f} m")
        else: 
            self.get_logger().info("정면: 장애물 없음")

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
