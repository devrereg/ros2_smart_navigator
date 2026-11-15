#!/usr/bin/env bash
# 전체 실행·종료·재실행 테스트: launch -> 거리 토픽 수신 확인 -> Ctrl+C -> 남은 프로세스 확인을 반복
# 사용: bash scripts/run_restart_test.sh [반복=5] | tee results/csv/restart_test.md
cd "$(dirname "$0")/.." || exit 1
[ -f install/setup.bash ] && source install/setup.bash
command -v ros2 > /dev/null || { echo 'ros2를 찾을 수 없습니다. ROS 2 환경을 source 하세요.'; exit 1; }
set -m  # 백그라운드 launch가 SIGINT를 무시하지 않도록 작업 제어를 켠다

CYCLES=${1:-5}
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-80}
PROCS='gz sim|detector_node|lib/obstacle_avoider/avoider|parameter_bridge|robot_state_publisher'
passed=0

echo '| 회차 | 기동 시간 (초) | 정상 종료 | 남은 프로세스 | 결과 |'
echo '|---|---|---|---|---|'
for cycle in $(seq 1 "$CYCLES"); do
  start=$(date +%s)
  ros2 launch obstacle_avoider avoid.launch.py world:=warehouse x_pose:=8.0 y_pose:=0.0 \
    > "/tmp/restart_$cycle.log" 2>&1 &
  launch=$!
  # 시뮬레이션 -> 감지 노드까지 데이터가 흐르면 기동 완료로 본다
  if timeout 90 ros2 topic echo --once /obstacle/front_distance > /dev/null 2>&1; then
    up=$(( $(date +%s) - start ))
  else
    up='시간 초과'
  fi
  kill -INT $launch 2> /dev/null
  clean='예'
  for _ in $(seq 30); do kill -0 $launch 2> /dev/null || break; sleep 1; done
  if kill -0 $launch 2> /dev/null; then
    clean='아니오 (30초 내 미종료)'
    kill -9 $launch
  fi
  sleep 2
  left=$(pgrep -fa "$PROCS" | grep -v pgrep | awk '{print $2}' | sort -u | tr '\n' ' ')
  if [ "$up" != '시간 초과' ] && [ "$clean" = '예' ] && [ -z "$left" ]; then
    result='통과'
    passed=$((passed + 1))
  else
    result='실패'
  fi
  echo "| $cycle | $up | $clean | ${left:-없음} | $result |"
  pkill -9 -f "$PROCS" 2> /dev/null  # 다음 회차를 깨끗한 상태에서 시작
  sleep 2
done
echo
echo "$passed/$CYCLES 통과"
[ "$passed" -eq "$CYCLES" ]
