"""raw_<reliability>_<rate>hz_<run>.csv 1개를 집계해 summary.csv에 1행 append."""
import argparse
import csv
from datetime import datetime
import os
import re
import statistics

# summary.csv 열 순서
FIELDS = [
    'run_id', 'timestamp_start', 'reliability', 'pub_rate_hz', 'repetition',
    'duration_sec', 'sent_count', 'received_count', 'loss_count', 'loss_rate',
    'latency_mean_ms', 'latency_p95_ms', 'latency_max_ms', 'env_note',
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raw_csv')
    p.add_argument('--duration', type=float, default=30.0, help='benchmark_pub의 duration_sec')
    p.add_argument('--env-note', default='')
    p.add_argument('--summary', default='results/csv/summary.csv')
    a = p.parse_args()

    # 파일명에서 실험 조건을 읽는다: raw_reliable_10hz_1.csv → reliable, 10, 1
    run_id = os.path.basename(a.raw_csv)[len('raw_'):-len('.csv')]
    m = re.fullmatch(r'(reliable|best_effort)_(\d+)hz_(\d+)', run_id)
    if not m:
        raise SystemExit(f'파일명 형식이 다름: {a.raw_csv}')
    reliability, rate, rep = m.group(1).upper(), int(m.group(2)), int(m.group(3))

    with open(a.raw_csv) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit('수신 기록이 없음')

    # 중복 수신은 한 번만 센다
    received = len({r['seq'] for r in rows})
    # pub이 정확히 rate * duration 건을 보내므로 송신 수는 계산으로 구한다
    sent = int(rate * a.duration)
    lat = sorted(float(r['latency_ms']) for r in rows)
    # 실행 시작 시각 = 수신된 메시지 중 가장 이른 송신 시각
    start_ns = min(int(r['send_time_ns']) for r in rows)

    row = {
        'run_id': run_id,
        'timestamp_start': datetime.fromtimestamp(start_ns / 1e9).isoformat(timespec='seconds'),
        'reliability': reliability,
        'pub_rate_hz': rate,
        'repetition': rep,
        'duration_sec': a.duration,
        'sent_count': sent,
        'received_count': received,
        'loss_count': sent - received,
        'loss_rate': round((sent - received) / sent, 4),
        'latency_mean_ms': round(statistics.mean(lat), 3),
        # 정렬된 목록에서 95% 위치의 값 (보간 없음)
        'latency_p95_ms': round(lat[int(0.95 * (len(lat) - 1))], 3),
        'latency_max_ms': round(lat[-1], 3),
        'env_note': a.env_note,
    }

    # 처음 만들 때만 헤더를 쓰고, 이후에는 행만 누적
    new = not os.path.exists(a.summary)
    with open(a.summary, 'a', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    print(row)


if __name__ == '__main__':
    main()
