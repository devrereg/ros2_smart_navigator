# avoid_trial.py - 자동 주행 1회를 감시해 회피 성공 여부를 판정한다 (11일차 C·A)
# 5일차에 저장소 밖 스크립트로 하던 감시를 노드로 옮겼다. scripts/run_avoid_trials.sh로 반복 실행한다
import csv
import math
import os
import time

from geometry_msgs.msg import TwistStamped
from nav_msgs.msg import Odometry
import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_monitor.scan_check import sector_stats, trial_verdict
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32

SECTORS = ['left_min', 'right_min', 'back_min']
TRACE_FIELDS = ['t_sec', 'x', 'y', 'front_topic', 'left_min', 'right_min', 'back_min',
                'all_min', 'cmd_lin', 'cmd_ang']
SUMMARY_FIELDS = ['label', 'x_pose', 'y_pose', 'duration_sec', 'moved_m', 'min_front',
                  'min_all', 'min_all_sector', 'min_all_t_sec', 'verdict', 'reason']


class AvoidTrial(Node):

    def __init__(self):
        super().__init__('avoid_trial')
        self.declare_parameter('label', 'trial')
        self.declare_parameter('x_pose', 0.0)  # 기록용 (스폰은 launch가 한다)
        self.declare_parameter('y_pose', 0.0)
        self.declare_parameter('duration_sec', 70.0)  # 5일차와 같은 감시 시간
        self.declare_parameter('out_dir', 'results/csv')
        self.duration = float(self.get_parameter('duration_sec').value)
        out_dir = self.get_parameter('out_dir').value
        os.makedirs(out_dir, exist_ok=True)
        self.summary_path = os.path.join(out_dir, 'avoid_trials.csv')
        trace_path = os.path.join(out_dir, f"avoid_trace_{self.get_parameter('label').value}.csv")
        # 시점별 기록: 접촉 의심이 어느 동작·방향에서 나왔는지 나중에 찾기 위한 것
        self.trace_file = open(trace_path, 'w', newline='')
        self.trace = csv.DictWriter(self.trace_file, fieldnames=TRACE_FIELDS)
        self.trace.writeheader()

        self.start = None  # /scan과 /odom이 모두 들어온 첫 시각부터 감시
        self.pos = None
        self.moved = 0.0
        self.front = None
        self.cmd = (0.0, 0.0)
        self.min_front = math.inf
        self.min_all = (math.inf, '', 0.0)  # 값, 방향, 시각

        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.create_subscription(Float32, '/obstacle/front_distance', self.on_front, 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_subscription(TwistStamped, '/cmd_vel', self.on_cmd, 10)
        self.get_logger().info(f'기록: {trace_path}, {self.summary_path}')

    def on_front(self, msg):
        self.front = msg.data
        if not math.isnan(msg.data):  # NaN은 측정 실패라 최소값 후보가 아니다
            self.min_front = min(self.min_front, msg.data)

    def on_cmd(self, msg):
        self.cmd = (msg.twist.linear.x, msg.twist.angular.z)

    def on_odom(self, msg):
        p = msg.pose.pose.position
        if self.pos is not None:
            self.moved += math.hypot(p.x - self.pos[0], p.y - self.pos[1])
        self.pos = (p.x, p.y)

    def on_scan(self, msg):
        if self.pos is None:
            return
        now = time.monotonic()
        if self.start is None:
            self.start = now
            self.moved = 0.0  # 스폰 직후 낙하 등 감시 전 이동은 세지 않는다
        t = now - self.start
        s = sector_stats(msg)
        if s['all_min'] < self.min_all[0]:
            # 전방 밖 구간이 최소이면 그 방향, 아니면 전방
            side = min(SECTORS, key=lambda k: s[k])
            self.min_all = (s['all_min'], side if s[side] <= s['all_min'] else 'front', t)
        self.trace.writerow({
            't_sec': f'{t:.2f}', 'x': f'{self.pos[0]:.3f}', 'y': f'{self.pos[1]:.3f}',
            'front_topic': self.front, **{k: s[k] for k in SECTORS + ['all_min']},
            'cmd_lin': f'{self.cmd[0]:.2f}', 'cmd_ang': f'{self.cmd[1]:.2f}'})

    def done(self):
        return self.start is not None and time.monotonic() - self.start >= self.duration

    def write_summary(self):
        verdict, reason = trial_verdict(self.min_front, self.min_all[0], self.moved)
        if self.start is None:
            verdict, reason = 'excluded', '/scan 또는 /odom 수신 없음'
        p = self.get_parameter
        row = {'label': p('label').value, 'x_pose': p('x_pose').value,
               'y_pose': p('y_pose').value,
               'duration_sec': round(time.monotonic() - self.start, 1) if self.start else 0,
               'moved_m': round(self.moved, 3), 'min_front': self.min_front,
               'min_all': self.min_all[0], 'min_all_sector': self.min_all[1],
               'min_all_t_sec': round(self.min_all[2], 2), 'verdict': verdict, 'reason': reason}
        new = not os.path.exists(self.summary_path)
        with open(self.summary_path, 'a', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=SUMMARY_FIELDS)
            if new:
                w.writeheader()
            w.writerow(row)
        self.get_logger().info(f'{verdict}: {row}')


def main():
    rclpy.init()
    node = AvoidTrial()
    try:
        while rclpy.ok() and not node.done():
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # 중간에 끊겨도 그때까지의 결과를 남긴다
        node.write_summary()
        node.trace_file.close()
        node.destroy_node()
        rclpy.try_shutdown()
