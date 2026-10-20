<<<<<<< HEAD
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
=======
import math
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import LaserScan

THRESHOLD = 0.5 # m
FRONT_HALF_ANGLE = math.radians(15)



def front_min(ranges, angle_min, angle_inc, r_min, r_max, half_angle=FRONT_HALF_ANGLE):
    """정면 ±half_angle 구간의 유효 최소 거리. 유효값 없으면 None"""
    valid = []
    for i, r in enumerate(ranges):
        a = math.atan2(math.sin(angle_min + i * angle_inc), math.cos(angle_min + i * angle_inc))
    if abs(a) <= half_angle and math.isfinite(r) and r_min <= r <= r_max:
        valid.append(r)
    return min(valid) if valid else None


def is_obstacle(dist, threshold=THRESHOLD):
    return dist is not None and dist <= threshold


class DetectorNode(Node):
    def __init__(self):
        super().__init__('obstacle_detector')
        self.create_subscription(LaserScan, '/scan', self.cb, qos_profile_sensor_data)

    def cb(self, msg):
        d = front_min(msg.ranges, msg.angle_min, msg.angle_increment,
        msg.range_min, msg.range_max)
        detected = is_obstacle(d)
        self.get_logger().info(
        f'front_min={d},threshold={THRESHOLD},detected={detected},'
        f'range=[{msg.range_min:.2f},{msg.range_max:.2f}]')

>>>>>>> 3663224 ([b] feat:/benchmark_pub.py 파일 수정)


def main():
    rclpy.init()
<<<<<<< HEAD
    node = DetectorNode()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
=======
    rclpy.spin(DetectorNode())
    rclpy.shutdown()

>>>>>>> 3663224 ([b] feat:/benchmark_pub.py 파일 수정)


if __name__ == '__main__':
    main()
