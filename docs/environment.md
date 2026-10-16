# 실행 환경 기록 (Environment)

> 1일차 — A: ROS 2 / Gazebo 버전 기록

## 합의된 기준 버전

- ROS 2 배포판: **Jazzy Jalisco**
- Gazebo: **Gazebo Harmonic**
- 로봇 모델: TurtleBot3 Burger
- 시뮬레이션 맵: TurtleBot3 기본 월드 (`turtlebot3_gazebo`) — 추후 자체 제작 맵으로 전환 예정
- RMW(DDS) 구현체: 팀원별 기본값 확인 필요 (아래 명령으로 기록, A는 `rmw_fastrtps_cpp`)

## 버전 확인 명령

```bash
# ROS 2 배포판 확인
echo $ROS_DISTRO
ros2 doctor --report | grep -i distribution

# RMW(DDS) 구현체 확인
echo $RMW_IMPLEMENTATION
ros2 doctor --report | grep -i rmw

# Gazebo Harmonic 버전 확인
gz sim --version

# 시뮬레이션 월드 실행 확인 (TurtleBot3 기본 월드)
export TURTLEBOT3_MODEL=burger
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

## 팀원별 환경 기록

| 팀원 | OS | ROS 2 배포판 | Gazebo 버전 | RMW/DDS | 비고 |
|---|---|---|---|---|---|
| A (나) | Ubuntu 24.04 | Jazzy | Harmonic (Sim 8.15.0) | rmw_fastrtps_cpp (기본값) | |
| B (태호님) | | | | | |
| C (제경님) | Ubuntu 24.04.5 | Jazzy | Harmonic (Sim 8.15.0) | rmw_fastrtps_cpp | |

> 각자 위 명령 결과를 표에 채운 뒤 PR로 공유한다. 배포판/Gazebo 버전이 다른 팀원이 있으면 1일차 내에 맞춘다.

## 참고

- TurtleBot3 시뮬레이션: <https://emanual.robotis.com/docs/en/platform/turtlebot3/simulation/>
- 실행 패키지/launch 파일 이름은 각자의 환경에서 확인한 값을 기준으로 하며, 다르면 이 문서에 기록하고 팀에 공유한다.

## 맵 변경 기록

- 당초 Robotnik 실험실 월드(`robotnik_gazebo_worlds`)를 사용하기로 했으나, `robotnik_lab_world`가 ROS 1(catkin, `gazebo_ros` Classic) 기반이라 Jazzy + Gazebo Harmonic에서 빌드되지 않는다. (`jazzy-devel` 브랜치에서 변환된 월드는 `electrical_substation_world`뿐)
- 팀 논의 결과, 현재는 TurtleBot3 기본 월드를 사용하고 이후 자체 제작 맵으로 전환한다.
