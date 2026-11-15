# 내가 해야할 일 

/scan 구독 및 sensor_msgs/msg/LaserScan 데이터 확인
전방 각도 구간의 최소 유효 거리 계산
NaN, inf, 범위 밖 값 등 비정상 센서값 처리
장애물 감지 로그와 테스트 사례 기록
센서 처리 및 감지 알고리즘 문서 작성

# day 0

## 서버 실행 

1. 해당 폴더로 이동

``` bash
cd 모델이 있는 폴더로 이동
```
! 왜 모델이 있는 폴더로 이동하지?

2. 열기ㅇ

``` bash
gz sim $ 해당 맵이 있는 경로/맵
    -s 서버만 열기: 센서 제어만 하기 용이
    -v 로그 출력 상세화
```
## 로봇 수동 제어

### 모델 토픽명 확인
  ```bash
  # 전체 토픽 목록에서 모델명으로 필터링
  gz topic -l | grep 모델명

  # 월드에 있는 모델 이름 확인
  gz model --list

  # 특정 모델 정보 (링크, 조인트 등)
  gz model -m 모델명

  # 토픽 상세 정보 (메시지 타입 확인)
  gz topic -i -t /토픽명

  # ROS 2 쪽 (브리지 실행 후)
  ros2 topic list | grep 모델명
  ros2 topic info /토픽명
  ```

### gz topic 
```bash
  # 토픽 목록
  gz topic -l

  # 토픽 정보 (메시지 타입, 퍼블리셔/서브스크라이버)
  gz topic -i -t /토픽명

  # 토픽 내용 보기
  gz topic -e -t /토픽명

  # 토픽 주기(Hz) 확인
  gz topic -f -t /토픽명

  # 메시지 발행
  gz topic -t /토픽명 -m 메시지_타입 -p '필드: 값'

  # 속도 명령
  gz topic -t /model/모델명/cmd_vel -m gz.msgs.Twist -p 'linear: {x: 속력_float}, angular: {z: 회전_float}'
```

### ros2 제어

```bash
# gz <-> ROS 2 브리지
  #   @ : 양방향,  [ : gz -> ROS,  ] : ROS -> gz
  ros2 run ros_gz_bridge parameter_bridge \
    /토픽명@ROS_메시지_타입[gz_메시지_타입

  # 예: cmd_vel(ROS -> gz)
  ros2 run ros_gz_bridge parameter_bridge \
    /model/모델명/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist

  # 토픽 목록 / 정보 / 내용
  ros2 topic list
  ros2 topic info /토픽명
  ros2 topic echo /토픽명

  # 메시지 발행 (-r: 반복 주기 Hz, --once: 1회)
  ros2 topic pub -r 주기_Hz /토픽명 메시지_타입 "{필드: 값}"

  # 속도 명령
  ros2 topic pub -r 주기_Hz /model/모델명/cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 속력_float}, angular: {z: 회전_float}}"

  # 키보드 텔레옵
  ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/model/모델명/cmd_vel
```

### GUI 제어
```bash
  # Gazebo 실행 (GUI 포함)
  gz sim 월드파일.sdf

  # 서버만 / GUI만 실행
  gz sim -s 월드파일.sdf
  gz sim -g

  # 시뮬레이션 일시정지 / 재생 (pause: true|false)
  gz service -s /world/월드명/control --reqtype gz.msgs.WorldControl \
    --reptype gz.msgs.Boolean --timeout 타임아웃_ms --req 'pause: bool'

  # rqt 슬라이더로 속도 제어
  ros2 run rqt_robot_steering rqt_robot_steering

  # RViz2 시각화
  rviz2
```

# day 1
/scan 메시지 타입·주기·QoS 확인, 장애물 감지 기준 정리


## 메시지 타입 확인
  ```bash
  # 토픽 목록 + 타입
  ros2 topic list -t

  # 특정 토픽 타입
  ros2 topic type /scan

  # 메시지 구조(필드) 확인
  ros2 interface show sensor_msgs/msg/LaserScan
  ros2 interface show geometry_msgs/msg/Twist
  ```

## 메시지 주기 확인
  ```bash
   # 발행 주기(Hz)
  ros2 topic hz /scan

  # 대역폭
  ros2 topic bw /scan
  ```
## QoS 확인
  ```bash
    # 퍼블리셔/서브스크라이버 QoS (Reliability, Durability, History, Depth)
  ros2 topic info /scan -v
  ```
