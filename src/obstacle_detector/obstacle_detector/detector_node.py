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



def main():
    rclpy.init()
    rclpy.spin(DetectorNode())
    rclpy.shutdown()



if __name__ == '__main__':
    main()
