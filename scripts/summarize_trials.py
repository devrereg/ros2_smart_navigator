"""avoid_trials.csv를 Markdown으로 요약하고 회피 성공률의 95% 신뢰구간을 구한다. 필요: python3-scipy."""
import argparse
import csv

from scipy import stats

TARGET = 0.8  # plans.md 8장: 10회 중 8회 이상 안전 회피 또는 정지


def summarize(rows):
    """판정 대상(pass/fail)만으로 성공률과 Clopper-Pearson 95% CI를 구한다."""
    judged = [r for r in rows if r['verdict'] in ('pass', 'fail')]
    n, k = len(judged), sum(r['verdict'] == 'pass' for r in judged)
    out = {'n': n, 'passed': k, 'excluded': len(rows) - n}
    if n:
        ci = stats.binomtest(k, n).proportion_ci(0.95, method='exact')
        out.update(rate=k / n, ci_low=ci.low, ci_high=ci.high, meets_target=k / n >= TARGET,
                   # 하한이 목표를 넘어야 "목표 이상"이라고 통계적으로 말할 수 있다
                   ci_above_target=ci.low >= TARGET)
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument('csv', nargs='?', default='results/csv/avoid/avoid_trials.csv')
    a = p.parse_args()
    with open(a.csv, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    print('| 회차 | 시작 위치 | 이동 (m) | 정면 최소 (m) | 전체 최소 (m) | 최소 방향·시각 | 판정 | 이유 |')
    print('|---|---|---|---|---|---|---|---|')
    for r in rows:
        print(f"| {r['label']} | ({r['x_pose']}, {r['y_pose']}) | {r['moved_m']} | "
              f"{float(r['min_front']):.3f} | {float(r['min_all']):.3f} | "
              f"{r['min_all_sector']} {r['min_all_t_sec']}s | {r['verdict']} | {r['reason']} |")
    s = summarize(rows)
    if not s['n']:
        print('\n판정 대상 없음')
        return
    print(f"\n성공 {s['passed']}/{s['n']}회 ({s['rate']:.0%}), 제외 {s['excluded']}회. "
          f"95% CI {s['ci_low']:.0%}~{s['ci_high']:.0%}. "
          f"목표 {TARGET:.0%}: {'충족' if s['meets_target'] else '미달'}"
          f"{', CI 하한도 목표 이상' if s['ci_above_target'] else ', CI 하한은 목표 미만'}")


if __name__ == '__main__':
    main()
