# 작업 히스토리 (History)

> 프로젝트의 변경사항, 결정 사항, 남은 작업을 기록한다. 바이브 코딩(Claude Code) 시 **먼저 이 문서를 읽고** 맥락을 파악한 뒤 작업한다.
> 작업 기록은 날짜별 파일로 나누어 이 디렉토리에 저장한다. 이 `README.md`에는 현재 상태 요약과 기록 목록만 둔다.

---

## 현재 상태 요약

| 항목 | 상태 |
|---|---|
| 환경 | ROS 2 Jazzy, Gazebo Sim 8.15.0 (Harmonic), RMW `rmw_fastrtps_cpp` (A 환경 확인 완료) |
| 로봇 / 맵 | TurtleBot3 Burger / 기본 `turtlebot3_world`, `worlds/warehouse.world`(Clearpath) 추가. 실행 시 `world:=<이름>`으로 선택, 추후 자체 제작 맵 예정 |
| 시뮬레이션 실행 | A 환경에서 실행 및 브리지 연결 확인 완료 |
| 구현 코드 | `sensor_monitor`(디버그용 구독), `obstacle_detector`(감지 노드·공통 함수), `obstacle_avoider`(수동 주행·상태 머신 회피). `experiment_monitor`는 빈 폴더 |
| `/scan` | `sensor_msgs/msg/LaserScan`, QoS Reliable·Volatile |
| `/cmd_vel` | **`geometry_msgs/msg/TwistStamped`** (`Twist` 아님), QoS Reliable·Volatile |
| 진행 중 브랜치 | `14-ryubengock` (5일차 통합 테스트, [기록](2026-10-25-day5-integration-test.md)). 이전 `7-ryubengock`: 4일차 B·C 작업 병합 완료, `detector_node.py` 충돌 마커 제거는 커밋 전 상태 ([기록](2026-10-20-detector-conflict-fix.md)). launch 맵 선택은 [기록](2026-10-19-launch-world-arg.md), 감지/회피 분리는 [기록](2026-10-19-detector-topic-split.md) |
| 4~5일차 회피 | warehouse 맵에서 직진 → 장애물 앞 정지(약 0.5 m) → 회피 동작 확인. 5일차 통합 테스트에서 10회 중 9회 안전 (2026-10-25, [검증 기록](../test_plan.md)). `(9.0, -15.0)` 시작에서 접촉 의심 1회, 스폰 불량 위치 2곳이 남음 |
| `/obstacle/front_distance` | `std_msgs/msg/Float32`, `detector_node` → `avoider`, 정면 좌우 15도 최소 유효 거리(없으면 `inf`) |

### 알아야 할 핵심 사실

- `/cmd_vel`은 `TwistStamped`다. 속도는 `msg.twist.linear.x`, `msg.twist.angular.z`에 넣고 `msg.header.stamp`를 채운다.
- Robotnik 월드(`robotnik_gazebo_worlds`)의 `robotnik_lab_world`는 ROS 1(catkin, Gazebo Classic) 기반이라 Jazzy에서 빌드되지 않는다. 사용하지 않는다.
- 통합 실행: `ros2 launch obstacle_avoider avoid.launch.py [world:=<맵 이름>] [spawn_robot:=false] [sim:=false]`. 인자와 실행 순서는 `docs/interfaces.md` 참고. 로봇이 world에 이미 포함된 `worlds/*burger.world`는 `spawn_robot:=false`로 실행한다. `worlds/`에 맵을 추가하면 다시 빌드해야 한다.
- 기본 bridge(`turtlebot3_burger_bridge.yaml`)에 `/scan`, `/cmd_vel` 등이 포함되어 있어 별도 bridge 설정은 필요 없다. 카메라 등 다른 토픽이 필요해지면 추가한다.
- 전방 거리 계산은 `obstacle_detector.front_distance.front_min_distance` 한 곳에만 둔다. `avoider`는 `/scan`을 직접 구독하지 않으므로 `detector_node`를 함께 실행해야 한다.
- 실행 world는 `warehouse`를 쓴다. `worlds/turtlebot3_burger.world`는 센서 플러그인이 없어 `/scan`이 나오지 않으므로 그대로는 쓸 수 없다. `spawn_robot:=false`여도 bridge는 launch가 따로 실행한다.
- `colcon build`는 Python 문법 오류를 잡지 못한다. 병합·리베이스 후에는 충돌 마커(`grep -rn "^<<<<<<<" src`)가 남았는지 확인하고 실제로 실행해 본다.
- Jazzy의 `ros2`는 `--version` 옵션을 지원하지 않는다. 버전은 `ros2 doctor --report`로 확인한다.

### 남은 작업 / 열린 질문