## 장애물 감지 기준 확인
  ```bash
  # LaserScan 파라미터 1회 출력
  ros2 topic echo /scan --once --field range_min
  ros2 topic echo /scan --once --field range_max
  ros2 topic echo /scan --once --field angle_min
  ros2 topic echo /scan --once --field angle_max
  ros2 topic echo /scan --once --field angle_increment

   # 실제 거리값 배열
  ros2 topic echo /scan --once --field ranges
  ```

## 문제점
### 1. /scan이 안 보일 때
판단 1: ros2 node list 로 scan이 있는지 확인 
    없음

판단 2: gz topic -l 로 scan이 있는지 확인
    있음

판단 3: 브리지 패키지 설치 및 시도
    성공 
        패키지 설치
            sudo apt update
            sudo apt install ros-jazzy-ros-gz
      ros2 run ros_gz_bridge parameter_bridge /scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan
    

### 브리지
Gazebo와 ROS 2는 서로 다른 통신 시스템을 사용
Gazebo가 /scan을 발행해도 ROS 2에서는 보이지 않음. ros_gz_bridge가 두 시스템 사이에서 메시지를 변환해서 전달

#### 특징
계속 실행해햐함

#### 왜 필요함?
제어 코드를 짜려면 ROS 2가 편하기 때문
기존 도구랑 연동 용의
 RViz2:스캔·지도 시각화, Nav2: 자율주행, SLAM (Cartographer 등) :지도 작성 ,teleop_twist_keyboard :키보드 조종  

# day 2
LaserScan 구독 노드 구현, 전방 거리 출력

## 노드 패키지 생성
  cd <레포>/src
  rm -rf sensor_monitor        # 비어 있는지 먼저 확인할 것
  ros2 pkg create --build-type ament_python sensor_monitor --dependencies rclpy sensor_msgs

## 노드 py 작성
``` python
import math
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from rclpy.executors import ExternalShutdownException

class LaserScan_sub(Node):
  def __init__(self):
    super().__init__('LaserScan_sub')
    self.create_subscription(LaserScan, '/scan',self.callback,10)

  def callback(self, msg):
    front = list(msg.ranges[-5:]) + list(msg.ranges[:6]) # 정면에서 +-5 도
    valid = [r for r in front if math.isfinite(r) and msg.range_min <= r <= msg.range_max]

    if valid:
      self.get_logger().info(f"정면 :{min(valid):.2f} m")
    else:
      self.get_logger().info("정면: 장애물 없음")

def main():
  rclpy.init()
  node = LaserScan_sub()
  try:
    rclpy.spin(node)
  except (KeyboardInterrupt, ExternalShutdownException):
    pass
  finally:
    node.destroy_node()
    rclpy.shutdown()
```

# day 3
전방 각도 구간의 최소 유효 거리 계산, inf·NaN 처리

## export 환경변수 제어
파일 위치를 바꿔서 world가 안열리는 문제가 생김 
  이를 해결 하기 위해 export로 환경 변수 제어

1. 현제 터미널에서 만 적용

``` bash
export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:/home/taeho-kim/ros2_smart_navigator/models
```

2. .bashrc에 영구 적용 하기

```bash
echo 'export GZ_SIM_RESOURCE_PATH=$GZ_SIM_RESOURCE_PATH:/home/taeho-kim/ros2_smart_navigator/models' >> ~/.bashrc
source ~/.bashrc
```

## 노드 테스트
1.  gz sim으로 월드 열기

2. ros2_smart_navigator 폴더에서 colcon build,source 하기

3. 패키지 안 setup.py 의 엔트리 포인트 보고 명령어 실행
  ros2 run sensor_monitor LaserScan_sub

4. 월드안 장애물 생성후 토픽 확인
  정상 작동


## inf·NaN 처리
``` python 
      valid = [r for r in front if math.isfinite(r) and msg.range_min <= r <= msg.range_max]
```
으로 변환

# day 4
메시지 수집 csv 파일, 요약 csv 파일 작성 및 시나리오 산정 맵 가져오기

## 수집 benchmark_pub.py

```python
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
        self.declare_parameter('rate_hz', 10.0)            # 초당 발행 횟수
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
        while rclpy.ok() and node.pub.get_subscription_count() == 0:
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
```

