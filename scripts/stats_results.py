"""summary.csv로 QoS 조건 간 차이가 통계적으로 유의한지 검정한다. 필요: python3-scipy.

설계: 2x2 요인(Reliability x 발행 주기), 반복 회차 = 블록(난괴법). 실험 단위는 실행 1회다.
분석: 지표별 y ~ 블록 + R + F + RxF 이원분산분석(Type III, 효과 코딩),
     잔차 정규성(Shapiro-Wilk)·등분산(Brown-Forsythe) 확인,
     주기별 Reliability 단순효과는 같은 회차끼리 짝지은 Wilcoxon 부호순위(Holm 보정),
     효과크기 dz(차이 평균/차이 표준편차), 차이 평균의 95% 부트스트랩 CI.
"""
import argparse
import csv

import numpy as np
from scipy import stats

ALPHA = 0.05
METRICS = ['loss_rate', 'latency_mean_ms', 'latency_p95_ms']
FIELDS = ['metric', 'test', 'term', 'statistic', 'df', 'p_value', 'p_holm', 'effect',
          'effect_size', 'ci_low', 'ci_high', 'significant', 'note']


def _design(rows, terms):
    """효과 코딩(+1/-1) 설계 행렬. 블록은 첫 회차를 기준으로 한 합-0 코딩."""
    r = np.array([1.0 if x['reliability'] == 'RELIABLE' else -1.0 for x in rows])
    rates = sorted({int(x['pub_rate_hz']) for x in rows})
    f = np.array([1.0 if int(x['pub_rate_hz']) == rates[-1] else -1.0 for x in rows])
    blocks = sorted({x['repetition'] for x in rows})
    cols = {'intercept': [np.ones(len(rows))], 'reliability': [r], 'rate': [f],
            'reliability:rate': [r * f], 'block': []}
    for b in blocks[1:]:
        cols['block'].append(np.array([1.0 if x['repetition'] == b else
                                       -1.0 if x['repetition'] == blocks[0] else 0.0
                                       for x in rows]))
    return np.column_stack([c for t in terms for c in cols[t]]) if terms else None


