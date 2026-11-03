# 6일차 C 통합 테스트 증거 (2026-11-03)

`docs/test_plan.md`의 **2026-11-03 — 6일차 C 통합 테스트**에서 사용한 요약만 보관한다.
전체 launch 로그·scan summary·rosbag은 용량과 리뷰 편의를 위해 저장소에 커밋하지 않고
실행 환경의 `~/day6_integration_evidence/`에 보관했다.

## 구성

| 파일 | 내용 |
|---|---|
| `2026-11-03-day6-metrics.csv` | 6일차 9회의 시작 위치, 감시 시간, 상태 전환, 정지 전 `front_min`, 전체 방향 최소 거리·각도, 판정 |
| `2026-11-03-day6-precision-metrics.csv` | 추가 정밀 2회의 `/scan`·`/odom` 기록 주기, 회피 사이클, 최소 거리 시점의 odom 자세, 0.15 m 이하 프레임 수 |
| `README.md` | 이 문서. 실행 조건과 원본 보관 위치 |

## 실행 조건

- ROS 2 Jazzy, Gazebo Harmonic 8.15.0, TurtleBot3 Burger, `warehouse`
- LDS-01: `range_min=0.12 m`, `range_max=3.50 m`, `angle_min=0.0 rad`, `angle_max≈6.28 rad`, 360개
- `ROS_DOMAIN_ID=42`, 회차별 `GZ_PARTITION` 분리
- 감시 토픽: `/scan`, `/odom`, `/cmd_vel`, `/obstacle/front_distance`
- 접촉 의심 기준: 감시 구간 중 `/scan` 전체 방향 최소 거리 `≤ 0.15 m` (5일차와 동일)
- 추가 정밀 2회는 `/scan` 약 5.01 Hz, `/odom` 약 47.7 Hz로 기록했다.
- Gazebo GUI가 OpenGL 컨텍스트를 만들지 못해, 추가 정밀 2회는 GUI만 제외한 headless 서버로 실행했다. 제품 launch/노드 코드는 수정하지 않았다.

## 원본 보관

```text
~/day6_integration_evidence/
├── run_9_-15/
├── run2_9_-15/
├── run3_9_-15/
├── run4_9_-15_70/
├── run5_9_-15_70/          # 추가 정밀 70초
├── run_8_0/
├── run_4_3/
├── run2_4_3_70/            # 추가 정밀 70초
├── run_1_-13c/
├── run_1_-13/
├── run_1_-13b/
├── run5_9_-15_70_gui_fail/
└── headless_avoid.launch.py
```

각 실행 디렉토리에는 `bag/`(MCAP + metadata), `launch.log`, `bag_record.log`,
`bag_info.txt`, `analysis.txt`, `metrics.json`, `minute_metrics.json`,
`scan_summary.csv`가 있다.