### 수정 요청
1.
src/sensor_monitor/sensor_monitor/benchmark_pub.py
        # declare_parameter: 노드 실행 시 사용할 파라미터(설정값)를 등록하고 기본값으로 초기화
        # 실행할 때 --ros-args -p 이름:=값 으로 바꿀 수 있다
        self.declare_parameter('reliability', 'reliable')  # reliable | best_effort
        self.declare_parameter('rate_hz', 10.0)            # 초당 발행 횟수
@devrereg
devrereg
10 hours ago
Owner
benchmark_sub.py 에는 정수형(10) 으로 되어있습니다.
실수형으로 선언시 파라미터를 10 으로 넘기면 타입에러가 발생할 수 있을것 같습니다. 정수형으로 통일하면 좋을 것 같습니다.

2.
src/sensor_monitor/sensor_monitor/benchmark_pub.py
    try:
        # subscriber와 연결되기 전에 보내면 앞쪽 메시지가 유실되므로 매칭을 기다린다
        while rclpy.ok() and node.pub.get_subscription_count() == 0:
            rclpy.spin_once(node, timeout_sec=0.1)
@devrereg
devrereg
10 hours ago
Owner
subscriber 가 안켜져있거나, QoS 가 맞지 않는 경우에 어떠한 문제인지 알 수 있는 방법이 없습니다.
if time.monotonic() > (while 실행 이후 30초 뒤):
error("원인 안내")
return

이런식으로 종료 코드를 작성하는게 좋을것 같습니다.


#### 요청 대안
1.
int,float 이든 각각의 파라미터에 형식을 맞춰야 하는걸 확인

그래서 정수 실수의 이점 확인 (cluad 사용 )
  - int가 나은 경우: 10, 20, 30Hz처럼 정해진 값만 쓰는 경우입니다. 카메라 FPS나 제어 루프가 보통 그렇습니다. 사용자도 대개 10이라고 입력하니 에러 날 일이 적습니다.

  - float가 나은 경우: 0.5Hz(2초에 한 번)처럼 1Hz보다 느리게 돌리거나 12.5처럼 세밀하게 조정해야 하는 경우입니다.


추후 세밀 조정 할때 float 형으로 변환하는게 좋아 보임 지금은 간단하게 돌리니깐
  예시 _rate_hz가 1Hz 미만이 될 일이 없다면 int로, 그럴 가능성이 있다면 float로 두고 YAML에도 10.0으로 쓰는 것을 추천

2.
  try:
          # subscriber와 연결되기 전에 보내면 앞쪽 메시지가 유실되므로 매칭을 기다린다
          deadline = time.monotonic() + 30.0
          while rclpy.ok() and node.pub.get_subscription_count() == 0:
              if time.monotonic() > deadline:
                node.get_logger().error(
                    f"30초 동안 '{node.pub.topic_name}' 토픽의 subscriber와 매칭되지 않았습니다. "
                    "subscriber 노드 실행 여부, 토픽 이름/타입, QoS 호환성, ROS_DOMAIN_ID를 확인하세요. "
                    f"(확인: ros2 topic info -v {node.pub.topic_name})")
                  return
              rclpy.spin_once(node, timeout_sec=0.1)

## 저장 benchmark_sub.py 

```python
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
```

## 요약 analyze_results.py

