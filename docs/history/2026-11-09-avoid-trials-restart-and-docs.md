# 2026-11-09 — 회피 성공률·재실행 시험 도구와 A·C·공동 문서 (A·C·공동)

- 브랜치 / 이슈: 미정 (커밋 전 변경사항)

## 변경사항

- `sensor_monitor/avoid_trial.py` 추가 (C·A, 11일차): 자동 주행 1회를 감시해 판정. 5일차에 저장소 밖 스크립트로 하던 감시를 노드로 옮겼다. 판정 로직 `trial_verdict`는 `scan_check.py`에 두고 단위 테스트를 붙였다. `package.xml`에 `geometry_msgs`, `nav_msgs` 추가.
- `scripts/run_avoid_trials.sh`, `scripts/summarize_trials.py` 추가 (C, 11일차): 10곳 × 3회 무작위 순서 실행, 성공률과 Clopper-Pearson 95% CI.
- `scripts/run_restart_test.sh` 추가 (A, 11일차): 실행·종료·재실행 반복과 잔여 프로세스 확인.
- `make_dashboard.py`: 회피 성공률, 재실행 결과 추가.
- 문서: `architecture.md`(A, 12일차), `avoidance.md`(C, 12일차), `presentation.md`(13일차, A·B·C·공동 예상 질문과 시연 절차), `retrospective.md` 틀(14일차), `test_plan.md` F·G절, `interfaces.md`, README.

## 결정 사항

- **회피 시험은 30회로 늘렸다.** 9/10회는 95% CI 하한이 56%라 목표 80% 충족을 말할 수 없다. 29/30 이상이면 하한이 83%다.
- **판정 기준은 5일차와 같게 두었다** (접촉 의심 0.15 m, 정지 동작 미발동·스폰 끼임은 제외). 기준을 바꾸면 5일차 결과와 비교할 수 없기 때문이다.
- **시점별 기록(`avoid_trace_*.csv`)을 남긴다.** 5일차 0.12 m 원인을 찾으려면 최소 거리가 나온 방향과 그때의 명령이 필요하기 때문이다.
- **시작 방향(yaw) 인자는 추가하지 않았다.** TurtleBot3 스폰 launch가 yaw를 받지 않아 스폰·bridge를 직접 구성해야 하는데, ROS 환경 없이 확인할 수 없어 범위에서 뺐다.
- **회고와 결과 수치는 비워 두었다.** 팀원 경험과 실측이 필요하다.

## 미해결

- 새 노드와 셸 스크립트는 ROS 2 환경에서 실행하지 않았다 (문법 검사와 순수 로직 단위 테스트만 통과).
- `media/demo/` 녹화본, 발표 자료 파일은 시연 후 만들어야 한다.
