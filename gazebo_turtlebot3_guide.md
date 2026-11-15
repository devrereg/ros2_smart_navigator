# Gazebo Sim 8 + TurtleBot3 Burger 완전 가이드

## 목차

1. [환경 구조](#1-환경-구조)
2. [Gazebo 실행 방법](#2-gazebo-실행-방법)
3. [빈 world에 TurtleBot3 추가](#3-빈-world에-turtlebot3-추가)
4. [객체 이동 방법](#4-객체-이동-방법)
5. [센서 데이터 수신](#5-센서-데이터-수신)
6. [로봇 수동 제어](#6-로봇-수동-제어)
7. [치트시트](#7-치트시트)
8. [문제 해결](#8-문제-해결)

---

## 1. 환경 구조

```
~/turtlebot3_ws/
├── models/
│   ├── turtlebot3_burger/
│   │   ├── model.config
│   │   ├── model.sdf
│   │   └── model-1_4.sdf
│   └── turtlebot3_common/
│       └── meshes/...
└── worlds/
    ├── empty_burger.world      # 빈 world + 터틀봇3 포함
    └── turtlebot3_burger.world # 원본 world
```

원본 모델 경로: `~/turtlebot3_burger/turtlebot3_simulations/turtlebot3_gazebo/models/`

---

## 2. Gazebo 실행 방법

```bash
cd $HOME/turtlebot3_ws/models
gz sim -s -v 3 $HOME/turtlebot3_ws/worlds/empty_burger.world
```

**주의:** 반드시 `models/` 디렉토리에서 실행해야 `model://` URI가 정상 해석됩니다.

### 환경변수 설정 (대안)

```bash
export GZ_SIM_RESOURCE_PATH=$HOME/turtlebot3_ws/models
```

`export` 후 별도 명령으로 실행하면 `gz` Ruby 래퍼가 환경변수를 전달하지 못할 수 있으므로, `env` 명령어를 사용하거나 `cd` 방식을 권장합니다.

---

## 3. 빈 world에 TurtleBot3 추가

### 방법 1: world 파일에 `<include>` 추가

```xml
<include>
  <uri>model://turtlebot3_burger</uri>
  <pose>0 0 0.1 0 0 0</pose>
</include>
```

`<pose>`로 위치/회전을 지정할 수 있습니다. 여러 대 넣고 싶으면 `<include>`을 여러 번 사용합니다.

### 방법 2: GUI Insert

1. Gazebo GUI 실행
2. 왼쪽 **Insert** 탭 클릭
3. `turtlebot3_burger` 선택
4. 3D 뷰에서 원하는 위치 클릭

### 방법 3: 서비스로 런타임 스폰

```bash
gz service -s /world/empty_world/create \
  --reqtype gz.msgs.Entity --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "burger2", type: MODEL'
```

---

## 4. 객체 이동 방법

### 방법 1: GUI에서 마우스로 이동

| 키 | 기능 |
|----|------|
| `T` | 이동 (Translate) 모드 |
| `R` | 회전 (Rotate) 모드 |
| `S` | 크기 조절 (Scale) 모드 |

선택 후 RGB 핸들(빨강=X, 초록=Y, 파랑=Z축)을 마우스로 드래그합니다.

**정밀 이동:** Entities 패널 → 객체 우클릭 → **Edit → Translation** 값 직접 입력

### 방법 2: 서비스로 이동

```bash
# 단일 객체 이동
gz service -s /world/empty_world/set_pose \
  --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'name: "turtlebot3_burger", position: {x: 1.0, y: 2.0, z: 0.1}'

# 여러 객체 동시 이동
gz service -s /world/empty_world/set_pose_vector \
  --reqtype gz.msgs.Pose_V --reptype gz.msgs.Boolean --timeout 3000 \
  --req 'pose: [
    {name: "turtlebot3_burger", position: {x: 1.0, y: 0.0, z: 0.1}},
    {name: "ground_plane", position: {x: 0.0, y: 0.0, z: 0.0}}
  ]'
```

### 방법 3: 물리 기반 이동

모델에 `DiffDrive` 플러그인이 있어 `cmd_vel` 토픽으로 이동할 수 있습니다:

```bash
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}, angular: {z: 0.1}'
```

---

## 5. 센서 데이터 수신

### 터미널 1: 서버 실행

```bash
cd $HOME/turtlebot3_ws/models
gz sim $HOME/turtlebot3_ws/worlds/empty_burger.world 

gz sim -s $HOME/turtlebot3_ws/worlds/empty_burger.world # 센서 제어만
	-v 로그출력 상세화
```

### 터미널 2: 센서 데이터 수신

```bash
# 토픽 목록 확인
gz topic -l

# IMU 데이터 (가속도, 각속도, 방향)
gz topic -e -t /imu

# LiDAR 데이터 (거리 배열)
gz topic -e -t /scan 
# 라이다 플러그인 설치 필수 sudo apt install -y gz-sim8-gpu-lidar-system gz-sensors8-gpu-lidar 2>&1 | tail -20

# 로봇 위치/자세 (Odometry)
gz topic -e -t /odom

# 관절 상태 (휠 위치, 속도)
gz topic -e -t /joint_states
```

### IMU 출력 예시

```
header {
  stamp { sec: 123 nsec: 456 }
  frame_id: "turtlebot3_burger/imu_link"
}
orientation { x: 0 y: 0 z: 0 w: 1 }
angular_velocity { x: 0 y: 0 z: 0.1 }
linear_acceleration { x: 0.2 y: 0 z: 9.81 }
```

### LiDAR 토픽이 없을 때

gz-sim 8에는 기본적으로 LiDAR 시스템 플러그인이 포함되어 있지 않습니다.

```bash
sudo apt update
sudo apt install gz-sensors8-gpu-lidar gz-sim8-gpu-lidar-system
```

설치 후 확인:

```bash
ls /usr/lib/x86_64-linux-gnu/gz-sim-8/plugins/ | grep -i lidar
```

플러그인 추가 하기:
월드 파일에 플러그인 항목에 추가 하기

---

## 6. 로봇 수동 제어

### 방법 A: `gz topic` 명령 (테스트용)

```bash
# 직진 (0.2 m/s)
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}'

# 회전 (0.5 rad/s)
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'angular: {z: 0.5}'

# 직진 + 회전
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}, angular: {z: 0.5}'

# 정지
gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.0}, angular: {z: 0.0}'
```

### 방법 B: GUI에서 제어

```bash
cd $HOME/turtlebot3_ws/models
gz sim $HOME/turtlebot3_ws/worlds/empty_burger.world
```

- 왼쪽 패널 → **Joint** 탭에서 각 관절에 속도 입력
- 또는 **Translate/Rotate** 모드(`T`/`R`)로 로봇을 직접 드래그

### 방법 C: ROS 2 토픽 (ROS 2 연동 시)

```bash
# 제어
ros2 topic pub /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.2}, angular: {z: 0.1}}" -r 10

# 센서 데이터 수신
ros2 topic echo /imu
ros2 topic echo /scan
```

---

## 7. 치트시트

| 작업     | 명령어                                                                                                                                                             |
| ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 토픽 목록  | `gz topic -l`                                                                                                                                                   |
| 데이터 수신 | `gz topic -e -t <토픽명>`                                                                                                                                          |
| 데이터 발행 | `gz topic -t <토픽> -m <타입> -p '<내용>'`                                                                                                                            |
| 이동     | `gz topic -t /cmd_vel -m gz.msgs.Twist -p 'linear: {x: 0.2}'`                                                                                                   |
| 서비스 목록 | `gz service --list`                                                                                                                                             |
| 서비스 호출 | `gz service -s <서비스> --reqtype <타입> --req '<내용>'`                                                                                                               |
| 객체 이동  | `gz service -s /world/<world>/set_pose --reqtype gz.msgs.Pose --reptype gz.msgs.Boolean --timeout 3000 --req 'name: "객체명", position: {x: 1.0, y: 0.0, z: 0.1}'` |

---

## 8. 문제 해결

| 문제 | 원인 | 해결 |
|------|------|------|
| `Could not find model.config` | CWD가 models/가 아님 | `cd $HOME/turtlebot3_ws/models` 후 실행 |
| `model://` URI 해석 실패 | 환경변수 미설정 | `cd`로 models/ 이동 |
| `/scan` 토픽 없음 | LiDAR 플러그인 미설치 | `sudo apt install gz-sim8-gpu-lidar-system` |
| `export` 후 환경변수 미전달 | gz Ruby 래퍼 문제 | `env GZ_SIM_RESOURCE_PATH=...` 또는 `cd` 사용 |


# 9. 브리지
ros2 run ros_gz_bridge parameter_bridge scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan


# 10. scan 정보
ros2 interface show sensor_msgs/msg/LaserScan 
```

# Single scan from a planar laser range-finder
#
# If you have another ranging device with different behavior (e.g. a sonar
# array), please find or create a different message, since applications
# will make fairly laser-specific assumptions about this data

std_msgs/Header header # timestamp in the header is the acquisition time of
	builtin_interfaces/Time stamp
		int32 sec
		uint32 nanosec
	string frame_id
                             # the first ray in the scan.
                             #
                             # in frame frame_id, angles are measured around
                             # the positive Z axis (counterclockwise, if Z is up)
                             # with zero angle being forward along the x axis

float32 angle_min            # start angle of the scan [rad]
float32 angle_max            # end angle of the scan [rad]
float32 angle_increment      # angular distance between measurements [rad]

float32 time_increment       # time between measurements [seconds] - if your scanner
                             # is moving, this will be used in interpolating position
                             # of 3d points
float32 scan_time            # time between scans [seconds]

float32 range_min            # minimum range value [m]
float32 range_max            # maximum range value [m]

float32[] ranges             # range data [m]
                             # (Note: values < range_min or > range_max should be discarded)
float32[] intensities        # intensity data [device-specific units].  If your
                             # device does not provide intensities, please leave
                             # the array empty.

```
ros2 topic info /scan -v
```

Type: sensor_msgs/msg/LaserScan

Publisher count: 1

Node name: ros_gz_bridge
Node namespace: /
Topic type: sensor_msgs/msg/LaserScan
Topic type hash: RIHS01_64c191398013af96509d518dac71d5164f9382553fce5c1f8cca5be7924bd828
Endpoint type: PUBLISHER
GID: 01.0f.05.8b.bc.1a.7d.31.00.00.00.00.00.00.14.03
QoS profile:
  Reliability: RELIABLE #신뢰 중심
  History (Depth): UNKNOWN #???
  Durability: VOLATILE # 연결된 이후에 데이터를 받음
  Lifespan: Infinite
  Deadline: Infinite
  Liveliness: AUTOMATIC
  Liveliness lease duration: Infinite

Subscription count: 0

```
ros2 topic hz /scan
```
average rate: 1.226
	min: 0.186s max: 66.671s std dev: 5.93042s window: 129
average rate: 1.261
	min: 0.186s max: 66.671s std dev: 5.81989s window: 134
average rate: 1.303
	min: 0.186s max: 66.671s std dev: 5.69508s window: 140
```


```
 ros2 topic echo /scan --once --field range_min
0.11999999731779099
---
taeho-kim@taeho-kim-750XED:~
❯ ros2 topic echo /scan --once --field range_max
3.5
---
taeho-kim@taeho-kim-750XED:~
❯  ros2 topic echo /scan --once --field angle_min
0.0
---
taeho-kim@taeho-kim-750XED:~
❯  ros2 topic echo /scan --once --field angle_max
6.28000020980835
---
taeho-kim@taeho-kim-750XED:~
❯  ros2 topic echo /scan --once --field angle_increment
0.01749303564429283
---
taeho-kim@taeho-kim-750XED:~
❯ ros2 topic echo /scan --once --field range
Invalid field 'range': 'LaserScan' object has no attribute 'range'
taeho-kim@taeho-kim-750XED:~ [1]
❯ ros2 topic echo /scan --once --field ranges
array('f', [inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf, inf])
---
```

  ┌───────────────────────┬────────────────────┬──────────────────────────────────────────────┐
  │         항목          │         값         │                     의미                     │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ angle_min / angle_max │ 0 ~ 6.28 rad       │ 0°부터 한 바퀴(360°)를 스캔                  │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ angle_increment       │ 0.0175 rad         │ 약 1° 간격, 데이터 360개                     │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ 정면                  │ ranges[0]          │ 0 rad가 정면(x축)                            │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ range_min / range_max │ 0.12 ~ 3.5 m       │ 이 범위를 벗어난 값은 무시                   │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ ranges가 전부 inf     │ —                  │ 3.5 m 안에 물체가 없다는 뜻이고, 고장이 아님 │
  ├───────────────────────┼────────────────────┼──────────────────────────────────────────────┤
  │ QoS                   │ RELIABLE, VOLATILE │ 구독에 기본값(depth 10)을 써도 맞음          │
  └───────────────────────┴────────────────────┴──────────────────────────────────────────────┘


  # recode