```python
"""raw_<reliability>_<rate>hz_<run>.csv 1개를 집계해 summary.csv에 1행 append."""
import argparse
import csv
from datetime import datetime
import os
import re
import statistics

# summary.csv 열 순서
FIELDS = [
    'run_id', 'timestamp_start', 'reliability', 'pub_rate_hz', 'repetition',
    'duration_sec', 'sent_count', 'received_count', 'loss_count', 'loss_rate',
    'latency_mean_ms', 'latency_p95_ms', 'latency_max_ms', 'env_note',
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raw_csv')
    p.add_argument('--duration', type=float, default=30.0, help='benchmark_pub의 duration_sec')
    p.add_argument('--env-note', default='')
    p.add_argument('--summary', default='results/csv/summary.csv')
    a = p.parse_args()

    # 파일명에서 실험 조건을 읽는다: raw_reliable_10hz_1.csv → reliable, 10, 1
    run_id = os.path.basename(a.raw_csv)[len('raw_'):-len('.csv')]
    m = re.fullmatch(r'(reliable|best_effort)_(\d+)hz_(\d+)', run_id)
    if not m:
        raise SystemExit(f'파일명 형식이 다름: {a.raw_csv}')
    reliability, rate, rep = m.group(1).upper(), int(m.group(2)), int(m.group(3))

    with open(a.raw_csv) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('수신 기록이 없음')

    # 중복 수신은 한 번만 센다
    received = len({r['seq'] for r in rows})
    # pub이 정확히 rate * duration 건을 보내므로 송신 수는 계산으로 구한다
    sent = int(rate * a.duration)
    lat = sorted(float(r['latency_ms']) for r in rows)
    # 실행 시작 시각 = 수신된 메시지 중 가장 이른 송신 시각
    start_ns = min(int(r['send_time_ns']) for r in rows)

    row = {
        'run_id': run_id,
        'timestamp_start': datetime.fromtimestamp(start_ns / 1e9).isoformat(timespec='seconds'),
        'reliability': reliability,
        'pub_rate_hz': rate,
        'repetition': rep,
        'duration_sec': a.duration,
        'sent_count': sent,
        'received_count': received,
        'loss_count': sent - received,
        'loss_rate': round((sent - received) / sent, 4),
        'latency_mean_ms': round(statistics.mean(lat), 3),
        # 정렬된 목록에서 95% 위치의 값 (보간 없음)
        'latency_p95_ms': round(lat[int(0.95 * (len(lat) - 1))], 3),
        'latency_max_ms': round(lat[-1], 3),
        'env_note': a.env_note,
    }

    # 처음 만들 때만 헤더를 쓰고, 이후에는 행만 누적
    new = not os.path.exists(a.summary)
    with open(a.summary, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(row)


if __name__ == '__main__':
    main()
```


## 시나리오 산정 맵 
조건
  - 장애물을 피할 수 있어야함
  - 특정 시나리오에 부합 해야함
  - 여러 상황에 사용 테스트하는 목적

### 1. 시나리오 : 재난 지역 물자 조잘

• DARPA SubT Challenge 맵 
 미 고등연구계획국(DARPA)의 지하/재난 구조 로봇 대회의 오픈소스 맵입니다. 무너진 벽, 파편, 복잡한 미로 형태의 동굴이나 지하 인프라 환경이 구현되어 있어 가상 LiDAR로 SLAM을 수행하기에 최적입니다.
 https://github.com/LTU-RAI/darpa_subt_worlds/tree/main/worlds

• RoboCup Rescue Sim 맵
 재난 구조 로봇 대회인 로보컵 레스큐 팀들이 공개한 Gazebo 월드로, 지진으로 무너진 방이나 장애물(Debri) 맵이 포함되어 있습니다
https://github.com/RoboCup-RSVRL/RoboCup2019RVRL_Demo

### 2. 시나리오 : 소형 농장,공장 물자 조달

• AWS RoboMaker Small Warehouse (추천)
 아마존(AWS)에서 로봇 시뮬레이션용으로 무료 공개한 소형 물류창고(Warehouse) 맵입니다. 선반, 화물 상자, 지입차 등이 배치되어 있어 공장 내 물자 조달 시나리오를 검증하기에 완벽한 표준 맵입니다.
 https://github.com/aws-robotics/aws-robomaker-small-warehouse-world/tree/ros2/worlds

• AgriBot / Gazebo Agriculture 월드
 이랑과 고랑, 작물(포도나무, 토마토 등)이 줄지어 배치된 가상 농장 맵이 오픈소스로 존재합니다. 터틀봇3 버거가 작물 사이를 헤집고 다니며 물자(비료, 수확물)를 나르는 시뮬레이션이 가능합니다.
 https://github.com/FieldRobotEvent/virtual_maize_field
 https://github.com/PRBonn/agribot/tree/master/agribot_gazebo/worlds


# day 5
센서값 미수신·비정상 거리값 처리 검증

## git 작업 흐름 
pr을 날리는데 뭐가 뭔지 몰라서 머지를 함 
  큰 문제는 안되었지만 나중에는 큰 문제가 될 수 있음 
  팀원이 작업 흐름 알려줌

머지(Merge): 서로 다른 두 개의 브랜치(Branch)를 하나로 합치는 병합 과정

작업 흐름 
  PR 날리기
  작업이 끝나면 main 을 작업브랜치에 pull 받는다
    원격 저장소의 main 최신 내역을 현재 브랜치로 가져와 병합하기
      git pull origin main  
  충돌나면 충돌나는 부분 작업자와 논의하여 해결한다.
  PR 을 날린다.

## 확인

