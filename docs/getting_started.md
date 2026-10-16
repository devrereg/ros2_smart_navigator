# 시작 가이드 (Getting Started)

> 새 팀원이 저장소를 clone 받아 시뮬레이션을 실행하고 첫 작업을 시작하기까지의 절차입니다. 위에서부터 순서대로 따라 하세요.

## 0. 준비물

| 항목 | 기준 |
|---|---|
| OS | Ubuntu 24.04 (Noble) |
| ROS 2 | Jazzy Jalisco |
| Gazebo | Gazebo Harmonic (`gz sim` 8.x) |
| 로봇 | TurtleBot3 Burger |
| 기타 | Git, GitHub 계정 (저장소 접근 권한 필요) |

기준 버전이 다르면 패키지 이름과 토픽 타입이 달라질 수 있습니다. 반드시 위 버전으로 맞추세요. 자세한 배경은 [`environment.md`](environment.md) 참고.

---

## 1. ROS 2 Jazzy 및 필요한 패키지 설치

ROS 2 Jazzy가 아직 없다면 [공식 설치 문서](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html)를 따라 `ros-jazzy-desktop`까지 설치합니다. 그다음 시뮬레이션에 필요한 패키지를 설치합니다.

```bash
sudo apt update
sudo apt install ros-jazzy-desktop ros-jazzy-ros-gz ros-jazzy-turtlebot3 ros-jazzy-turtlebot3-simulations ros-jazzy-turtlebot3-teleop python3-colcon-common-extensions git
```

---

## 2. 환경 설정 (`~/.bashrc`)

터미널을 열 때마다 `source`와 `export`를 반복하지 않도록 `~/.bashrc`에 한 번만 등록해 둡니다. 이렇게 해 두면 **이후에는 `ros2 launch ...`만 실행해도 됩니다.**

### 2-1. 이미 등록되어 있는지 확인

```bash
grep -nE "ros/jazzy|TURTLEBOT3_MODEL" ~/.bashrc
```

아래 두 줄이 이미 나오면 2-2는 건너뛰고 2-3으로 갑니다. 같은 줄이 두 번 나오면 하나만 남기고 지웁니다.

```text
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=burger
```

### 2-2. `~/.bashrc`에 추가

