# DDS QoS 실험

세부 설계는 `plans.md` 7장 참고. 결과 절은 측정 후 실제 값으로 채운다.

## 센서 토픽과 실험 토픽의 QoS 차이

| 항목 | `/scan` (주행) | `/benchmark/data` (실험) | `qos_profile_sensor_data` (참고) |
|---|---|---|---|
| Reliability | RELIABLE | 조건별 RELIABLE / BEST_EFFORT | BEST_EFFORT |
| Durability | VOLATILE | VOLATILE | VOLATILE |
| History | Publisher depth 미확인 (`UNKNOWN` 표시), 구독 KEEP_LAST 10 | KEEP_LAST 10 | KEEP_LAST 5 |
| 메시지 타입 | `sensor_msgs/msg/LaserScan` | `std_msgs/msg/UInt8MultiArray` | - |
| 주기 | 5 Hz (`model.sdf`) | 10 / 50 Hz | - |

`/scan`은 `ros_gz_bridge`가 RELIABLE로 발행하므로 `detector_node`는 기본 QoS로 구독한다. 실험은 별도 토픽에서 하므로 주행 토픽의 QoS는 바꾸지 않는다.

Reliability 호환성:

| Publisher \ Subscriber | RELIABLE | BEST_EFFORT |
|---|---|---|
| RELIABLE | 연결 (재전송 있음) | 연결 (재전송 없음) |
| BEST_EFFORT | **연결 안 됨** | 연결 (재전송 없음) |

연결 안 됨을 직접 확인하려면 sub를 `reliable`, pub을 `best_effort`로 실행한다. pub이 30초 뒤 매칭 실패 오류로 끝나고, `ros2 topic info -v /benchmark/data`에 양쪽 QoS가 표시된다.

## 실험 조건

| 항목 | 값 |
|---|---|
| Reliability | RELIABLE, BEST_EFFORT (pub·sub 같은 값) |
| 발행 주기 | 10 Hz, 50 Hz |
| 메시지 크기 | 64 바이트 |
| 실험 시간 | 조건별 30초 |
| 반복 | 조건별 10회 (블록 10개 × 4조건 = 40회, 약 25분) |
| 실행 순서 | 블록(회차)마다 4조건 순서를 무작위로 섞음, `SEED`와 순서는 `run_order.csv`에 기록 |
| 실행 환경 | 한 컴퓨터, Gazebo 미실행, 별도 `ROS_DOMAIN_ID` |

## 실험 설계와 통계 분석

계획서(`plans.md` 7장)의 "조건별 최소 3회"는 평균 비교만 가능하고 유의성은 판단할 수 없어 아래처럼 보완했다.

| 항목 | 이전 | 보완 | 이유 |
|---|---|---|---|
| 실험 단위 | (명시 안 됨) | 실행 1회 | 한 실행 안의 메시지 수천 건은 서로 독립이 아니다. 메시지 단위로 검정하면 표본이 부풀어 p값이 과도하게 작아진다(유사반복) |
| 실행 순서 | 회차 → 주기 → Reliability 고정 순서 | 블록 안 무작위화 (난괴법) | 고정 순서면 시간에 따른 변화(발열, 백그라운드 작업)가 특정 조건에 몰려 QoS 효과와 구분되지 않는다 |
| 반복 | 3회 | 10회 | 아래 검정력 표 |
| 분석 | 평균 막대 그래프 | 이원분산분석 + 대응 비모수 검정 + 효과크기·신뢰구간 | 차이가 우연인지 판단하고, 크기를 함께 보고 |

**검정력** (α=0.05, 블록 포함 모형, 주효과 검출 확률, `stats_results.power_note`로 계산)

| 셀당 반복 | 중간 효과 f=0.25 | f=0.4 | 큰 효과 f=0.5 |
|---:|---:|---:|---:|
| 3 | 11% | 22% | 31% |
| 5 | 18% | 38% | 54% |
| 10 | 33% | 68% | 86% |