1. 월드 ,모델 파일 안에 에 mu와 mu2 계수 있는데 마찰력 관련 계수라 이것도 케이스별 확인해 보기
  turtlebot3 buger/model.sdf
    오른쪽 바퀴,왼쪽 바퀴 100000.0 이 기본 값임
  월드에서는 안보임
    마찰력 값이 없을 때 디폴트(기본값)를 사용하며 이를 파일에 명시적으로 적어두지 않기 때문
    - 설정 방법
      ```xml
      <model name="my_model">
        <link name="link">
          <collision name="collision">
            <geometry>
              <!-- 상자, 구 등 기하학적 형태 정의 -->
            </geometry>

            <!-- 💡 여기에 surface와 friction 태그를 추가합니다 -->
            <surface>
              <friction>
                <ode>
                  <mu>1.0</mu>  <!-- 주 마찰 방향 (기본값 보통 1.0) -->
                  <mu2>1.0</mu> <!-- 부 마찰 방향 (기본값 보통 1.0) -->
                </ode>
              </friction>
            </surface>

          </collision>
        </link>
      </model>
      ```
  <mu>: 첫 번째 마찰 방향(Primary friction direction)에 대한 마찰 계수입니다. 보통 0(마찰 없음)에서 1(강한 마찰) 사이의 값을 주지만, 필요에 따라 더 큰 값을 줄 수도 있습니다.
  <mu2>: 첫 번째 방향과 수직인 두 번째 마찰 방향(Secondary friction direction)에 대한 마찰 계수입니다. 보통 mu와 동일하게 맞추거나 목적에 따라 다르게 설정합니다.

2. 가속도 어떻게 작용하는지 
3. 속도별 같은 상황에서 어떻게 작동하는지 확인중이였어요

4. 라이더 센서 위치
  정중앙 최상단.
 출처:  https://docs.robotis.com/docs/systems/turtlebot3/features/ 


# 센서값 미수신·비정상 거리값 처리 검증

## 미수신값 이란?
데이터가 제시간에 들어오지 않거나 완전히 끊겨서 아무 정보도 없는 상태

### 현상
/scan 토픽의 발행(Publish)이 멈춤

### 예외 처리 방법
타임아웃 감지 로직 (일정 시간 데이터 안 오면 즉시 정지)

## 비정상 거리값 이란?
데이터는 들어왔지만, 물리적으로 불가능하거나 신뢰할 수 없는 엉뚱한 값이 들어온 상태

### 현상
/scan 데이터 내용에 음수, NaN, Inf, 튀는 값이 섞임

### 예외 처리 방법
소프트웨어 필터 (허용 범위 밖의 값 제거, 이동 평균 필터 등)

## 검증 해야하는 이유
로봇의 충돌(안전사고)을 막고 시스템이 갑자기 다운되는 것을 방지하기 위해서

## 검증 방법
데이터 입력 단에서 의도적으로 결함 데이터를 주입(Fault Injection)하고
시스템이 정의된 예외 처리 로직에 따라 안전하게 반응하는지 확인

### 미수신 검증 방법
의도적 토픽 차단, 가짜 타임아웃 주입

#### 결과 

#### 왜 그렇게 나오는지 코드

### 비정상 거리값 검증 방법
노드 가로채기

#### 결과 

#### 왜 그렇게 나오는지 코드


## 변경
NaN,inf,-inf 값을 구분해서 동작을 하기로함

### 센서 부

### 동작 부

# day6
센서 데이터와 감지 로그 일치 여부 확인

