"""raw_<reliability>_<rate>hz_<run>.csv를 집계해 summary.csv에 run_id별 1행으로 기록."""
import argparse
import csv
from datetime import datetime
import os
import re
import statistics

# summary.csv 열 순서
FIELDS = [
    'run_id', 'timestamp_start', 'reliability', 'pub_rate_hz', 'repetition',
    'duration_sec', 'sent_count', 'received_count', 'receive_rate', 'loss_count', 'loss_rate',
    'duplicate_count', 'out_of_order_count',
    'latency_mean_ms', 'latency_p95_ms', 'latency_max_ms', 'env_note',
]


def analyze(raw_csv, duration, env_note=''):
    """raw CSV 1개를 summary 1행과 누락 seq 목록으로 집계한다."""
    # 파일명에서 실험 조건을 읽는다: raw_reliable_10hz_1.csv → reliable, 10, 1
    run_id = os.path.basename(raw_csv)[len('raw_'):-len('.csv')]
    m = re.fullmatch(r'(reliable|best_effort)_(\d+)hz_(\d+)', run_id)
    if not m:
        raise SystemExit(f'파일명 형식이 다름: {raw_csv}')
    reliability, rate, rep = m.group(1).upper(), int(m.group(2)), int(m.group(3))

    with open(raw_csv) as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f'수신 기록이 없음: {raw_csv}')

    # pub이 정확히 rate * duration 건을 보내므로 송신 수는 계산으로 구한다
    sent = int(rate * duration)
    seqs = [int(r['seq']) for r in rows]
    if max(seqs) >= sent:
        raise SystemExit(f'seq {max(seqs)}가 송신 수 {sent}를 넘음. --duration을 확인: {raw_csv}')
    # 중복 수신은 한 번만 센다. 끝부분 유실도 잡히도록 수신 seq 최대값이 아니라 sent와 비교한다
    received = len(set(seqs))
    missing = sorted(set(range(sent)) - set(seqs))
    # 그때까지의 최대 seq보다 작은 seq가 처음 오면 순서가 뒤바뀐 수신이다
    seen, top, out_of_order = set(), -1, 0
    for seq in seqs:
        if seq not in seen and seq < top:
            out_of_order += 1
        seen.add(seq)
        top = max(top, seq)

    lat = sorted(float(r['latency_ms']) for r in rows)
    # 실행 시작 시각 = 수신된 메시지 중 가장 이른 송신 시각
    start_ns = min(int(r['send_time_ns']) for r in rows)

    row = {
        'run_id': run_id,
        'timestamp_start': datetime.fromtimestamp(start_ns / 1e9).isoformat(timespec='seconds'),
        'reliability': reliability,
        'pub_rate_hz': rate,
        'repetition': rep,
        'duration_sec': duration,
        'sent_count': sent,
        'received_count': received,
        'receive_rate': round(received / sent, 4),
        'loss_count': sent - received,
        'loss_rate': round((sent - received) / sent, 4),
        'duplicate_count': len(seqs) - received,
        'out_of_order_count': out_of_order,
        'latency_mean_ms': round(statistics.mean(lat), 3),
        # 정렬된 목록에서 95% 위치의 값 (보간 없음)
        'latency_p95_ms': round(lat[int(0.95 * (len(lat) - 1))], 3),
        'latency_max_ms': round(lat[-1], 3),
        'env_note': env_note,
    }
    return row, missing


def write_summary(path, new_rows):
    """같은 run_id는 새 값으로 바꾸고 나머지 행은 유지한다."""
    rows = {}
    if os.path.exists(path):
        with open(path, newline='') as f:
            rows = {r['run_id']: r for r in csv.DictReader(f)}
    rows.update({r['run_id']: r for r in new_rows})
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows.values())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('raw_csv', nargs='+')
    p.add_argument('--duration', type=float, default=30.0, help='benchmark_pub의 duration_sec')
    p.add_argument('--env-note', default='')
    p.add_argument('--summary', default='results/csv/summary.csv')
    a = p.parse_args()

    new_rows = []
    for path in a.raw_csv:
        row, missing = analyze(path, a.duration, a.env_note)
        new_rows.append(row)
        print(row)
        if missing:
            print(f'  누락 seq {len(missing)}건, 앞부분: {missing[:20]}')
    write_summary(a.summary, new_rows)


if __name__ == '__main__':
    main()