def _sse(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    return float(resid @ resid), resid


def anova(rows, y):
    """Type III 이원분산분석. 각 항을 뺀 모형과 전체 모형의 잔차제곱합 차이로 F를 구한다."""
    full = ['intercept', 'block', 'reliability', 'rate', 'reliability:rate']
    X = _design(rows, full)
    sse, resid = _sse(X, y)
    df_err = len(y) - np.linalg.matrix_rank(X)
    if df_err <= 0 or sse == 0:
        return None, resid
    out = []
    for term in full[1:]:
        Xr = _design(rows, [t for t in full if t != term])
        df = np.linalg.matrix_rank(X) - np.linalg.matrix_rank(Xr)
        ss = _sse(Xr, y)[0] - sse
        F = (ss / df) / (sse / df_err)
        out.append({'term': term, 'statistic': F, 'df': f'{df},{df_err}',
                    'p_value': float(stats.f.sf(F, df, df_err)),
                    'effect': 'partial_eta2', 'effect_size': ss / (ss + sse)})
    return out, resid


def cohen_dz(d):
    sd = np.std(d, ddof=1)
    return 0.0 if sd == 0 else float(np.mean(d) / sd)


def holm(ps):
    """Holm-Bonferroni 보정 p값 (입력 순서 유지)."""
    order = np.argsort(ps)
    adj, running = [0.0] * len(ps), 0.0
    for i, k in enumerate(order):
        running = max(running, min(1.0, (len(ps) - i) * ps[k]))
        adj[k] = running
    return adj


def analyze_metric(rows, metric):
    y = np.array([float(r[metric]) for r in rows])
    base = {'metric': metric}
    if np.ptp(y) == 0:
        return [{**base, 'test': '-', 'note': f'모든 실행 값이 {y[0]}로 같음: 차이 없음, 검정 불필요'}]

    results = []
    table, resid = anova(rows, y)
    if table is None:
        results.append({**base, 'test': 'ANOVA',
                        'note': '자유도 부족 또는 잔차 0: 블록당 4조건이 모두 있어야 함'})
    else:
        for t in table:
            results.append({**base, 'test': 'ANOVA', **t, 'significant': t['p_value'] < ALPHA})
        sw = stats.shapiro(resid) if len(resid) >= 3 and np.ptp(resid) > 0 else None
        if sw:
            results.append({**base, 'test': 'Shapiro-Wilk(잔차)', 'term': '정규성',
                            'statistic': sw.statistic, 'p_value': sw.pvalue,
                            'note': '' if sw.pvalue >= ALPHA else
                            '정규성 기각: ANOVA보다 아래 Wilcoxon 결과를 우선 해석'})
    cells, by_block = {}, {}
    for r, v in zip(rows, y):
        key = (r['reliability'], int(r['pub_rate_hz']))
        cells.setdefault(key, []).append(v)
        by_block[key + (r['repetition'],)] = v
    groups = [g for g in cells.values() if len(g) >= 2]
    if len(groups) >= 2 and any(np.ptp(g) > 0 for g in groups):
        lv = stats.levene(*groups, center='median')
        results.append({**base, 'test': 'Brown-Forsythe', 'term': '등분산',
                        'statistic': lv.statistic, 'p_value': lv.pvalue,
                        'note': '' if lv.pvalue >= ALPHA else '등분산 기각: Wilcoxon 결과를 우선 해석'})

    simple = []
    for rate in sorted({k[1] for k in cells}):
        # 같은 회차(블록)의 두 실행을 짝지어 회차 간 변동을 없앤다
        pairs = [(('RELIABLE', rate, b), ('BEST_EFFORT', rate, b))
                 for b in sorted({r['repetition'] for r in rows})]
        d = np.array([by_block[a] - by_block[b] for a, b in pairs
                      if a in by_block and b in by_block])
        if len(d) < 2:
            continue
        row = {**base, 'test': 'Wilcoxon(대응)', 'term': f'RELIABLE-BEST_EFFORT @ {rate}Hz',
               'statistic': float(np.mean(d)), 'df': f'n={len(d)}',
               'p_value': 1.0 if not d.any() else float(stats.wilcoxon(d).pvalue),
               'effect': 'dz', 'effect_size': cohen_dz(d)}
        if np.ptp(d) > 0:
            ci = stats.bootstrap((d,), np.mean, n_resamples=5000,
                                 random_state=0).confidence_interval
            row['ci_low'], row['ci_high'] = ci.low, ci.high
        simple.append(row)
    for row, p_adj in zip(simple, holm([s['p_value'] for s in simple])):
        row['p_holm'], row['significant'] = p_adj, p_adj < ALPHA
    return results + simple


def run_stats(rows):
    return [r for m in METRICS for r in analyze_metric(rows, m)]


def power_note(n_per_cell, blocks, f=0.5):
    """효과 크기 f(Cohen, 0.5=큼)인 주효과를 alpha=0.05로 검출할 검정력."""
    n = 4 * n_per_cell
    df_err = n - 4 - (blocks - 1)
    crit = stats.f.ppf(1 - ALPHA, 1, df_err)
    return float(stats.ncf.sf(crit, 1, df_err, f * f * n))


def fmt(v):
    if isinstance(v, float):
        return f'{v:.4g}'
    return '' if v is None else str(v)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--summary', default='results/csv/summary.csv')
    p.add_argument('--out', default='results/csv/stats.csv')
    a = p.parse_args()
    with open(a.summary, newline='') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit(f'집계 결과가 없음: {a.summary}')

    results = run_stats(rows)
    with open(a.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows({k: fmt(r.get(k)) for k in FIELDS} for r in results)

    print('| 지표 | 검정 | 항 | 통계량 | df | p | p(Holm) | 효과크기 | 95% CI | 유의 | 비고 |')
    print('|---|---|---|---|---|---|---|---|---|---|---|')
    for r in results:
        ci = f"[{fmt(r['ci_low'])}, {fmt(r['ci_high'])}]" if 'ci_low' in r else ''
        sig = {True: '예', False: '아니오'}.get(r.get('significant'), '')
        cols = [r['metric'], r['test']] + [fmt(r.get(k)) for k in (
            'term', 'statistic', 'df', 'p_value', 'p_holm')] + [
            f"{fmt(r.get('effect'))} {fmt(r.get('effect_size'))}", ci, sig, fmt(r.get('note'))]
        print('| ' + ' | '.join(cols) + ' |')
    print(f'\n저장: {a.out}')


if __name__ == '__main__':
    main()
