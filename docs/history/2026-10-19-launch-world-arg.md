# 2026-10-19 — launch 맵 선택 인자와 warehouse 맵 추가, 4일차 통합 실행 점검 (A)

- 브랜치 / 이슈: `7-ryubengock` / [#7](https://github.com/devrereg/ros2_smart_navigator/issues/7)
- 계획서 4일차 A 업무(통합 실행 순서와 노드 간 데이터 흐름 점검)의 결과다. 커밋 전 변경사항이다.

## 변경사항

- `obstacle_avoider/launch/avoid.launch.py`
  - 인자 `world`(기본 `turtlebot3_world`), `spawn_robot`(기본 `true`), `x_pose`, `y_pose` 추가.
  - `turtlebot3_world.launch.py`를 통째로 포함하던 방식을 버리고, Gazebo 서버·GUI, `robot_state_publisher`, 로봇 스폰(`spawn_turtlebot3.launch.py`, bridge 포함)을 직접 구성. `world`는 경로 또는 이름으로 받아 `obstacle_avoider/worlds` → `turtlebot3_gazebo/worlds` 순으로 찾고, 못 찾으면 사용 가능한 목록과 함께 오류를 낸다.
- `obstacle_avoider/setup.py`: 저장소 루트 `worlds/*.world`를 `share/obstacle_avoider/worlds`로 설치.
- `worlds/warehouse.world` 신규: Clearpath `clearpath_simulator`의 `clearpath_gz/worlds/warehouse.sdf`(BSD-3-Clause)를 확장자만 바꿔 추가. 로봇이 포함되지 않은 월드다.
- `docs/interfaces.md`: "통합 실행 순서와 데이터 흐름", launch 인자 표 추가.

## 결정 사항

- **`turtlebot3_world.launch.py`를 포함하지 않고 직접 구성했다.** 그 파일은 월드 경로가 코드에 박혀 있어 인자로 맵을 바꿀 수 없기 때문이다. 스폰과 bridge는 기존 `spawn_turtlebot3.launch.py`를 그대로 재사용한다.
- **별도 bridge 설정은 만들지 않았다.** 기본 `turtlebot3_burger_bridge.yaml`에 `/scan`, `/cmd_vel` 등 현재 필요한 토픽이 모두 있다.
- **`worlds/`를 패키지로 옮기지 않고 `setup.py`에서 `../../worlds`를 참조한다.** 팀이 이미 루트 `worlds/`를 쓰고 있어 구조를 바꾸지 않기 위해서다. colcon이 패키지 디렉토리에서 `setup.py`를 실행한다는 점에 의존한다.
- **맵으로 Clearpath warehouse를 선택했다.** Jazzy + Harmonic에서 쓸 수 있는 SDF 월드이고 장애물 회피 시험에 적합한 구조이기 때문이다.

## 미해결

- `worlds/turtlebot3_burger.world`는 로봇 경로가 `file:///home/taeho-kim/...`로 박혀 있어 다른 PC에서 로드되지 않는다. `model://turtlebot3_burger`로 고쳐야 한다. (이번 변경에서는 손대지 않았다.)
- warehouse에서 장애물 앞 회피 동작은 아직 확인하지 않았다. 스폰 위치와 주행 시나리오가 필요하다.
- 4일차 B(감지 로그·경계값), C(상태 로직)는 해당 담당자 몫이다.
