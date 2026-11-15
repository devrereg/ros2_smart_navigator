# 2026-11-03 — 센서 검증 도구와 QoS 실험 파이프라인 (B)

- 브랜치 / 이슈: 미정 (커밋 전 변경사항)

## 변경사항

- `sensor_monitor`: `detection_log`, `sensor_fault_test`, 공유 로직 `scan_check.py` 추가.
- `benchmark_pub`: 매칭 후 2초 대기, 발행 후 2초 대기, 매칭 실패 시 종료 코드 1.
- `benchmark_sub`: `idle_timeout_sec` 추가. 기본값 0은 기존처럼 Ctrl+C까지 수신한다.
- `analyze_results.py`: 여러 파일 입력, 수신율·중복·순서 뒤바뀜·누락 seq 추가, 같은 `run_id`는 덮어쓴다.
- `run_experiment.sh`, `plot_results.py`, `run_sensor_regression.sh`, `summarize_detection.py`, `check_env.sh` 추가.
- 문서: `qos_experiment.md`, `detection.md`, `interfaces.md`, `test_plan.md`, `getting_started.md`.

## 결정 사항

- **벤치마크 노드는 `sensor_monitor`에 둔다.** 이미 구현되어 있고 옮겨도 기능 차이가 없기 때문이다. `experiment_monitor`는 빈 폴더로 남아 있다.
- **`detection_log`는 `front_min_distance`를 호출하지 않고 샘플 각도로 다시 계산한다.** 같은 함수를 쓰면 구간 정의 오류를 찾을 수 없기 때문이다.
- **pub 시작·종료에 대기를 넣었다.** pub 쪽 매칭만 보면 sub 쪽 매칭 전에 보낸 메시지가 유실되고, 발행 직후 노드를 없애면 끝부분이 유실될 수 있어 이를 QoS 차이로 오인할 수 있기 때문이다.
- **그래프 라벨은 영어로 쓴다.** Ubuntu에 한글 글꼴이 없으면 글자가 깨지기 때문이다.

## 미해결

- ROS 2 환경에서 실행하지 않았다. `scan_check.py`, `analyze_results.py`, `plot_results.py`, `summarize_detection.py`만 ROS 없이 시험했고, 노드와 셸 스크립트의 동작은 미확인이다.
- 메시지 크기는 64 바이트 한 조건이다. 크기별 비교는 raw 파일명에 크기가 없어 추가 작업이 필요하다.
