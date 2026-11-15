#!/usr/bin/env bash
# 회피 성공률 시험: 시작 위치별 자동 주행 -> avoid_trials.csv -> 성공률과 95% 신뢰구간
# 사용: bash scripts/run_avoid_trials.sh [위치별 반복=3] [결과폴더=results/csv/avoid]  (SEED=정수로 순서 재현)
cd "$(dirname "$0")/.." || exit 1
[ -f install/setup.bash ] && source install/setup.bash
command -v ros2 > /dev/null || { echo 'ros2를 찾을 수 없습니다. ROS 2 환경을 source 하세요.'; exit 1; }
set -m  # 백그라운드 launch가 SIGINT를 무시하지 않도록 작업 제어를 켠다

REPS=${1:-3}  # 10곳 x 3회 = 30회. 29/30 이상이어야 95% CI 하한이 목표 80%를 넘는다 (docs/avoidance.md)
OUT=${2:-results/csv/avoid}
DURATION=70.0  # 5일차와 같은 회차당 감시 시간
SEED=${SEED:-$RANDOM}
# 5일차 판정 대상 10곳. (5.0,-6.0), (-8.0,-8.0)은 스폰 직후 끼여 쓰지 않는다
POSITIONS='8.0,0.0 0.0,-8.0 -6.0,8.0 4.0,3.0 11.0,-2.0 -3.0,-2.0 7.0,4.5 9.0,-15.0 1.0,-13.0 -6.0,-13.0'
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-79}

mkdir -p "$OUT"
# 위치 x 반복을 섞어 실행 순서(시간)에 따른 영향이 특정 위치에 몰리지 않게 한다
trials=$(python3 -c 'import random, sys; c = sys.argv[3:]; c = [f"{p}@{r}" for r in range(1, int(sys.argv[2]) + 1) for p in c]; random.Random(sys.argv[1]).shuffle(c); print(*c)' \
  "$SEED" "$REPS" $POSITIONS)

for trial in $trials; do
  pos=${trial%@*}
  rep=${trial#*@}
  x=${pos%,*}
  y=${pos#*,}
  label="x${x}_y${y}_${rep}"
  echo "=== $label ==="
  ros2 launch obstacle_avoider avoid.launch.py world:=warehouse x_pose:="$x" y_pose:="$y" \
    > "$OUT/launch_$label.log" 2>&1 &
  launch=$!
  # 감시는 /scan과 /odom이 들어온 뒤부터 DURATION초. Gazebo 기동 대기 60초 여유
  timeout -s INT $((${DURATION%.*} + 60)) ros2 run sensor_monitor avoid_trial --ros-args \
    -p label:="$label" -p x_pose:="$x" -p y_pose:="$y" -p duration_sec:=$DURATION -p out_dir:="$OUT"
  kill -INT $launch 2> /dev/null
  for _ in $(seq 30); do kill -0 $launch 2> /dev/null || break; sleep 1; done
  kill -9 $launch 2> /dev/null
  pkill -9 -f 'gz sim' 2> /dev/null  # 다음 회차가 이전 시뮬레이션과 섞이지 않게 정리
  sleep 2
done

python3 scripts/summarize_trials.py "$OUT/avoid_trials.csv" | tee "$OUT/avoid_trials.md"
echo "완료: $OUT (SEED=$SEED). avoider 상태 전환은 launch_*.log, 시점별 거리는 avoid_trace_*.csv"
