# avoider.py - 3일차 C 기초 틀 (B 감지 연동 전)
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.declare_parameter('stop_dist', 0.5)
        self.declare_parameter('slow_dist', 1.0)
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.5)
        self.declare_parameter('front_deg', 30.0)

        self.front_min = None
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_timer(0.1, self.tick)  # 10Hz
        self.get_logger().info('avoider started (TwistStamped 10Hz)')

    def on_scan(self, msg):
        # TODO(B): 전방 최소 유효거리 로직으로 교체 예정. 현재는 기초 틀.
        n = len(msg.ranges)
        half = int(math.radians(float(self.get_parameter('front_deg').value) / 2) / msg.angle_increment)
        idx = list(range(0, min(half + 1, n))) + list(range(max(0, n - half), n))
        vals = [r for i in idx for r in [msg.ranges[i]]
                if math.isfinite(r) and msg.range_min < r < msg.range_max]
        self.front_min = min(vals) if vals else float('inf')

    def tick(self):
        p = self.get_parameter
        stop_d, slow_d = float(p('stop_dist').value), float(p('slow_dist').value)
        lin, ang = float(p('linear_x').value), float(p('angular_z').value)
        d = self.front_min

        if d is None:  # 스캔 미수신 -> 안전 정지
            cmd_lin, cmd_ang = 0.0, 0.0
        elif d < stop_d:  # 가까움 -> 회전 (제자리)
            cmd_lin, cmd_ang = 0.0, ang
        elif d < slow_d:  # 중간 -> 감속 직진
            cmd_lin, cmd_ang = lin * 0.5, 0.0
        else:  # 여유 -> 직진
            cmd_lin, cmd_ang = lin, 0.0

        msg = TwistStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        msg.twist.linear.x = cmd_lin
        msg.twist.angular.z = cmd_ang
        self.pub.publish(msg)


def main():
    rclpy.init()
    node = Avoider()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
