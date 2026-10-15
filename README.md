# ros2_smart_navigator

ROS 2와 Gazebo 시뮬레이션 환경에서 TurtleBot3 Burger의 LiDAR 기반 장애물 회피 기능을 구현하고, DDS QoS 설정에 따른 메시지 전달 성능을 비교·분석하는 프로젝트입니다.

## 실행 환경

- ROS 2: Jazzy Jalisco
- Gazebo: Harmonic
- 로봇 모델: TurtleBot3 Burger
- 시뮬레이션 맵: Robotnik 실험실 월드 (`robotnik_gazebo_worlds`)

팀원별 환경 확인 절차와 기록은 [`docs/environment.md`](docs/environment.md) 참고.

## 저장소 구조

```text
ros2_smart_navigator/
├── docs/            # 아키텍처, 인터페이스, 테스트, QoS 실험, 회고 문서
├── src/             # ROS 2 패키지 (sensor_monitor, obstacle_avoider, experiment_monitor)
├── launch/          # launch 파일
├── config/          # 파라미터/설정 파일
├── scripts/         # 실험 실행 및 결과 분석 스크립트
├── tests/           # 테스트 코드
├── results/         # 실험 결과 (csv, figures)
└── media/           # 스크린샷, 시연 영상
```

## 브랜치 전략

작업은 기능 브랜치(`feature/<담당자>-<기능>`)에서 진행하고 `integration` 브랜치로 모은 뒤 `main`에 병합합니다. 자세한 규칙은 [`docs/branching.md`](docs/branching.md) 참고.

## 팀 구성

| 역할 | 담당 |
|---|---|
| 시스템 설계 및 통합 | A |
| LiDAR 센서 처리 및 장애물 감지 | B |
| 장애물 회피 및 주행 제어 | C |
| QoS 실험 및 포트폴리오 (공동) | A·B·C |

## 전체 계획

14일 상세 일정과 역할 분담은 [`docs/plans.md`](docs/plans.md) 참고.
