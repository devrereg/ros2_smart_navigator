# 2026-10-20 — detector_node 리베이스 충돌 마커 제거 (A)

- 브랜치 / 이슈: `7-ryubengock` / [#7](https://github.com/devrereg/ros2_smart_navigator/issues/7)
- B, C의 4일차 작업을 `7-ryubengock`에 합치는 리베이스 중 남은 충돌 마커를 제거했다. 커밋 전 변경사항이다.

## 변경사항

- `obstacle_detector/obstacle_detector/detector_node.py`: 리베이스 충돌 마커(`<<<<<<<` 등)가 해결되지 않은 채 커밋·push되어 있었다. `32620e4`(A의 감지/회피 분리 버전)로 되돌렸다.
  - 마커 때문에 Python 문법 오류로 노드가 시작 즉시 종료되었고, `/obstacle/front_distance`가 발행되지 않아 `avoider`가 정지 상태였다.

## 결정 사항

- **충돌 해결 시 B의 이전 버전이 아니라 A의 분리 버전을 택했다.** `avoider`와 `docs/interfaces.md`가 `/obstacle/front_distance` 발행 구조를 전제로 하기 때문이다. B 버전은 거리를 발행하지 않고 로그만 출력하며, `front_min`의 `if` 들여쓰기 오류로 마지막 값 하나만 검사한다.
- 이 과정에서 B 버전의 경계값 로그(`THRESHOLD=0.5`, `is_obstacle`)는 빠졌다. 계획서 4일차 B 업무(감지 로그·경계값 확인)는 A 버전 위에 로그만 추가하는 방식으로 다시 하기로 한다. 방식은 B와 협의한다.

## 미해결

- B에게 충돌 마커가 push된 경위와 경계값 로그 재작업을 알려야 한다.
- B가 이번에 합친 `benchmark_pub/sub`는 QoS 실험용이다. 4일차 B 업무와의 관계를 B에게 확인한다.
- warehouse 맵의 스폰 위치와 시나리오 정리, 실패 사례 기록(공동 D)이 남았다.
