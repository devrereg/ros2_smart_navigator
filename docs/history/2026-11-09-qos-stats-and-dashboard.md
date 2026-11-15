# 2026-11-09 — QoS 실험 설계 보완과 테스트 대시보드 (B)

- 브랜치 / 이슈: 미정 (커밋 전 변경사항)

## 변경사항

- `run_experiment.sh`: 기본 반복 3 → 10회, 회차(블록)마다 4조건 순서를 `SEED`로 무작위화, `run_order.csv` 기록, 끝나면 `stats_results.py` 실행.
- `scripts/stats_results.py` 추가: 블록 포함 이원분산분석, 가정 검정, 대응 Wilcoxon 단순효과(Holm), 효과크기·부트스트랩 CI → `stats.csv`.
- `scripts/make_dashboard.py` 추가: 단위 테스트(junit), 센서 회귀, QoS 요약·검정·그래프를 `results/dashboard.html` 한 장으로.
- `tests/test_stats_results.py` 추가. `check_env.sh`·`getting_started.md`에 `python3-scipy` 추가. `qos_experiment.md`에 실험 설계·검정력·분석 절차.

## 결정 사항

- **실험 단위는 실행 1회다.** 메시지 단위로 검정하면 유사반복으로 p값이 부풀기 때문이다.
- **블록 안 무작위화.** 기존 고정 순서는 시간에 따른 변화와 QoS 효과를 구분할 수 없다.
- **조건별 10회.** 3회는 대응 검정 최소 p가 0.25라 유의성 판단이 불가능하고, 10회는 큰 효과 검출력 86%다.
- **단순효과는 같은 회차끼리 짝지어 비교한다.** 짝짓지 않은 검정(Mann-Whitney)은 회차 간 드리프트가 크면 실제 차이를 놓쳤다(가짜 데이터로 확인).
- **scipy 의존성 추가** (팀 확인 필요).

## 미해결

- ROS 2 환경에서 10회 실험을 실행하지 않았다. 통계·대시보드는 가짜 데이터로만 확인했다.
- `plans.md` 7장의 "조건별 최소 3회"는 팀 계획서라 고치지 않았다. 10회로 바꾼 것을 팀에 공유해야 한다.
