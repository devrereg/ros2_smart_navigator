# 테스트 시나리오

> 1일차 완료 기준: 테스트 시나리오 초안. 세부 항목은 각 담당자가 작업 진행에 따라 추가한다.

## 통합 테스트 시나리오 (초안)

1. 시뮬레이션 실행: `ros2 launch robotnik_lab_world robotnik_lab_world.launch.py`
2. 토픽 확인: `ros2 topic list`, `ros2 topic info /scan`, `ros2 topic info /cmd_vel`
3. 장애물 감지 테스트 (3일차 이후, B 작성)
4. 장애물 회피 테스트 (4~5일차 이후, C 작성)
5. 통합 실행 테스트 (6일차 이후, A 작성)
6. QoS 비교 실험 테스트 (8~10일차, A·B·C 공동 작성)

## 완료 기준(초안)

- 사전 정의한 10회 테스트 중 8회 이상 안전 회피 또는 정지 (`plans.md` 8장 참고)
