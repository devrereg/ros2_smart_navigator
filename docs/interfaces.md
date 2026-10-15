# 노드·토픽 인터페이스

> 1일차 완료 기준: 인터페이스 표 초안. B가 `/scan`, C가 `/cmd_vel`을 확인한 뒤 아래 표를 채운다.

| 토픽 | 메시지 타입 | Publisher | Subscriber | QoS | 비고 |
|---|---|---|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` (확인 필요) | Gazebo/TurtleBot3 | 장애물 감지 노드 (B) | 확인 필요 | `ros2 topic info /scan`으로 확정 |
| `/cmd_vel` | `geometry_msgs/msg/Twist` 또는 `TwistStamped` (확인 필요) | 회피 로직 노드 (C) | TurtleBot3 | 확인 필요 | `ros2 topic info /cmd_vel`으로 확정 |
| `/benchmark/...` | 미정 (8일차 설계) | experiment_monitor | experiment_monitor | 실험별 가변 | QoS 실험용, 주행 토픽과 분리 |

> 기존에 안정화한 인터페이스를 우선 유지하고, 변경 시 `docs/branching.md`의 리뷰 기준에 따라 팀에 공유한다.