## 검증
```python
"""/scan으로 다시 계산한 전방 거리와 /obstacle/front_distance의 일치 여부를 확인한다."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import math
import os
import sys
import time

# 샘플별 판정 값. CSV의 result 열과 화면 집계에 그대로 쓰인다.
MATCH = 'MATCH'                  # 값 일치
MISMATCH = 'MISMATCH'            # 발행됐지만 값이 다름
MISSING = 'MISSING'              # 발행돼야 하는데 없음
EXTRA = 'EXTRA'                  # 대응하는 스캔이 없는 발행
NOT_PUBLISHED = 'NOT_PUBLISHED'  # 잘못된 스캔이라 발행하지 않음 (정상)

# 결과 CSV의 열 순서
FIELDS = ['scan_seq', 'scan_stamp', 'expected', 'observed', 'result']
BAND_MARGIN = 50  # 정렬할 때 허용하는 앞뒤 어긋남(샘플)


def expected_front(ranges, angle_min, inc, range_min, range_max, front_deg=30.0):
    """
    스캔에서 기대하는 전방 거리를 계산한다.

    검증 대상과 같은 함수를 쓰면 계산 오류를 잡지 못하므로 front_min_distance를
    호출하지 않는다. 정면도 인덱스 0으로 가정하지 않고 angle_min으로 찾는다.
    잘못된 스캔이나 전방 전체 NaN이면 None(발행 안 함이 정상)을 반환한다.
    """
    # 각도 정보가 잘못된 스캔은 구간을 정할 수 없다
    if not all(math.isfinite(v) for v in (angle_min, inc, front_deg)) or inc <= 0.0:
        return None
    n = len(ranges)
    # half: 정면에서 좌우로 포함할 샘플 수. detector_node와 같은 반올림 규칙을 쓴다
    half = round(math.radians(front_deg / 2) / inc)
    # center: 각도가 0도인 샘플의 인덱스 (angle_min=0이면 인덱스 0)
    center = round(-angle_min / inc) % n if n else 0
    # 스캔은 원형이므로 인덱스 거리는 양쪽 방향 중 짧은 쪽으로 잰다 (359번은 0번의 바로 옆)
    sector = [r for i, r in enumerate(ranges)
              if min((i - center) % n, (center - i) % n) <= half]

    # 특수값 우선순위: -inf(너무 가까움) > 유효 거리 > 전체 NaN > 그 외(장애물 없음)
    if float('-inf') in sector:
        return float('-inf')
    # 경계값은 제외한다. NaN과 +inf는 이 비교를 통과하지 못해 자동으로 빠진다
    valid = [r for r in sector if range_min < r < range_max]
    if valid:
        return min(valid)
    if sector and all(math.isnan(r) for r in sector):
        return None
    return float('inf')


def same(a, b, tol):
    """두 거리가 오차 안에서 같은지 판단한다. inf는 부호까지 같아야 같은 값이다."""
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= tol


def align(expected, observed, tol):
    """
    기대값과 발행값을 순서를 유지한 채 맞춰 (스캔 번호, 발행 번호, 판정) 목록을 반환한다.

    Float32에는 stamp가 없어 시각으로 짝지을 수 없고, 단순 순번 비교는 한 건만
    빠져도 뒤가 전부 어긋난다. 그래서 불일치 건수가 최소인 정렬을 찾는다.
    """
    # cost[i, j]: 스캔 앞 i개와 발행 앞 j개를 맞췄을 때의 최소 불일치 건수 (동적 계획법)
    # back[i, j]: 그 최소값이 나온 직전 칸과 판정. 끝에서 되짚어 결과를 만든다
    n, m = len(expected), len(observed)
    # 대각선 근처만 계산해 긴 수집에서도 느려지지 않게 한다.
    # 폭이 건수 차이 이상이어야 (n, m)까지 가는 경로가 항상 존재한다
    band = abs(n - m) + BAND_MARGIN
    cost = {(0, 0): 0}
    back = {}
    for i in range(n + 1):
        for j in range(max(0, i - band), min(m, i + band) + 1):
            if i == 0 and j == 0:
                continue
            options = []  # (직전 칸, 추가 비용, 판정) 후보
            # 스캔과 발행을 짝짓는 경우. None 스캔은 발행이 없어야 하므로 짝짓지 않는다
            if i and j and expected[i - 1] is not None:
                ok = same(expected[i - 1], observed[j - 1], tol)
                options.append(((i - 1, j - 1), 0 if ok else 1, MATCH if ok else MISMATCH))
            # 스캔만 소비하는 경우: None 스캔이면 정상, 아니면 누락
            if i:
                none = expected[i - 1] is None
                options.append(((i - 1, j), 0 if none else 1, NOT_PUBLISHED if none else MISSING))
            # 발행만 소비하는 경우: 대응하는 스캔이 없는 발행
            if j:
                options.append(((i, j - 1), 1, EXTRA))
            # 폭 밖의 칸은 계산하지 않았으므로 후보에서 뺀다
            options = [o for o in options if o[0] in cost]
            prev, step, result = min(options, key=lambda o: cost[o[0]] + o[1])
            cost[i, j] = cost[prev] + step
            back[i, j] = (prev, result)

    # 끝 칸에서 시작점까지 되짚는다. 없는 쪽의 번호는 None으로 둔다
    rows = []
    pos = (n, m)
    while pos != (0, 0):
        prev, result = back[pos]
        rows.append((
            pos[0] - 1 if result != EXTRA else None,
            pos[1] - 1 if result not in (MISSING, NOT_PUBLISHED) else None,
            result,
        ))
        pos = prev
    rows.reverse()  # 끝에서부터 모았으므로 시간 순서로 되돌린다
    return rows


def trim_edges(rows, edge):
    """수집 시작·종료 순간에 한쪽 토픽만 잡힌 샘플을 양 끝에서 edge개까지 제외한다."""
    # MISMATCH는 실제 값 오류이므로 끝에 있어도 제외하지 않는다
    start, end = 0, len(rows)
    while start < min(edge, end) and rows[start][2] in (MISSING, EXTRA):
        start += 1
    tail = 0
    while tail < edge and end > start and rows[end - 1][2] in (MISSING, EXTRA):
        end -= 1
        tail += 1
    return rows[start:end]


def verdict(counts):
    """집계로 최종 판정을 낸다. 일치 건수가 0이면 확인한 것이 없으므로 PASS가 아니다."""
    if counts[MISMATCH] or counts[MISSING] or counts[EXTRA]:
        return 'FAIL'
    return 'PASS' if counts[MATCH] else 'INCONCLUSIVE'


def fmt(value):
    """CSV에 쓸 거리 문자열을 만든다. 값이 없으면 빈 칸이다."""
    return '' if value is None else f'{value:.4f}'


def write_csv(path, scans, observed, rows):
    """정렬 결과를 샘플당 한 행으로 저장한다."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for si, oi, result in rows:
            # EXTRA는 대응하는 스캔이 없어 스캔 쪽 열을 비운다
            seq, stamp, exp = scans[si] if si is not None else ('', '', None)
            w.writerow({
                'scan_seq': seq,
                'scan_stamp': stamp,
                # 'none'은 발행하지 않는 것이 정상인 스캔, 빈 칸은 스캔 자체가 없는 행이다
                'expected': 'none' if si is not None and exp is None else fmt(exp),
                'observed': fmt(observed[oi]) if oi is not None else '',
                'result': result,
            })


def collect(duration, front_deg):
    """두 토픽을 구독해 (스캔 목록, 발행값 목록)을 반환한다."""
    # 계산 함수는 ROS 없이 테스트할 수 있도록 rclpy는 여기서만 불러온다
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import Float32

    # seen: 첫 메시지가 도착한 토픽 이름
    scans, observed, seen = [], [], set()

    def on_scan(msg):
        seen.add('scan')
        if len(seen) < 2:  # 두 토픽이 모두 연결된 뒤부터 기록한다
            return
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        exp = expected_front(msg.ranges, msg.angle_min, msg.angle_increment,
                             msg.range_min, msg.range_max, front_deg)
        scans.append((len(scans), f'{stamp:.3f}', exp))

    def on_distance(msg):
        seen.add('distance')
        if len(seen) == 2:
            observed.append(msg.data)

    rclpy.init()
    node = Node('detection_checker')
    # 검증 노드 쪽에서 메시지를 버리지 않도록 큐를 크게 잡는다 (QoS는 기본 Reliable)
    node.create_subscription(LaserScan, '/scan', on_scan, 100)
    node.create_subscription(Float32, '/obstacle/front_distance', on_distance, 100)
    node.get_logger().info(f'{duration:.0f}초 동안 수집합니다. Ctrl+C로 먼저 끝낼 수 있습니다.')
    deadline = time.monotonic() + duration
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl+C로 끝내도 그때까지 모은 데이터는 분석한다
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return scans, observed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--duration', type=float, default=60.0, help='수집 시간(초)')
    p.add_argument('--front-deg', type=float, default=30.0, help='detector_node의 front_deg')
    p.add_argument('--tolerance', type=float, default=1e-3, help='일치로 보는 오차(m)')
    p.add_argument('--edge', type=int, default=3, help='양 끝에서 제외할 수 있는 샘플 수')
    p.add_argument('--out', default=None, help='결과 CSV 경로')
    a = p.parse_args()

    # 수집이 끝난 뒤 한 번에 분석한다
    scans, observed = collect(a.duration, a.front_deg)
    expected = [s[2] for s in scans]
    all_rows = align(expected, observed, a.tolerance)
    rows = trim_edges(all_rows, a.edge)
    counts = Counter(r[2] for r in rows)

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = a.out or f'results/csv/detection_check_{stamp}.csv'
    write_csv(out, scans, observed, rows)

    # 값 분포를 함께 출력한다. 범위가 좁으면 로봇이 멈춘 채 비교했다는 뜻이다
    finite = [e for e in expected if e is not None and math.isfinite(e)]
    print(f'스캔 {len(scans)}건, 발행 {len(observed)}건, 양 끝 제외 {len(all_rows) - len(rows)}건')
    for name in (MATCH, MISMATCH, MISSING, EXTRA, NOT_PUBLISHED):
        print(f'{name}: {counts[name]}')
    if finite:
        print(f'유한 거리 범위: {min(finite):.3f} ~ {max(finite):.3f} m')
    print(f'+inf: {expected.count(float("inf"))}, -inf: {expected.count(float("-inf"))}, '
          f'발행 안 함: {expected.count(None)}')
    print(f'CSV: {out}')
    result = verdict(counts)
    print(f'판정: {result}')
    # 종료 코드로도 판정을 알린다
    sys.exit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result])


if __name__ == '__main__':
    main()
```
### ROS 없이 도는 단위 테스트 
검증 스크립트 자체가 맞게 판정하는지 확인하려면 이 테스트가 필요
  스크립트에 버그가 있으면 PASS가 나와도 믿을 수 없기 때문

  1. 시뮬레이션에서 만들기 어려운 상황을 확인할 수 있습니다.
     - 메시지 1건 누락, 값 오류, 전방 전체 NaN, -inf 같은 경우입니다.
     - Gazebo를 정상으로 돌리면 이런 일이 거의 생기지 않습니다. 그래서 스크립트가 이를 FAIL로 잡는지 확인할 기회가 없습니다.
     - 예를 들어 test_detector_not_running_is_not_pass는 detector_node가 꺼져 있을 때 PASS가 나오지 않는지 확인합니다.
  2. 빠르게 반복할 수 있습니다.
     - 시뮬레이션 한 번에 몇 분 걸리지만, 테스트 16건은 0.03초에 끝납니다.
     - 이번에 주석을 달 때도 코드가 깨지지 않았는지 바로 확인했습니다.
  3. ROS가 없는 PC에서도 돌아갑니다.
     - 지금 이 PC에는 ROS 2가 없지만 판정 로직은 여기서 검증했습니다.
  4. 저장소의 기존 방식과 같습니다.
     - test_front_distance.py도 FakeScan으로 Gazebo 없이 거리 계산만 검증합니다.

