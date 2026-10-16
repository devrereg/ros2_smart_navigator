# 노드·토픽 인터페이스

> 1일차 완료 기준: 인터페이스 표 초안. B가 `/scan`, C가 `/cmd_vel`을 확인한 뒤 아래 표를 채운다.

| 토픽 | 메시지 타입 | Publisher | Subscriber | QoS | 비고 |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | Gazebo/TurtleBot3 | 장애물 감지 노드 (B) | Reliable, Volatile | Publisher는 `ros_gz_bridge`. 구독 시 QoS를 맞출 것 (아래 참고) |
| `/cmd_vel` | `geometry_msgs/msg/TwistStamped` | 회피 로직 노드 (C) | TurtleBot3 (`ros_gz_bridge`) | Reliable, Volatile | **`Twist`가 아님.** 헤더(`stamp`, `frame_id`)를 채워 발행해야 함 |
| `/benchmark/...` | 미정 (8일차 설계) | experiment_monitor | experiment_monitor | 실험별 가변 | QoS 실험용, 주행 토픽과 분리 |

## 확인된 사항 (A, ROS 2 Jazzy + Gazebo Harmonic, TurtleBot3 기본 월드)

- `ros_gz_bridge` 실행 로그에서 `cmd_vel (geometry_msgs/msg/TwistStamped) -> cmd_vel (gz.msgs.Twist)`와 `scan (gz.msgs.LaserScan) -> scan (sensor_msgs/msg/LaserScan)`을 확인했다.
- 회피 노드(C)는 속도 명령을 `TwistStamped`로 발행해야 한다. `Twist`로 발행하면 로봇이 움직이지 않는다.
- 속도 값은 `msg.twist.linear.x`, `msg.twist.angular.z`에 넣는다. (`Twist`와 달리 `twist` 필드 안에 있다.)
- `msg.header.stamp`는 `self.get_clock().now().to_msg()`로 채운다. 시뮬레이션 시간을 쓰려면 `use_sim_time`을 `true`로 설정한다.
- `/scan` Publisher(`ros_gz_bridge`)의 QoS는 `ros2 topic info /scan --verbose`로 확인했다: Reliability `RELIABLE`, Durability `VOLATILE`, Lifespan·Deadline `Infinite`, Liveliness `AUTOMATIC` (History depth는 `UNKNOWN`으로 표시됨).
- 구독 노드(B)의 QoS가 Publisher보다 엄격하면(예: Subscriber가 `TRANSIENT_LOCAL`) 메시지를 받지 못한다. 기본 QoS(`Reliable`, `Volatile`)로 구독하면 호환된다.
- `/cmd_vel`도 확인했다(`teleop_keyboard` 실행 중). Subscriber(`ros_gz_bridge`)와 Publisher(`teleop_keyboard`) 모두 Reliability `RELIABLE`, Durability `VOLATILE`, Lifespan·Deadline `Infinite`, Liveliness `AUTOMATIC`이다. 회피 노드(C)도 기본 QoS(`Reliable`, `Volatile`)로 발행하면 호환된다.

> 기존에 안정화한 인터페이스를 우선 유지하고, 변경 시 `docs/branching.md`의 리뷰 기준에 따라 팀에 공유한다.
