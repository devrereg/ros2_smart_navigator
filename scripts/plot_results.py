"""summary.csv로 조건별 수신율·지연시간 비교 그래프를 만든다. 필요: python3-matplotlib."""
import argparse
import csv
import os
import statistics

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

SERIES = [('RELIABLE', '#2a78d6'), ('BEST_EFFORT', '#eb6834')]
INK = '#52514e'
GRID = '#e4e3df'
BAR_WIDTH = 0.34
GAP = 0.02

CHARTS = [
    ('receive_rate', 'Receive rate (%)', 100.0, 'receive_rate.png'),
    ('latency_mean_ms', 'Mean latency (ms)', 1.0, 'latency_mean.png'),
    ('latency_p95_ms', 'p95 latency (ms)', 1.0, 'latency_p95.png'),
]


def plot(rows, field, ylabel, scale, path):
    rates = sorted({int(r['pub_rate_hz']) for r in rows})
    fig, ax = plt.subplots(figsize=(6.4, 4.0), facecolor='#fcfcfb')
    ax.set_facecolor('#fcfcfb')

    for s, (reliability, color) in enumerate(SERIES):
        means = []
        for x, rate in enumerate(rates):
            vals = [float(r[field]) * scale for r in rows
                    if r['reliability'] == reliability and int(r['pub_rate_hz']) == rate]
            if not vals:
                means.append(0.0)
                continue
            means.append(statistics.mean(vals))
            pos = x + (s - 0.5) * (BAR_WIDTH + GAP)
            # 반복 횟수가 적으므로 오차 막대 대신 회차별 값을 그대로 찍는다
            ax.scatter([pos] * len(vals), vals, s=22, color='white', edgecolor=INK,
                       linewidth=0.8, zorder=3)
        xs = [x + (s - 0.5) * (BAR_WIDTH + GAP) for x in range(len(rates))]
        bars = ax.bar(xs, means, BAR_WIDTH, color=color, label=reliability, zorder=2)
        ax.bar_label(bars, fmt='%.2f', padding=8, color=INK, fontsize=9)

    ax.set_xticks(range(len(rates)), [f'{rate} Hz' for rate in rates])
    ax.set_ylabel(ylabel, color=INK)
    ax.set_ylim(bottom=0)
    ax.margins(y=0.15)
    ax.tick_params(colors=INK, length=0)
    ax.grid(axis='y', color=GRID, linewidth=0.8, zorder=0)
    for side in ('top', 'right', 'left'):
        ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    reps = len({r['repetition'] for r in rows})
    ax.set_title(f'{ylabel}: bar = mean, dot = run (up to {reps} runs per condition)',
                 color=INK, fontsize=10, loc='left', pad=18)
    ax.legend(frameon=False, labelcolor=INK, loc='upper center', ncol=2,
              bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--summary', default='results/csv/summary.csv')
    p.add_argument('--out-dir', default='results/figures')
    a = p.parse_args()

    with open(a.summary, newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f'집계 결과가 없음: {a.summary}')
    os.makedirs(a.out_dir, exist_ok=True)
    for field, ylabel, scale, name in CHARTS:
        plot(rows, field, ylabel, scale, os.path.join(a.out_dir, name))


if __name__ == '__main__':
    main()