## 사용 방법

터미널 1: 전체 시스템 실행
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
source install/setup.bash
export TURTLEBOT3_MODEL=burger
ros2 launch obstacle_avoider avoid.launch.py world:=warehouse x_pose:=8.0 y_pose:=0.0


터미널 2: 저장소 루트에서 검증 실행
source /opt/ros/jazzy/setup.bash
python3 scripts/check_detection.py --duration 60

유의 사항 
  - 두 터미널의 ROS_DOMAIN_ID는 같아야 합니다.
  - 로봇이 움직이는 상태에서 돌려야 합니다. 출력의 유한 거리 범위가 좁으면 멈춘 채로 비교한 것이라 검증 의미가 약합니다.
  - front_deg를 바꿔 실행했다면 --front-deg에 같은 값을 넣으세요.
  - 그 밖의 옵션은 --tolerance(기본 0.001 m), --edge(기본 3), --out(CSV 경로)입니다.

## 결과 
화면에 건수와 판정이 나오고, 샘플별 상세는 results/csv/detection_check_<시각>.csv에 저장

  ┌───────────────┬───────────────────────────────┬───────────┐
  │     결과      │             의미                │ 판정 영향 │
  ├───────────────┼───────────────────────────────┼───────────┤
  │ MATCH         │ 값 일치                         │ 정상      │
  ├───────────────┼───────────────────────────────┼───────────┤
  │ NOT_PUBLISHED │ 잘못된 스캔이라 발행하지 않음    │ 정상      │
  ├───────────────┼───────────────────────────────┼───────────┤
  │ MISMATCH      │ 발행됐지만 값이 다름            │ FAIL      │
  ├───────────────┼───────────────────────────────┼───────────┤
  │ MISSING       │ 발행돼야 하는데 없음            │ FAIL      │
  ├───────────────┼───────────────────────────────┼───────────┤
  │ EXTRA         │ 대응하는 스캔이 없는 발행       │ FAIL      │
  └───────────────┴───────────────────────────────┴───────────┘