# avoider.py - 4일차 C: 상태 머신 기반 장애물 회피
# 5일차: 정지 감지(stuck detection)로 후진 -> 회전 복구를 추가한다.
import math

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
from obstacle_avoider.common import make_cmd_vel
from obstacle_avoider.safety import StuckDetector
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from std_msgs.msg import Float32

FORWARD, SLOW, STOP, ROTATE, RECOVER = 'FORWARD', 'SLOW', 'STOP', 'ROTATE', 'RECOVER'
BACK, TURN, GAVE_UP = 'BACK', 'TURN', 'GAVE_UP'


class Avoider(Node):
    def __init__(self):
        super().__init__('avoider')
        # --- 4일차: 전방 거리 기반 상태 머신 ---
        self.declare_parameter('stop_dist', 0.5)      # 회전 시작
        self.declare_parameter('slow_dist', 1.0)      # 감속 시작
        self.declare_parameter('recover_dist', 1.5)   # 재주행 시작 (히스테리시스)
        self.declare_parameter('linear_x', 0.2)
        self.declare_parameter('angular_z', 0.5)
        self.declare_parameter('scan_timeout', 0.5)
        self.declare_parameter('stop_time', 0.3)      # 정지 유지 시간
        self.declare_parameter('recover_time', 1.0)   # 재주행 유지 시간

        # --- 5일차: 정지 감지(센서 사각지대 대응) ---
        self.declare_parameter('odom_topic', '/odom')
        self.declare_parameter('odom_timeout', 0.5)      # odom 끊김 판정
        self.declare_parameter('stuck_check_time', 1.0)  # 이동 감시 창(초)
        self.declare_parameter('stuck_move_eps', 0.03)   # 창 안 최소 이동 거리(m)
        self.declare_parameter('back_speed', -0.1)       # 음수 = 후진
        self.declare_parameter('back_time', 0.8)         # 후진 시간(초)
        self.declare_parameter('turn_angle_deg', 90.0)   # 후진 후 회전 각도
        self.declare_parameter('turn_dir', -1.0)         # -1: 오른쪽, +1: 왼쪽
        self.declare_parameter('stuck_window', 180.0)    # 재시도 횟수 시간창(초)
        self.declare_parameter('stuck_max', 3)           # 시간창 안 최대 재시도

        self.front_min = None
        self.last_scan_time = None
        self.state = FORWARD
        self.state_start = self.get_clock().now()
        self.tick_count = 0

        # 정지 감지용 위치 (기본 /odom, 시뮬 테스트는 ground-truth 토픽으로 교체 가능)
        self.odom_x = 0.0
        self.odom_y = 0.0
        self.last_odom_time = None
        self.stuck = StuckDetector(
            window_s=float(self.get_parameter('stuck_check_time').value),
            move_eps=float(self.get_parameter('stuck_move_eps').value),
            counter_window_s=float(self.get_parameter('stuck_window').value),
            max_count=int(self.get_parameter('stuck_max').value),
        )

        self.create_subscription(Float32, '/obstacle/front_distance', self.on_distance, 10)
        self.create_subscription(
            Odometry, self.get_parameter('odom_topic').value, self.on_odom, 10)
        self.pub = self.create_publisher(TwistStamped, '/cmd_vel', 10)
        self.create_timer(0.1, self.tick)  # 10Hz
        self.get_logger().info(f'avoider started (state machine, state={self.state})')

    def on_distance(self, msg):
        self.last_scan_time = self.get_clock().now()
        self.front_min = msg.data  # 유효값이 없으면 inf

    def on_odom(self, msg):
        self.odom_x = msg.pose.pose.position.x
        self.odom_y = msg.pose.pose.position.y
        self.last_odom_time = self.get_clock().now()

    def odom_fresh(self, now):
        if self.last_odom_time is None:
            return False
        timeout = float(self.get_parameter('odom_timeout').value)
        return (now - self.last_odom_time).nanoseconds / 1e9 <= timeout

    def enter(self, state):
        if state != self.state:
            self.get_logger().info(f'{self.state} -> {state}')
            self.state = state
            self.state_start = self.get_clock().now()
            self.stuck.reset()  # 새 상태에서는 이동 감시를 처음부터

    def elapsed(self):
        return (self.get_clock().now() - self.state_start).nanoseconds / 1e9

    def on_stuck(self, now_s):
        """정지 감지 시: 후진 상태로, 시간창 안 횟수가 넘으면 포기한다."""
        count = self.stuck.register(now_s)
        max_count = int(self.get_parameter('stuck_max').value)
        window = float(self.get_parameter('stuck_window').value)
        if count >= max_count:
            self.get_logger().error(
                f'stuck {count} times in {window:.0f}s -> GAVE_UP (stop)')
            self.enter(GAVE_UP)
        else:
            self.get_logger().warn(
                f'stuck detected ({count}/{max_count}) -> BACK then TURN')
            self.enter(BACK)

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
        back_s = float(p('back_speed').value)
        back_t = float(p('back_time').value)
        turn_w = ang * float(p('turn_dir').value)
        turn_deg = float(p('turn_angle_deg').value)
        turn_t = (math.radians(turn_deg) / abs(turn_w)
                  if abs(turn_w) > 1e-6 else 0.0)

        now = self.get_clock().now()
        now_s = now.nanoseconds / 1e9
        d = self.front_min
        if self.last_scan_time is None or (now - self.last_scan_time).nanoseconds / 1e9 > timeout:
            d = None  # 거리 수신 끊김

        # 전진 명령 중인데 실제 위치가 안 변하면 stuck -> BACK/GAVE_UP
        if d is not None and self.state in (FORWARD, SLOW) and self.odom_fresh(now):
            if self.stuck.update(now_s, self.odom_x, self.odom_y):
                self.on_stuck(now_s)
        else:
            self.stuck.reset()

        if d is None:  # 거리 미수신/끊김 -> 안전 정지
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
        elif self.state == BACK:
            cmd_lin, cmd_ang = back_s, 0.0
            if self.elapsed() > back_t:
                self.enter(TURN)
        elif self.state == TURN:
            cmd_lin, cmd_ang = 0.0, turn_w
            if self.elapsed() > turn_t:
                self.enter(FORWARD)
        else:  # GAVE_UP: 더 이상 재시도하지 않고 정지 유지
            cmd_lin, cmd_ang = 0.0, 0.0

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