- [x] `worlds/turtlebot3_burger.world`의 로봇 경로를 `model://turtlebot3_burger`로 수정 (센서 플러그인 누락은 미해결, 아래 참고)
- [ ] `worlds/turtlebot3_burger.world`에 `gz-sim-sensors-system` 플러그인 추가 (이 world를 쓸 때만 필요, 현재는 `warehouse` 사용)
- [ ] warehouse 맵 스폰 위치·시나리오 정리 (사용 불가: `(5.0, -6.0)`, `(-8.0, -8.0)`), launch에 시작 방향(yaw) 인자 추가 검토
- [ ] `(9.0, -15.0)` 시작에서 최소 거리 0.12 m가 나온 원인 확인 (C·B), 정면 ±15도 밖 장애물 대응 범위 논의
- [ ] B에게 충돌 마커 push 경위 공유, 경계값 로그를 A 버전 `detector_node` 위에 다시 추가 (4일차 B 업무), `benchmark_pub/sub`와의 관계 확인
- [ ] 맵 제작 방향 확정 (팀원과 상의, 담당·일정 미정)
- [ ] B, C의 `docs/environment.md` 환경 기록 표 채우기
- [ ] 클린 환경에서 `docs/getting_started.md`의 설치 절차 검증
- [ ] 회의에서 B·C에게 감지/회피 분리 변경 공유 및 리뷰 (`main` 반영 후) (시뮬레이션 연동은 2026-10-19 A가 확인 완료, `docs/test_plan.md` 검증 기록 참고)

---

## 기록 목록 (최신순)

| 날짜 | 담당 | 제목 | 파일 |
|---|---|---|---|
| 2026-10-25 | A | 5일차 통합 테스트 결과 기록 (정지·회피 9/10회) | [2026-10-25-day5-integration-test.md](2026-10-25-day5-integration-test.md) |
| 2026-10-20 | A | burger.world 경로 수정, spawn_robot:=false 시 bridge 누락 수정 | [2026-10-20-world-path-and-bridge.md](2026-10-20-world-path-and-bridge.md) |
| 2026-10-20 | A | detector_node 리베이스 충돌 마커 제거 | [2026-10-20-detector-conflict-fix.md](2026-10-20-detector-conflict-fix.md) |
| 2026-10-19 | A | launch 맵 선택 인자와 warehouse 맵 추가, 4일차 통합 실행 점검 | [2026-10-19-launch-world-arg.md](2026-10-19-launch-world-arg.md) |
| 2026-10-19 | A | 장애물 감지/회피 분리 및 전방 거리 공통 함수 | [2026-10-19-detector-topic-split.md](2026-10-19-detector-topic-split.md) |
| 2026-10-16 | A | 환경 확인 및 맵 변경, 문서 정비 | [2026-10-16-env-and-map-change.md](2026-10-16-env-and-map-change.md) |

---

## 작성 규칙

Claude Code로 작업할 때 이 디렉토리를 아래 방식으로 관리한다.

1. **작업 시작 전:** 이 `README.md`의 "현재 상태 요약"과 "남은 작업", 그리고 최신 기록 파일을 읽는다.
2. **작업 후:** 새 기록 파일을 만든다.
   - 파일명: `YYYY-MM-DD-<영문-소문자-요약>.md` (예: `2026-10-17-scan-subscriber.md`). 같은 날 여러 개면 요약으로 구분한다.
   - 첫 줄: `# YYYY-MM-DD — 제목 (담당자)`
   - 포함할 것: 브랜치/이슈, **변경사항**(코드·문서·설정 등 저장소에 반영된 변경), 결정 사항과 **이유**, 미커밋 변경.
   - 제외할 것: 실행·동작 확인, 버전 확인, 테스트 실행 같은 **확인 작업** 자체. 확인 결과가 앞으로 작업에 영향을 주는 핵심 사실이면 "현재 상태 요약"의 "알아야 할 핵심 사실"에 적는다.
   - 코드나 git 로그에서 알 수 있는 단순 변경 나열은 피하고, 나중에 맥락이 필요한 내용 위주로 쓴다.
3. **README 갱신:** "기록 목록" 표 맨 위에 새 행을 추가하고, "현재 상태 요약"과 "남은 작업"을 최신 상태로 고친다. 끝난 항목은 체크하거나 지운다.
4. **프로젝트와 관련된 내용만 기록한다.** 개인 PC의 환경 설정(`~/.bashrc` 수정, 계정 로그인, 패키지 설치 등)과 git에 올라가지 않는 로컬 파일(`.claude/` 등 `.gitignore` 대상)의 내용은 쓰지 않는다. 팀원에게 필요한 설정 절차는 `docs/getting_started.md`에 둔다.
5. **추측과 사실을 구분한다.** 핵심 사실 중 확인하지 않은 내용은 "미확인"이라고 적는다.
6. 기존 기록 파일은 과거 사실이므로 고치지 않는다. 틀린 내용이 있으면 새 기록에서 정정한다.
