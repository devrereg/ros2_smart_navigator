import struct  # 바이너리(이진) 데이터와 파이썬 값 사이의 변환을 처리하는 struct 내장 모듈
import time

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
# QoSProfile: QoS 설정 묶음, ReliabilityPolicy: 데이터를 얼마나 확실하게 보낼 것인가에 대한 정책
from rclpy.qos import QoSProfile, ReliabilityPolicy
from std_msgs.msg import UInt8MultiArray

# payload 앞 16바이트: seq(uint64) + send_time_ns(uint64), 나머지는 0으로 채움
# struct.Struct: 포맷을 객체로 만들어 두고 pack/unpack에 재사용
# '<QQ': '<' = 리틀 엔디언, 'Q' = unsigned 64bit 정수 → 8바이트 x 2 = 16바이트
HEADER = struct.Struct('<QQ')


class BenchmarkPub(Node):

    def __init__(self):
        super().__init__('benchmark_pub')
        # declare_parameter: 노드 실행 시 사용할 파라미터(설정값)를 등록하고 기본값으로 초기화
        # 실행할 때 --ros-args -p 이름:=값 으로 바꿀 수 있다
        self.declare_parameter('reliability', 'reliable')  # reliable | best_effort
        self.declare_parameter('rate_hz', 10)            # 초당 발행 횟수
        self.declare_parameter('duration_sec', 30.0)       # 발행 시간(초)
        self.declare_parameter('payload_bytes', 64)        # 메시지 1건 크기(바이트)

        # get_parameter: 등록해 둔 파라미터를 코드 안에서 실제로 읽어옴
        reliability = self.get_parameter('reliability').value
        rate_hz = self.get_parameter('rate_hz').value
        duration = self.get_parameter('duration_sec').value
        # 헤더(16바이트)보다 작게 지정해도 최소 16바이트는 보장
        size = max(self.get_parameter('payload_bytes').value, HEADER.size)

        # 문자열 파라미터('reliable')를 대문자로 바꿔 ReliabilityPolicy.RELIABLE 등으로 변환
        # depth=10: 최근 메시지 10건까지 큐에 보관 (KEEP_LAST)
        qos = QoSProfile(depth=10, reliability=ReliabilityPolicy[reliability.upper()])
        self.pub = self.create_publisher(UInt8MultiArray, '/benchmark/data', qos)

        # 정확히 rate * duration 건만 보낸다 → sent_count = rate * duration
        self.total = int(rate_hz * duration)
        # payload 크기를 맞추기 위한 0 바이트 (매번 만들지 않도록 미리 생성)
        self.padding = bytes(size - HEADER.size)
        self.seq = 0  # 다음에 보낼 메시지 순번 (0부터)
        self.timer = None
        self.rate_hz = rate_hz

    def start(self):
        # 타이머 주기 = 1 / rate_hz 초 → 주기마다 tick() 호출
        self.get_logger().info(f'발행 시작: {self.total}건')
        self.timer = self.create_timer(1.0 / self.rate_hz, self.tick)

    def tick(self):
        msg = UInt8MultiArray()
        # [seq | 송신 시각(ns) | 0 패딩] 순서로 바이트를 이어 붙여 payload 구성
        msg.data = HEADER.pack(self.seq, time.time_ns()) + self.padding
        self.pub.publish(msg)
        self.seq += 1


def main():
    rclpy.init()
    node = BenchmarkPub()
    try:
        # subscriber와 연결되기 전에 보내면 앞쪽 메시지가 유실되므로 매칭을 기다린다
        deadline = time.monotonic() + 30.0 #monotonic() 을 사용해 시스템 시각 및 서버 시간 동기화에 독립시킴 , 30초 뒤로 설정 변경 가능
        while rclpy.ok() and node.pub.get_subscription_count() == 0:
            if time.monotonic() > deadline:
                node.get_logger().error(f"30초 동안 '{node.pub.topic_name}' 토픽의 subscriber와 매칭되지 않았습니다. "
                                        "subscriber 노드 실행 여부, 토픽 이름/타입, QoS 호환성, ROS_DOMAIN_ID를 확인하세요. "
                                        f"(확인: ros2 topic info -v {node.pub.topic_name})")
            rclpy.spin_once(node, timeout_sec=0.1)
        node.start()
        # spin 대신 spin_once 반복: total 건을 다 보내면 루프를 빠져나와 자동 종료
        while rclpy.ok() and node.seq < node.total:
            rclpy.spin_once(node)
        node.get_logger().info(f'발행 완료: {node.seq}건')
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
