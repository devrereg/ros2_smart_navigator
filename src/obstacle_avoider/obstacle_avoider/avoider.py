# avoider.py - 4일차 C: 상태 머신 기반 장애물 회피
# 5일차: 정지 감지(stuck detection)로 후진 -> 회전 복구를 추가한다.
# 7일차: front_distance의 NaN/-inf/+inf 센티널을 구분해 안전 정지/후진/전진을 처리한다.
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
        self.declare_parameter('stuck_max', 3)           # stuck/too-close 공통 최대 재시도

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
        self.front_min = msg.data  # NaN/-inf/+inf 센티널 포함

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

    def format_distance(self, d):
        """로그용 거리 표기. NaN/-inf/+inf를 구분한다."""
        if d is None:
            return 'None'
        if math.isnan(d):
            return 'nan'
        if math.isinf(d):
            return '+inf' if d > 0 else '-inf'
        return f'{d:.2f}m'

    def publish_cmd(self, lin, ang, d):
        self.pub.publish(make_cmd_vel(self, lin, ang))
        self.tick_count += 1
        if self.tick_count % 10 == 0:  # 1초마다 상태와 거리 로그
            self.get_logger().info(
                f'state={self.state} front_min={self.format_distance(d)} '
                f'cmd=({lin:.2f}, {ang:.2f})'
            )

    def on_recovery(self, reason, now_s):
        """stuck/too-close 공통: BACK 후 TURN, 횟수 제한에 도달하면 GAVE_UP."""
        # StuckDetector.register()를 두 종류의 복구 시도에 공통으로 사용한다.
        count = self.stuck.register(now_s)
        max_count = int(self.get_parameter('stuck_max').value)
        window = float(self.get_parameter('stuck_window').value)
        if count >= max_count:
            self.get_logger().error(
                f'recovery attempts {count} in {window:.0f}s '
                f'(last={reason}) -> GAVE_UP (stop)')
            self.enter(GAVE_UP)
        else:
            self.get_logger().warn(
                f'{reason} detected (recovery {count}/{max_count}) -> BACK then TURN')
            self.enter(BACK)

    def on_stuck(self, now_s):
        self.on_recovery('stuck', now_s)

    def on_too_close(self, now_s):
        self.on_recovery('too close', now_s)

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

        # NaN/미수신: 상태를 바꾸지 않고 정지한다. 상태 타이머도 멈춰서
        # 복구 중 NaN이 끼어도 BACK/TURN 시간을 건너뛰지 않게 한다.
        if d is None or math.isnan(d):
            self.state_start = now
            self.stuck.reset()  # NaN으로 멈춘 것을 stuck으로 오판하지 않도록 이동 기록 초기화
            self.publish_cmd(0.0, 0.0, d)
            return

        # 0 이하(음수, -inf)는 too-close로 보고 후진/탐색 복구를 시작한다.
        too_close = d <= 0.0
        if too_close and self.state not in (BACK, TURN, GAVE_UP):
            self.on_too_close(now_s)

        # 전진 명령 중인데 실제 위치가 안 변하면 stuck -> BACK/GAVE_UP
        if (not too_close and self.state in (FORWARD, SLOW)
                and self.odom_fresh(now)):
            if self.stuck.update(now_s, self.odom_x, self.odom_y):
                self.on_stuck(now_s)
        else:
            self.stuck.reset()

        if self.state == FORWARD:
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
            if d > rec_d:  # 거리 회복 시 불필요한 회전을 하지 않는다
                self.enter(FORWARD)
            elif self.elapsed() > stop_t:
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

        self.publish_cmd(cmd_lin, cmd_ang, d)


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
