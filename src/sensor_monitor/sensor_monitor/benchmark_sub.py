import csv
import os
import struct
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import UInt8MultiArray

HEADER = struct.Struct('<QQ')  # benchmark_pub과 동일한 형식 (seq, send_time_ns)


class BenchmarkSub(Node):

    def __init__(self):
        super().__init__('benchmark_sub')
        self.declare_parameter('reliability', 'reliable')  # reliable | best_effort
        self.declare_parameter('rate_hz', 10)  # 파일명 기록용 (발행 주기는 pub이 정함)
        self.declare_parameter('run', 1)  # 반복 번호 (파일명 기록용)
        self.declare_parameter('out_dir', 'results/csv')  # 실행 위치 기준 상대 경로

        reliability = self.get_parameter('reliability').value
        rate_hz = self.get_parameter('rate_hz').value
        run = self.get_parameter('run').value
        out_dir = self.get_parameter('out_dir').value

        # raw_<condition>_<run>.csv, condition = <reliability>_<rate>hz
        # 같은 이름이 있으면 덮어쓴다 ('w' 모드)
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, f'raw_{reliability}_{rate_hz}hz_{run}.csv')
        self.file = open(path, 'w', newline='')
        self.writer = csv.writer(self.file)
        self.writer.writerow(
            ['seq', 'send_time_ns', 'recv_time_ns', 'latency_ms', 'payload_bytes'])
        self.get_logger().info(f'기록: {path}')

        # pub과 reliability가 다르면 연결이 안 되거나(RELIABLE sub + BEST_EFFORT pub)
        # 조건이 섞이므로 반드시 같은 값으로 실행한다
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy[reliability.upper()])
        self.create_subscription(UInt8MultiArray, '/benchmark/data', self.callback, qos)

    def callback(self, msg):
        # 수신 시각을 가장 먼저 찍어 처리 시간이 지연에 섞이지 않게 한다
        recv_ns = time.time_ns()
        data = bytes(msg.data)
        # 앞 16바이트에서 seq와 송신 시각을 꺼냄 (나머지는 패딩)
        seq, send_ns = HEADER.unpack_from(data)
        # pub과 sub이 같은 컴퓨터의 같은 시계를 쓰므로 그대로 빼면 지연시간
        latency_ms = (recv_ns - send_ns) / 1e6
        # 1건당 1행. 손실/중복/순서 판정은 기록 후 seq로 분석한다
        self.writer.writerow([seq, send_ns, recv_ns, f'{latency_ms:.3f}', len(data)])


def main():
    rclpy.init()
    node = BenchmarkSub()
    try:
        rclpy.spin(node)  # Ctrl+C 할 때까지 수신
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        # 버퍼에 남은 행을 디스크에 기록하고 파일을 닫는다
        node.file.close()
        node.destroy_node()
        rclpy.try_shutdown()
