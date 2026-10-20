# 2026-10-20 — turtlebot3_burger.world 경로 수정과 spawn_robot:=false 시 bridge 누락 수정 (A)

- 브랜치 / 이슈: `7-ryubengock` / [#7](https://github.com/devrereg/ros2_smart_navigator/issues/7)
- 커밋 전 변경사항이다.

## 변경사항

- `worlds/turtlebot3_burger.world`: 로봇 경로 `file:///home/taeho-kim/.../models/turtlebot3_burger`를 `model://turtlebot3_burger`로 변경. 다른 PC에서도 로드되도록 `empty_burger.world`와 같은 방식으로 맞췄다. 이제 로봇은 저장소 `models/`가 아니라 `turtlebot3_gazebo` 패키지의 모델을 쓴다.
- `obstacle_avoider/launch/avoid.launch.py`: `spawn_robot:=false`일 때 `ros_gz_bridge`의 `parameter_bridge`를 `turtlebot3_burger_bridge.yaml` 설정으로 따로 실행한다.
- `docs/interfaces.md`: 위 동작에 맞게 실행 순서와 `spawn_robot` 인자 설명 수정.

## 결정 사항

- **`spawn_robot:=false`여도 bridge는 실행한다.** bridge가 `spawn_turtlebot3.launch.py` 안에 들어 있어서, 스폰을 건너뛰면 `/scan`, `/cmd_vel` 연결도 함께 빠지는 버그가 있었다.
- **`turtlebot3_burger.world`에 센서 플러그인은 추가하지 않았다.** 이 world로는 실행하지 않고 `warehouse`를 쓰기로 했기 때문이다.

## 미해결

- `worlds/turtlebot3_burger.world`에는 `gz-sim-sensors-system` 플러그인이 없어 `/scan` 데이터가 나오지 않는다. 이 world로 실행하면 `detector_node`가 아무것도 받지 못하고 `avoider`가 안전 정지 상태(`front_min=None`)에 머문다. 쓰려면 `empty_burger.world`처럼 `<plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors">` 한 줄을 추가해야 한다.
