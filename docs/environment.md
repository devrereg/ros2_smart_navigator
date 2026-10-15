# 실행 환경 기록 (Environment)

> 1일차 — A: ROS 2 / Gazebo 버전 기록

## 합의된 기준 버전

- ROS 2 배포판: **Jazzy Jalisco**
- Gazebo: **Gazebo Harmonic**
- 로봇 모델: TurtleBot3 Burger
- 시뮬레이션 맵: Robotnik 실험실 월드 (`robotnik_gazebo_worlds`)
- RMW(DDS) 구현체: 팀원별 기본값 확인 필요 (아래 명령으로 기록)

## 버전 확인 명령

```bash
# ROS 2 배포판 확인
echo $ROS_DISTRO
ros2 --version

# RMW(DDS) 구현체 확인
echo $RMW_IMPLEMENTATION
ros2 doctor --report | grep -i rmw

# Gazebo Harmonic 버전 확인
gz sim --version

# 실험실 월드 실행 확인
ros2 launch robotnik_lab_world robotnik_lab_world.launch.py
```

## 팀원별 환경 기록

| 팀원 | OS | ROS 2 배포판 | Gazebo 버전 | RMW/DDS | 비고 |
|---|---|---|---|---|---|
| A (나) | | Jazzy | Harmonic | | |
| B (태호님) | | | | | |
| C (제경님) | | | | | |

> 각자 위 명령 결과를 표에 채운 뒤 PR로 공유한다. 배포판/Gazebo 버전이 다른 팀원이 있으면 1일차 내에 맞춘다.

## 참고

- 맵 저장소: <https://github.com/RobotnikAutomation/robotnik_gazebo_worlds>
- 실행 패키지/launch 파일 이름은 각자의 교육 환경에서 확인한 값을 기준으로 하며, 다르면 이 문서에 기록하고 팀에 공유한다.
