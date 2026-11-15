# 시스템 아키텍처

12일차 A 작성. 토픽 타입·QoS·launch 인자의 세부 값은 [`interfaces.md`](interfaces.md), 계획은 `plans.md` 4장 참고.

## 전체 구조

주행 기능과 QoS 실험은 토픽과 `ROS_DOMAIN_ID`로 분리되어 서로 영향을 주지 않는다.

```text
[주행]  Gazebo(warehouse + TurtleBot3 Burger)
          │ gz /scan, /odom                       ▲ gz /cmd_vel
          ▼                                       │
        ros_gz_bridge ───────────────────────────┘
          │ /scan (LaserScan, 5 Hz)      │ /odom (Odometry)
          ▼                              │
        detector_node (B)                │
          │ /obstacle/front_distance     │
          ▼ (Float32)                    ▼
        avoider (C) ── 상태 머신 + 정지 감지 ──> /cmd_vel (TwistStamped)

[검증]  detection_log, avoid_trial, sensor_fault_test (sensor_monitor) ── /scan 등을 따로 구독해 CSV 기록

[실험]  benchmark_pub ── /benchmark/data (UInt8MultiArray, QoS 가변) ──> benchmark_sub   (ROS_DOMAIN_ID 78)
```

## 패키지와 책임

| 패키지 | 노드 / 모듈 | 담당 | 책임 |
|---|---|---|---|
| `obstacle_detector` | `detector_node`, `front_distance.front_min_distance` | B | `/scan` 정면 ±15도의 최소 유효 거리 계산·발행. 특수값 규칙(REP 117)은 [`detection.md`](detection.md) |
| `obstacle_avoider` | `avoider`, `safety.StuckDetector`, `manual_drive` | C | 거리 기반 상태 머신, 정지 감지와 복구, `/cmd_vel` 발행. [`avoidance.md`](avoidance.md) |
| `obstacle_avoider` | `launch/avoid.launch.py` | A | 시뮬레이션·bridge·감지·회피를 한 번에 실행 |
| `sensor_monitor` | `detection_log`, `sensor_fault_test`, `avoid_trial`, `scan_check` | B·C | 감지 결과 대조, 이상값 회귀, 회피 시험 판정. 판정 로직은 ROS 없이 시험 가능한 `scan_check.py`에 둔다 |
| `sensor_monitor` | `benchmark_pub`, `benchmark_sub` | 공동 | QoS 실험. [`qos_experiment.md`](qos_experiment.md) |
| `scripts/` | 실행·분석·대시보드 | 공동 | 아래 "검증·실험 흐름" |

계획서의 `experiment_monitor` 패키지는 비어 있다. 벤치마크 노드를 이미 구현된 `sensor_monitor`에 두었기 때문이다 (2026-11-03 결정).

## 설계 결정

| 결정 | 이유 |
|---|---|
| 감지(`detector_node`)와 회피(`avoider`)를 노드로 분리하고 `Float32` 거리 하나로 연결 | 각자 따로 시험할 수 있다. `avoider`는 거리를 직접 발행해 Gazebo 없이 시험한다 (`test_plan.md` A절) |
| 전방 거리 계산은 `front_min_distance` 한 곳에만 둔다 | 노드마다 계산이 달라지는 것을 막는다 |
| 검증 노드(`detection_log`)는 같은 함수를 쓰지 않고 각도로 다시 계산 | 같은 함수로 비교하면 구간 정의 오류를 찾을 수 없다 |
| 전방 전체가 `NaN`이면 발행하지 않는다 | `avoider`가 `scan_timeout`(0.5초) 후 안전 정지한다. 측정 실패를 "장애물 없음"으로 오인하지 않는다 |
| `/cmd_vel`은 `TwistStamped` | Jazzy + Harmonic의 `ros_gz_bridge` 설정. `Twist`로 보내면 로봇이 움직이지 않는다 |
| 실험·회귀 시험은 각자 다른 `ROS_DOMAIN_ID` (77~80) | 가짜 `/scan`이나 벤치마크 트래픽이 주행·다른 시험과 섞이지 않게 한다 |

## 실행 방법

```bash
colcon build --symlink-install && source install/setup.bash
bash scripts/check_env.sh                       # 의존성 점검, 모두 OK여야 함
ros2 launch obstacle_avoider avoid.launch.py world:=warehouse x_pose:=8.0 y_pose:=0.0
```

launch 실행 순서: Gazebo 서버·GUI → `robot_state_publisher` → 로봇 스폰 + `ros_gz_bridge` → `detector_node`, `avoider`. 센서 데이터가 오기 전에는 `avoider`가 정지 상태로 기다린다.

## 검증·실험 흐름

| 목적 | 명령 | 결과 |
|---|---|---|
| 단위 테스트 | `colcon test` 또는 `python3 -m pytest tests --junitxml=results/junit.xml` | `build/*/pytest.xml`, `results/junit.xml` |
| 감지 결과 대조 (B) | `ros2 run sensor_monitor detection_log` → `summarize_detection.py` | `results/csv/detection_log.csv` |
| 센서 이상값 회귀 (B) | `bash scripts/run_sensor_regression.sh \| tee results/csv/sensor_regression.md` | 14개 시나리오 |
| 회피 성공률 (C) | `bash scripts/run_avoid_trials.sh` | `results/csv/avoid/` |
| 실행·종료·재실행 (A) | `bash scripts/run_restart_test.sh \| tee results/csv/restart_test.md` | 회차별 기동·종료·잔여 프로세스 |
| QoS 실험 (공동) | `bash scripts/run_experiment.sh` → `plot_results.py` | `summary.csv`, `stats.csv`, 그래프 |
| 전체 요약 | `python3 scripts/make_dashboard.py` | `results/dashboard.html` |

## 알려진 한계

- 정면 ±15도 밖의 장애물은 감지·회피하지 않는다. 회전 중 측면 접촉 가능성이 있다 (5일차 `(9.0, -15.0)` 회차).
- 시작 방향(yaw)을 launch에서 지정할 수 없다. TurtleBot3 스폰 launch가 `x_pose`, `y_pose`만 받기 때문이며, 벽·코너 시나리오는 시작 위치로만 만든다.
- `/obstacle/front_distance`는 `Float32`라 타임스탬프가 없다. 검증 노드는 수신 시각으로 짝짓는다.
- 시뮬레이션에서만 검증했다. 실제 로봇의 센서 잡음·지연은 반영되지 않았다.
