# 2026-10-19 — 장애물 감지/회피 분리 및 전방 거리 공통 함수 (A)

- 브랜치: `integrations`
- 계획서 3일차 A 업무(B 노드 통합, 인터페이스 리뷰)의 결과다. 커밋 전 변경사항이다.

## 변경사항

- `obstacle_detector`
  - `front_distance.py` 신규: 전방 최소 유효 거리 계산 공통 함수 `front_min_distance(msg, front_deg)`.
  - `detector_node.py`: 빈 뼈대를 구현. `/scan`을 구독해 `/obstacle/front_distance`(`std_msgs/Float32`)로 발행. 파라미터 `front_deg`(전체 폭, 기본 30).
  - `test/test_front_distance.py` 신규: 공통 함수 단위 테스트 8건.
- `obstacle_avoider/avoider.py`: `/scan` 직접 구독과 거리 계산을 제거하고 `/obstacle/front_distance`를 구독. `front_deg` 파라미터는 `detector_node`로 이동.
- `sensor_monitor/LaserScan_sub.py`: 공통 함수를 호출하도록 변경. 유효값 필터가 반대로 되어 있던 버그(`not math.isfinite`) 수정, flake8 15건 수정.
- `package.xml`: `obstacle_detector`에 `std_msgs`, `obstacle_avoider`의 `sensor_msgs`를 `std_msgs`로 교체, `sensor_monitor`에 `obstacle_detector` 의존성 추가.
- `docs/interfaces.md`, `docs/test_plan.md` 갱신. `test_plan.md`에 장애물 거리별 테스트 케이스(`avoider` 판정 11건, 감지 4건)를 추가했다. 판정 케이스는 `/obstacle/front_distance`를 직접 발행하는 방식이라 Gazebo 없이 재현할 수 있다.
- `obstacle_avoider/launch/avoid.launch.py` 신규: `detector_node`와 `avoider`를 함께 실행. 인자 `sim`(기본 `true`, TurtleBot3 월드 시뮬레이션 포함 여부), `front_deg`(기본 30.0). `package.xml`, `setup.py`에 launch 설치와 실행 의존성 추가. 기본값을 `sim:=true`로 한 이유는 한 줄 명령으로 전체가 뜨게 하려는 것이고, 이미 시뮬레이션이 떠 있으면 `sim:=false`로 노드만 붙인다.
- `.gitignore`에 `__pycache__/`, `*.pyc` 추가, 추적 중이던 `src/sensor_monitor/sensor_monitor/__pycache__/*.pyc` 추적 해제. 빌드 산출물이 커밋에 섞이고 변경 목록을 어지럽히기 때문이다.

## 결정 사항

- **감지와 회피를 토픽으로 분리했다.** 계획서의 핵심 결과물이 "감지 노드"와 "회피 노드" 두 개인데, B와 C가 각자 거리 계산을 갖고 있어 한쪽만 고쳐질 위험이 있었다(`LaserScan_sub`의 필터 버그가 C의 코드에는 없었다). 이후 감지 결과를 별도 토픽으로 볼 수 있어 로그·QoS 실험에도 유리하다.
- **계산은 `obstacle_detector`의 공통 함수 한 곳에 둔다.** `LaserScan_sub`는 삭제하지 않고 같은 함수를 호출하는 디버그용으로 남겼다(B의 작업물 보존).
- **`half` 계산에 `round()`를 사용한다.** `int(radians(15)/radians(1))`이 부동소수점 오차로 14가 되어 ±15° 경계 샘플이 빠졌다. C의 기존 코드에도 같은 문제가 있었고, 공통 함수로 옮기며 함께 해결했다.
- `/scan` 구독자를 문서 기준(감지 노드 하나)에 맞췄다. `avoider`는 `/scan`을 직접 구독하지 않는다.

## 미해결 / 팀 공유 필요

- 변경 범위가 B(`sensor_monitor`)와 C(`avoider`)의 코드에 걸쳐 있다. `main`에 반영한 뒤 회의에서 공유하고 리뷰를 받기로 했다.
- 이 변경 이후 `avoider`는 `detector_node`가 실행 중이어야 동작한다. `avoid.launch.py`로 함께 실행한다. launch 파일은 A가 시뮬레이션에서 실행해 확인했다(구두 확인).
- `detector_node` → `avoider` 연동은 A가 시뮬레이션에서 확인했다(`docs/test_plan.md` 검증 기록, 구두 확인으로 로그·스크린샷 증거는 없음).