없는 줄만 아래 명령으로 맨 아래에 추가합니다.

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```
```bash
echo 'export TURTLEBOT3_MODEL=burger' >> ~/.bashrc
```

> 직접 편집하려면 `nano ~/.bashrc`로 열어 맨 아래에 두 줄을 붙여 넣고, `Ctrl+O` → `Enter`로 저장한 뒤 `Ctrl+X`로 나옵니다.

### 2-3. 변경 내용 반영

`~/.bashrc`는 터미널이 **새로 열릴 때** 읽힙니다. 이미 열려 있는 터미널에는 아래 명령으로 바로 반영합니다. (새 터미널을 열어도 됩니다.)

```bash
source ~/.bashrc
```

### 2-4. 반영 확인

```bash
echo $ROS_DISTRO $TURTLEBOT3_MODEL
```

`jazzy burger`가 나오면 됩니다.

### 2-5. 오류가 나는 경우

터미널을 열 때 `No such file or directory` 오류가 나면 `~/.bashrc`에 **없는 경로를 `source`하는 줄**이 있다는 뜻입니다. 오류에 나온 경로를 확인하고 해당 줄을 지우거나 올바른 경로로 고칩니다. 동작에는 영향이 없지만 정리해 두는 것이 좋습니다.

- 예: 존재하지 않는 `source ~/turtlebot3_ws/install/setup.bash` → 줄 삭제
- 예: `colcon-argcomplete/bash` → 올바른 경로는 `/usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash`

---

## 3. 버전 확인

모두 기준 버전과 일치하는지 확인합니다.

```bash
echo $ROS_DISTRO
```
`jazzy`가 나와야 합니다.

```bash
gz sim --version
```
`Gazebo Sim, version 8.x`가 나와야 합니다.

```bash
ros2 doctor --report | grep -i "middleware name"
```
기본값은 `rmw_fastrtps_cpp`입니다.

> `ros2 --version`은 Jazzy에서 지원하지 않는 옵션이라 오류가 납니다. 위 명령을 사용하세요.

확인한 값은 [`environment.md`](environment.md)의 "팀원별 환경 기록" 표에 본인 행을 채워 PR로 공유합니다.

---

## 4. 저장소 clone

```bash
cd ~
git clone https://github.com/devrereg/ros2_smart_navigator.git
cd ros2_smart_navigator
```

GitHub 로그인이 필요하면 `gh auth login`을 사용하거나 개인 액세스 토큰(HTTPS) / SSH 키를 설정합니다.

저장소 구조는 [`README.md`](../README.md)에 정리되어 있습니다.

---

## 5. 시뮬레이션 실행

2번에서 `~/.bashrc` 설정을 마쳤다면 **`ros2 launch` 명령만 실행하면 됩니다.** 터미널마다 `source /opt/ros/jazzy/setup.bash`나 `export TURTLEBOT3_MODEL=burger`를 다시 입력할 필요가 없습니다.

```bash
ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py
```

정상이라면 다음과 같이 됩니다.

- Gazebo 창이 열리고 육각형 맵에 TurtleBot3 Burger가 나타납니다. (처음에는 로딩에 시간이 걸립니다.)
- 터미널에 `Entity creation successful`과 `Creating GZ->ROS Bridge: ...` 로그가 나옵니다.
- `QML ... Binding loop detected`, `gz_frame_id ... not defined in SDF` 경고는 동작에 영향이 없으므로 무시해도 됩니다.

> `Package ... not found`나 로봇이 생성되지 않는 문제가 생기면 2-4의 반영 확인부터 다시 해 보세요. `~/.bashrc` 설정이 없는 환경(예: SSH로 접속한 새 셸)에서는 `source /opt/ros/jazzy/setup.bash`와 `export TURTLEBOT3_MODEL=burger`를 먼저 실행해야 합니다.

> 현재는 TurtleBot3 기본 월드를 사용합니다. 추후 팀 자체 제작 맵으로 바뀌면 이 절을 갱신합니다. (`plans.md`의 "선택한 맵" 참고)

---

## 6. 동작 확인

**새 터미널**을 열고 아래를 확인합니다. (2번 설정이 되어 있으면 환경은 자동으로 불러와지므로 바로 `ros2` 명령을 쓰면 됩니다.)

### 6-1. 토픽 확인

```bash
ros2 topic list
```
`/scan`, `/cmd_vel`, `/odom` 등이 보여야 합니다.

```bash
ros2 topic info /scan --verbose
```
```bash
ros2 topic info /cmd_vel --verbose
```

### 6-2. 키보드로 로봇 움직여 보기

```bash
ros2 run turtlebot3_teleop teleop_keyboard
```

| 키 | 동작 |
|---|---|
| `w` / `x` | 전진 / 후진 |
| `a` / `d` | 좌회전 / 우회전 |
| `s` | 정지 |

Gazebo 안의 Burger가 움직이면 정상입니다. 실행을 끝낼 때는 각 터미널에서 `Ctrl+C`를 누릅니다.

---

## 7. 이 프로젝트에서 꼭 알아야 할 인터페이스

전체 내용은 [`interfaces.md`](interfaces.md)를 참고하세요. 핵심만 정리하면:

| 토픽 | 메시지 타입 | QoS |
|---|---|---|
| `/scan` | `sensor_msgs/msg/LaserScan` | Reliable, Volatile |
| `/cmd_vel` | `geometry_msgs/msg/TwistStamped` | Reliable, Volatile |

> **주의:** `/cmd_vel`은 `Twist`가 아니라 **`TwistStamped`**입니다. `Twist`로 발행하면 로봇이 움직이지 않습니다. 속도 값은 `msg.twist.linear.x`, `msg.twist.angular.z`에 넣습니다.

---

## 8. 작업 시작하기

1. 자신의 역할을 [`plans.md`](plans.md)에서 확인합니다.
2. 브랜치 규칙, 커밋 메시지 규칙, PR 절차는 [`branching.md`](branching.md)를 따릅니다.
3. 작업을 시작하기 전에 GitHub 이슈를 만들고, 이슈 번호로 작업 브랜치를 만듭니다. 브랜치명은 `{이슈번호}-{닉네임}` 형식입니다. (예: 이슈 #12, 닉네임 `ryubengock` → `12-ryubengock`)

```bash
git checkout main
git pull origin main
git checkout -b <이슈번호>-<닉네임>
```

4. 작업이 끝나면 푸시하고 `main`으로 PR을 생성합니다. (`integration` 브랜치는 현재 사용하지 않습니다.)

5. ROS 2 패키지(`src/` 아래)를 추가·수정한 뒤에는 워크스페이스 루트에서 빌드하고 환경을 불러옵니다. (패키지가 아직 없으면 건너뜁니다.)

```bash
colcon build --symlink-install
source install/setup.bash
```

`build/`, `install/`, `log/`는 `.gitignore`에 들어 있어 커밋되지 않습니다.

---

## 9. 문제 해결

| 증상 | 확인할 것 |
|---|---|
| `Package 'turtlebot3_gazebo' not found` | 1번의 `apt install` 실행 여부, `source /opt/ros/jazzy/setup.bash` 적용 여부 |
| Gazebo 창이 안 뜨거나 화면이 깨짐 | 그래픽 드라이버 확인, 터미널 로그의 에러 메시지 확인 |
| 로봇이 생기지 않음 | `echo $TURTLEBOT3_MODEL`이 `burger`인지 확인 |
| `teleop_keyboard`로 움직이지 않음 | 시뮬레이션이 실행 중인지, `ros2 topic info /cmd_vel --verbose`에서 Subscriber가 있는지 확인 |
| 이전 Gazebo 프로세스가 남아 실행이 꼬임 | `pkill -f "gz sim"` 후 다시 실행 |
| 터미널을 열 때마다 `No such file or directory` 오류 | `~/.bashrc`에서 없는 경로를 `source`하는 줄 삭제 |

해결되지 않으면 실행한 명령과 전체 에러 메시지를 팀 채널에 공유하세요.
