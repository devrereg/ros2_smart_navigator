#!/usr/bin/env bash
# 새 환경에서 프로젝트 실행에 필요한 항목을 점검한다
# 사용: bash scripts/check_env.sh
cd "$(dirname "$0")/.." || exit 1  # 어디서 실행해도 저장소 루트 기준으로 동작
# 빌드가 끝난 환경이면 프로젝트 패키지도 찾을 수 있도록 불러온다
[ -f install/setup.bash ] && source install/setup.bash
failed=0

check() {  # 이름, 조건 명령
  # 명령 출력은 숨기고 성공 여부만 OK/NG로 표시한다
  if eval "$2" > /dev/null 2>&1; then
    echo "OK  $1"
  else
    echo "NG  $1"
    failed=$((failed + 1))
  fi
}

# 합의된 기준 버전 (docs/environment.md)
check 'ROS 2 Jazzy' '[ "$ROS_DISTRO" = jazzy ]'
check 'Gazebo Harmonic (Sim 8.x)' 'gz sim --version | grep -q "version 8\."'
check 'TURTLEBOT3_MODEL=burger' '[ "$TURTLEBOT3_MODEL" = burger ]'
check 'colcon' 'command -v colcon'
check 'matplotlib (그래프용)' 'python3 -c "import matplotlib"'
check 'scipy (통계 검정용)' 'python3 -c "import scipy"'
# 외부 패키지와, colcon build 후 설치되는 프로젝트 패키지
for pkg in ros_gz_sim ros_gz_bridge turtlebot3_gazebo turtlebot3_teleop \
           obstacle_detector obstacle_avoider sensor_monitor; do
  check "패키지 $pkg" "ros2 pkg prefix $pkg"
done

echo "RMW: ${RMW_IMPLEMENTATION:-기본값}, 실패 $failed건"
[ "$failed" -eq 0 ]  # 하나라도 NG이면 종료 코드 1
