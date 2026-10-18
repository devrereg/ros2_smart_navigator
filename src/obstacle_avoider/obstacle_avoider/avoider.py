# avoider.py - 4일차 C: 상태 머신 기반 장애물 회피
import math
import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import TwistStamped

from obstacle_avoider.common import make_cmd_vel

FORWARD, SLOW, STOP, ROTATE, RECOVER = 'FORWARD', 'SLOW', 'STOP', 'ROTATE', 'RECOVER'


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        self.declare_parameter('stop_dist', 0.5)      # 회전 시작
        self.declare_parameter('slow_dist', 1.0)      # 감속 시작
        self.declare_parameter('recover_dist', 1.5)   # 재주행 시작 (히스테리시스)
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.5)
        self.declare_parameter('front_deg', 30.0)
        self.declare_parameter('scan_timeout', 0.5)
        self.declare_parameter('stop_time', 0.3)      # 정지 유지 시간
        self.declare_parameter('recover_time', 1.0)   # 재주행 유지 시간

        self.front_min = None
        self.last_scan_time = None
        self.state = FORWARD
        self.state_start = self.get_clock().now()
        self.tick_count = 0
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_timer(0.1, self.tick)  # 10Hz
        self.get_logger().info(f'avoider started (state machine, state={self.state})')

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

    def enter(self, state):
        if state != self.state:
            self.get_logger().info(f'{self.state} -> {state}')
            self.state = state
            self.state_start = self.get_clock().now()

    def elapsed(self):
        return (self.get_clock().now() - self.state_start).nanoseconds / 1e9

    def tick(self):
        p = self.get_parameter
        stop_d = float(p('stop_dist').value)
        slow_d = float(p('slow_dist').value)
        rec_d = float(p('recover_dist').value)
        lin = float(p('linear_x').value)
        ang = float(p('angular_z').value)
        timeout = float(p('scan_timeout').value)
        stop_t = float(p('stop_time').value)
        rec_t = float(p('recover_time').value)

        now = self.get_clock().now()
        d = self.front_min
        if self.last_scan_time is None or (now - self.last_scan_time).nanoseconds / 1e9 > timeout:
            d = None  # 스캔 끊김

        if d is None:  # 스캔 미수신/끊김 -> 안전 정지
            cmd_lin, cmd_ang = 0.0, 0.0
        elif self.state == FORWARD:
            cmd_lin, cmd_ang = lin, 0.0
            if d < stop_d:
                self.enter(STOP)
            elif d < slow_d:
                self.enter(SLOW)
        elif self.state == SLOW:
            cmd_lin, cmd_ang = lin * 0.5, 0.0
            if d < stop_d:
                self.enter(STOP)
            elif d > rec_d:  # 충분히 멀어져야 복귀 (히스테리시스)
                self.enter(FORWARD)
        elif self.state == STOP:
            cmd_lin, cmd_ang = 0.0, 0.0
            if self.elapsed() > stop_t:
                self.enter(ROTATE)
        elif self.state == ROTATE:
            cmd_lin, cmd_ang = 0.0, ang
            if d > rec_d:  # 전방이 충분히 비면 재주행
                self.enter(RECOVER)
        elif self.state == RECOVER:
            cmd_lin, cmd_ang = lin, 0.0
            if d < stop_d:
                self.enter(STOP)
            elif self.elapsed() > rec_t:
                self.enter(FORWARD)

        self.pub.publish(make_cmd_vel(self, cmd_lin, cmd_ang))

        self.tick_count += 1
        if self.tick_count % 10 == 0:  # 1초마다 상태와 거리 로그
            d_txt = 'None' if d is None else ('inf' if d == float('inf') else f'{d:.2f}m')
            self.get_logger().info(
                f'state={self.state} front_min={d_txt} cmd=({cmd_lin:.2f}, {cmd_ang:.2f})'
            )


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