10회면 큰 효과는 86%로 검출한다. 작은 효과까지 검출하려면 반복을 더 늘려야 하며, 유의하지 않은 결과는 "차이 없음"이 아니라 "이 검정력으로는 검출되지 않음"으로 기록한다. 3회에서는 대응 Wilcoxon 검정의 최소 p가 0.25라 원리상 유의할 수 없다.

**가설과 지표** (측정 전에 고정)

- 주 지표: `loss_rate`, `latency_mean_ms`. 탐색 지표: `latency_p95_ms`.
- H0: Reliability에 따른 지표 차이가 없다. H1: 있다 (양측). α=0.05.

**분석** (`scripts/stats_results.py`, 결과 `results/csv/stats.csv`)

1. 지표별 `y ~ 블록 + Reliability + 주기 + Reliability×주기` 이원분산분석 (Type III, 효과 코딩). 실패한 실행이 있어 셀 크기가 달라도 계산된다.
2. 가정 확인: 잔차 Shapiro-Wilk(정규성), Brown-Forsythe(등분산). 기각되면 3번 결과를 우선 해석한다.
3. 주기별 단순효과: 같은 회차의 RELIABLE·BEST_EFFORT 실행을 짝지은 Wilcoxon 부호순위 검정, 지표 안에서 Holm 보정. 효과크기 dz와 차이 평균의 95% 부트스트랩 CI를 함께 보고한다.
4. 모든 실행 값이 같으면(예: 손실 0%) 검정하지 않고 "차이 없음"으로 기록한다.

블록 항이 유의하면 회차에 따라 측정값이 변했다는 뜻이다. 무작위화와 블록 항이 이 변화를 QoS 효과에서 분리한다.

## 측정 방법

- 송신 수: `rate_hz × duration_sec`. `benchmark_pub`은 정확히 이 수만큼 발행한다.
- 수신 수: raw CSV의 고유 `seq` 개수. 중복은 `duplicate_count`로 따로 센다.
- 누락: 송신 수 - 수신 수. 수신 `seq` 최대값이 아니라 송신 수와 비교하므로 끝부분 유실도 포함된다.
- 지연: `recv_time_ns - send_time_ns`. 두 노드가 같은 컴퓨터의 `time.time_ns()`를 쓰므로 시계 동기화 오차가 없다.
- 연결 직후와 종료 직전의 유실을 QoS 차이로 오인하지 않도록, pub은 매칭 후 2초 기다린 뒤 발행하고 발행 후 2초 뒤 종료한다.

## 실행 절차

```bash
colcon build --symlink-install --packages-select sensor_monitor
bash scripts/run_experiment.sh          # 조건별 10회, 끝나면 stats.csv까지 생성
python3 scripts/plot_results.py
python3 scripts/make_dashboard.py       # results/dashboard.html
```

순서를 재현하려면 `SEED=1234 bash scripts/run_experiment.sh`처럼 실행한다. 대시보드는 단위 테스트 결과(`results/junit.xml` 또는 `colcon test` 후 `build/*/pytest.xml`)와 센서 회귀 결과(`results/csv/sensor_regression.md`)가 있으면 함께 보여 준다. 단위 테스트 결과는 `python3 -m pytest tests --junitxml=results/junit.xml`로 만든다.

결과는 `results/csv/raw_*.csv`, `results/csv/summary.csv`, `results/csv/stats.csv`, `results/csv/run_order.csv`, `results/figures/*.png`, `results/dashboard.html`에 저장된다. 재현성은 `bash scripts/run_experiment.sh 10 results/csv/rerun`으로 다른 폴더에 다시 측정해 비교한다.

## 결과

측정 전.

## 한계

- 로컬 loopback에서는 패킷 손실이 거의 없어 조건 간 차이가 작을 수 있다. 그 경우 결과를 그대로 기록하고, 손실을 임의로 만들지 않는다.
- 지연에는 DDS 전달 외에 Python 노드의 스케줄링 시간이 포함된다.
