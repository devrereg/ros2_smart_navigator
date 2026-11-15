# 회고

14일차 팀 회고. 각 칸은 팀원이 직접 채운다. 수치는 [`test_plan.md`](test_plan.md)와 `results/dashboard.html`의 실제 결과만 쓴다.

## 목표 대비 결과 (`plans.md` 8장)

| 평가 영역 | 완료 기준 | 결과 | 근거 |
|---|---|---|---|
| 시뮬레이션 환경 | Burger와 월드 정상 실행 | | `run_restart_test.sh` 결과 |
| 장애물 회피 | 10회 중 8회 이상 안전 회피·정지 | 5일차 9/10회. 11일차: | `run_avoid_trials.sh` 성공률·95% CI |
| ROS 2 구조 | 노드·토픽 흐름 설명 | | [`architecture.md`](architecture.md) |
| QoS 실험 | 반복 데이터, CSV, 그래프, 해석 | | `stats.csv`, [`qos_experiment.md`](qos_experiment.md) |
| 문서화 | 실행법, 구조도, 결과 | | README, `docs/` |
| 협업·재현성 | GitHub 이력, 재현 절차 | | PR 목록 |

## 잘된 점 (Keep)

| 담당 | 내용 |
|---|---|
| A | |
| B | |
| C | |

## 문제였던 점 (Problem)

| 담당 | 내용 | 원인 |
|---|---|---|
| A | | |
| B | | |
| C | | |

참고할 기록: 리베이스 후 충돌 마커가 남은 채 push됨 (2026-10-20), `/cmd_vel` 타입 혼동 (`Twist` vs `TwistStamped`), 스폰 위치 불량 2곳, 시작 방향 지정 불가.

## 다음에 시도할 것 (Try)

| 담당 | 내용 |
|---|---|
| A | |
| B | |
| C | |

## 남은 과제

- 정면 ±15도 밖 장애물 대응
- launch 시작 방향(yaw) 인자
- 실제 로봇에서 검증
