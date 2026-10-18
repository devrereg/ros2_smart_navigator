# avoider.py - 3일차 C: /scan 전방 최소거리로 정지/감속/회전 결정
import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped

from obstacle_avoider.common import make_cmd_vel


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.declare_parameter('stop_dist', 0.5)
        self.declare_parameter('slow_dist', 1.0)
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.5)
        self.declare_parameter('front_deg', 30.0)
        self.declare_parameter('scan_timeout', 0.5)

        self.front_min = None
        self.last_scan_time = None
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_timer(0.1, self.tick)  # 10Hz
        self.get_logger().info('avoider started (TwistStamped 10Hz)')

    def on_scan(self, msg):
        self.last_scan_time = self.get_clock().now()
        inc = msg.angle_increment
        if inc <= 0.0:  # 잘못된 스캔 -> 안전 정지
            self.front_min = None
            return
        n = len(msg.ranges)
        half = int(math.radians(float(self.get_parameter('front_deg').value) / 2) / inc)
        idx = list(range(0, min(half + 1, n))) + list(range(max(0, n - half), n))
        vals = [msg.ranges[i] for i in idx
                if math.isfinite(msg.ranges[i]) and msg.range_min < msg.ranges[i] < msg.range_max]
        self.front_min = min(vals) if vals else float('inf')

    def tick(self):
        p = self.get_parameter
        stop_d, slow_d = float(p('stop_dist').value), float(p('slow_dist').value)
        lin, ang = float(p('linear_x').value), float(p('angular_z').value)
        timeout = float(p('scan_timeout').value)

        now = self.get_clock().now()
        d = self.front_min
        if self.last_scan_time is None or (now - self.last_scan_time).nanoseconds / 1e9 > timeout:
            d = None  # 스캔 끊김 -> 안전 정지

        if d is None:  # 스캔 미수신/끊김 -> 안전 정지
            cmd_lin, cmd_ang = 0.0, 0.0
        elif d < stop_d:  # 가까움 -> 회전 (제자리)
            cmd_lin, cmd_ang = 0.0, ang
        elif d < slow_d:  # 중간 -> 감속 직진
            cmd_lin, cmd_ang = lin * 0.5, 0.0
        else:  # 여유 -> 직진
            cmd_lin, cmd_ang = lin, 0.0

        self.pub.publish(make_cmd_vel(self, cmd_lin, cmd_ang))


def main():
    rclpy.init()
    node = Avoider()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
