#!/usr/bin/env bash
# QoS 비교 실험: 조건별 반복 실행 -> raw CSV -> summary.csv -> stats.csv
# 사용: bash scripts/run_experiment.sh [반복수=10] [결과폴더=results/csv]  (SEED=정수로 순서 재현)
cd "$(dirname "$0")/.." || exit 1
[ -f install/setup.bash ] && source install/setup.bash
command -v ros2 > /dev/null || { echo 'ros2를 찾을 수 없습니다. ROS 2 환경을 source 하세요.'; exit 1; }

REPS=${1:-10}  # 조건별 10회: 근거는 docs/qos_experiment.md '실험 설계'
OUT=${2:-results/csv}
DURATION=30.0
PAYLOAD=64
RATES='10 50'
SEED=${SEED:-$RANDOM}
export ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-78}  # 다른 ROS 노드와 섞이지 않게 분리

pgrep -f 'gz sim' > /dev/null && echo '경고: Gazebo가 실행 중입니다. 조건을 통제하려면 끄고 실행하세요.'
mkdir -p "$OUT"
echo 'order,repetition,reliability,rate_hz,start_time,seed' > "$OUT/run_order.csv"
order=0

failed=0
for run in $(seq 1 "$REPS"); do
  # 회차(블록)마다 4조건의 실행 순서를 무작위로 섞는다. 시간에 따른 변화(발열, 백그라운드 작업)가
  # 한 조건에 몰려 QoS 차이로 보이는 것을 막는다
  conds=$(python3 -c 'import random, sys; c = sys.argv[2:]; random.Random(sys.argv[1]).shuffle(c); print(*c)' \
    "$SEED-$run" $(for rate in $RATES; do echo "reliable:$rate best_effort:$rate"; done))
  for cond in $conds; do
    rel=${cond%:*}
    rate=${cond#*:}
    order=$((order + 1))
    echo "$order,$run,$rel,$rate,$(date -Iseconds),$SEED" >> "$OUT/run_order.csv"
    echo "=== $rel ${rate}Hz run $run ==="
    # sub가 끝나지 못할 때를 대비한 상한: 매칭 대기 30초 + 실험 시간 + 여유
    timeout -k 2 $((${DURATION%.*} + 45)) ros2 run sensor_monitor benchmark_sub --ros-args \
      -p reliability:=$rel -p rate_hz:=$rate -p run:=$run -p out_dir:="$OUT" \
      -p idle_timeout_sec:=3.0 &
    sub=$!
    ros2 run sensor_monitor benchmark_pub --ros-args \
      -p reliability:=$rel -p rate_hz:=$rate -p duration_sec:=$DURATION \
      -p payload_bytes:=$PAYLOAD
    pub_status=$?
    wait $sub
    if [ $pub_status -ne 0 ]; then
      echo "실패: $rel ${rate}Hz run $run"
      rm -f "$OUT/raw_${rel}_${rate}hz_${run}.csv"
      failed=$((failed + 1))
    fi
  done
done

NOTE="$(uname -sr), ${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp(default)}, domain $ROS_DOMAIN_ID, ${PAYLOAD}B"
python3 scripts/analyze_results.py "$OUT"/raw_*.csv --duration "$DURATION" \
  --env-note "$NOTE" --summary "$OUT/summary.csv" || exit 1
python3 scripts/stats_results.py --summary "$OUT/summary.csv" --out "$OUT/stats.csv"
echo "완료: $OUT/summary.csv, $OUT/stats.csv (실패 $failed회, SEED=$SEED)"
[ "$failed" -eq 0 ]
