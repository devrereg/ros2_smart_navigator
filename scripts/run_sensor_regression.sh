#!/usr/bin/env bash
# detector_node 센서 이상값 회귀 테스트 (Gazebo 불필요)
# 사용: bash scripts/run_sensor_regression.sh
cd "$(dirname "$0")/.." || exit 1
[ -f install/setup.bash ] && source install/setup.bash
command -v ros2 > /dev/null || { echo 'ros2를 찾을 수 없습니다. ROS 2 환경을 source 하세요.'; exit 1; }

export ROS_DOMAIN_ID=77  # 가짜 /scan이 시뮬레이션과 섞이지 않게 분리

timeout 60 ros2 run obstacle_detector detector_node &
detector=$!
ros2 run sensor_monitor sensor_fault_test
status=$?
kill $detector 2> /dev/null
wait $detector 2> /dev/null
exit $status
