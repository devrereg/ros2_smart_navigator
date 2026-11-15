"""detection_log CSV를 Markdown으로 요약 (7일차 성공·실패 사례 정리용)."""
import argparse
from collections import Counter
import csv
from datetime import datetime

CONTACT_DIST = 0.15  # 5일차 접촉 의심 기준 (m)
PROBLEM = ('mismatch', 'no_topic', 'extra_topic')


def as_time(row):
    if not row['time_ns']:
        return '-'
    return datetime.fromtimestamp(int(row['time_ns']) / 1e9).strftime('%H:%M:%S.%f')[:-3]


def summarize(rows, limit):
    counts = Counter(r['status'] for r in rows)
    scanned = [r for r in rows if r['all_min'] != '']
    print('## 일치 여부\n')
    print('| 상태 | 건수 |\n|---|---:|')
    for status, count in counts.most_common():
        print(f'| {status} | {count} |')

    print('\n## 전방 구간 특수값 (샘플 수 합계)\n')
    print('| nan | +inf | -inf | 범위 밖 |\n|---:|---:|---:|---:|')
    totals = [sum(int(r[k]) for r in scanned)
              for k in ('nan', 'pos_inf', 'neg_inf', 'out_of_range')]
    print('| ' + ' | '.join(map(str, totals)) + ' |')

    if scanned:
        nearest = min(scanned, key=lambda r: float(r['all_min']))
        contact = sum(float(r['all_min']) <= CONTACT_DIST for r in scanned)
        print('\n## 최소 거리\n')
        print(f"- 전체 방향 최소 {nearest['all_min']} m ({as_time(nearest)}), "
              f"좌 {nearest['left_min']} / 우 {nearest['right_min']} / "
              f"후 {nearest['back_min']} / 전방 {nearest['calc']}")
        print(f'- 접촉 의심(<= {CONTACT_DIST} m) 스캔 {contact}건 / 전체 {len(scanned)}건')

    problems = [r for r in rows if r['status'] in PROBLEM]
    print(f'\n## 실패 사례 (전체 {len(problems)}건 중 앞 {limit}건)\n')
    print('| 시각 | 상태 | 토픽 값 | 스캔 계산 값 |\n|---|---|---:|---:|')
    for r in problems[:limit]:
        print(f"| {as_time(r)} | {r['status']} | {r['topic']} | {r['calc']} |")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('log_csv', nargs='?', default='results/csv/detection_log.csv')
    p.add_argument('--limit', type=int, default=20)
    a = p.parse_args()
    with open(a.log_csv, newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f'기록이 없음: {a.log_csv}')
    summarize(rows, a.limit)


if __name__ == '__main__':
    main()
