# detection_log.py - /scan과 /obstacle/front_distance를 대조해 CSV로 기록한다 (6일차 B)
# detector_node와 같은 /scan을 받아 따로 계산한 값이 토픽 값과 같은지 스캔마다 확인한다
import csv
import os
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_monitor.scan_check import front_min_by_angle, ScanTopicMatcher, sector_stats
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32

# CSV 열 순서. topic은 토픽 값, calc는 스캔에서 다시 계산한 값이다
FIELDS = ['time_ns', 'status', 'topic', 'calc', 'left_min', 'right_min', 'back_min', 'all_min',
          'nan', 'pos_inf', 'neg_inf', 'out_of_range']


class DetectionLog(Node):

    def __init__(self):
        super().__init__('detection_log')
        self.declare_parameter('front_deg', 30.0)  # detector_node와 같은 값으로 실행
        self.declare_parameter('out', 'results/csv/detection_log.csv')
        out = self.get_parameter('out').value

        # 같은 이름이 있으면 덮어쓴다 ('w' 모드). 회차별로 남기려면 out을 바꿔 실행한다
        os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
        self.file = open(out, 'w', newline='')
        self.writer = csv.DictWriter(self.file, fieldnames=FIELDS)
        self.writer.writeheader()
        self.matcher = ScanTopicMatcher()
        self.create_subscription(LaserScan, '/scan', self.on_scan, 10)
        self.create_subscription(Float32, '/obstacle/front_distance', self.on_topic, 10)
        # 메시지가 끊겨도 짝 없는 항목을 확정할 수 있도록 주기적으로 확인한다
        self.create_timer(0.1, self.on_timer)
        self.get_logger().info(f'기록: {out}')

    def on_scan(self, msg):
        front_deg = float(self.get_parameter('front_deg').value)
        # time_ns는 avoider 로그와 시각을 맞추기 위한 벽시계 시각이다
        info = {'time_ns': time.time_ns(), **sector_stats(msg, front_deg)}
        calc = front_min_by_angle(msg, front_deg)
        # 짝짓기에는 시스템 시각 변경에 영향받지 않는 monotonic을 쓴다
        self.write(self.matcher.add_scan(time.monotonic(), calc, info))

    def on_topic(self, msg):
        self.write(self.matcher.add_topic(time.monotonic(), msg.data))

    def on_timer(self):
        self.write(self.matcher.poll(time.monotonic()))

    def write(self, rows):
        for row in rows:
            self.writer.writerow(row)
            # 정상 행은 CSV에만 남기고, 문제 행은 실행 중에 바로 보이도록 경고한다
            if row['status'] in ('mismatch', 'no_topic', 'extra_topic'):
                self.get_logger().warn(
                    f"{row['status']}: topic={row['topic']} calc={row['calc']}")


def main():
    rclpy.init()
    node = DetectionLog()
    try:
        rclpy.spin(node)  # Ctrl+C 할 때까지 기록
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # 버퍼에 남은 행을 디스크에 기록하고 파일을 닫는다
        node.file.close()
        node.destroy_node()
        rclpy.try_shutdown()
