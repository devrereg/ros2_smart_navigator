# sensor_fault_test.py - 가짜 /scan을 넣어 detector_node 결과를 판정한다 (11일차 B)
# 시뮬레이션과 섞이지 않도록 scripts/run_sensor_regression.sh로 실행한다
import sys
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from sensor_monitor.scan_check import (RANGE_MAX, RANGE_MIN, same_distance, scenario_ranges,
                                       SCENARIOS)
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Float32

SCANS_PER_SCENARIO = 5
PERIOD_SEC = 0.2  # 실제 라이다와 같은 5 Hz


class SensorFaultTest(Node):

    def __init__(self):
        super().__init__('sensor_fault_test')
        self.pub = self.create_publisher(LaserScan, '/scan', 10)
        self.create_subscription(Float32, '/obstacle/front_distance', self.on_topic, 10)
        self.received = []

    def on_topic(self, msg):
        self.received.append(msg.data)

    def publish_scan(self, sc):
        ranges = scenario_ranges(sc)
        msg = LaserScan()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_scan'
        msg.angle_increment = sc['increment']
        msg.angle_max = sc['increment'] * (len(ranges) - 1)
        msg.range_min = RANGE_MIN
        msg.range_max = RANGE_MAX
        msg.ranges = ranges
        self.pub.publish(msg)

    def spin_for(self, seconds):
        deadline = time.monotonic() + seconds
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.01)

    def run_scenario(self, sc):
        self.received = []
        for _ in range(SCANS_PER_SCENARIO):
            self.publish_scan(sc)
            self.spin_for(PERIOD_SEC)
        self.spin_for(0.3)  # 마지막 결과까지 받고, 다음 시나리오와 섞이지 않게 기다린다
        expected = sc['expected']
        if expected is None:
            return not self.received
        return (len(self.received) == SCANS_PER_SCENARIO
                and all(same_distance(expected, v) for v in self.received))


def main():
    rclpy.init()
    node = SensorFaultTest()
    failed = 0
    try:
        deadline = time.monotonic() + 15.0
        while node.pub.get_subscription_count() == 0 or node.count_publishers(
                '/obstacle/front_distance') == 0:
            if time.monotonic() > deadline:
                node.get_logger().error('detector_node와 연결되지 않았습니다.')
                return 1
            node.spin_for(0.1)
        node.spin_for(2.0)  # 양쪽 매칭이 끝날 시간을 준다

        print('| 시나리오 | 기대 | 수신 | 결과 |')
        print('|---|---|---|---|')
        for sc in SCENARIOS:
            ok = node.run_scenario(sc)
            failed += 0 if ok else 1
            expected = '발행 없음' if sc['expected'] is None else sc['expected']
            print(f"| {sc['name']} | {expected} | {sorted(set(node.received))} | "
                  f"{'통과' if ok else '실패'} |", flush=True)
        print(f'\n{len(SCENARIOS) - failed}/{len(SCENARIOS)} 통과')
    except (KeyboardInterrupt, ExternalShutdownException):
        return 130
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
