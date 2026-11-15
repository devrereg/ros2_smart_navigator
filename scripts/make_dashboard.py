"""테스트·실험 결과를 한 장의 HTML 대시보드로 모은다. 없는 입력은 '데이터 없음'으로 표시한다.

사용: python3 scripts/make_dashboard.py  → results/dashboard.html (브라우저로 열기)
"""
import argparse
import csv
from datetime import datetime
import glob
import html
import os
import statistics
import xml.etree.ElementTree as ET

from stats_results import ALPHA, METRICS, power_note, run_stats
from summarize_trials import summarize, TARGET

CSS = """
:root { --bg:#fcfcfb; --card:#fff; --ink:#1f1e1c; --muted:#6b6a66; --line:#e4e3df;
  --ok:#1f7a4d; --ok-bg:#e6f4ec; --ng:#b3261e; --ng-bg:#fbe9e7; --accent:#2a78d6; }
@media (prefers-color-scheme: dark) { :root { --bg:#161615; --card:#1f1f1d; --ink:#ecebe8;
  --muted:#a3a29d; --line:#34332f; --ok:#6fd19c; --ok-bg:#16301f; --ng:#ff8a80;
  --ng-bg:#3a1b18; --accent:#7ab3f5; } }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:14px/1.5 system-ui, 'Noto Sans KR', sans-serif; }
main { max-width:1100px; margin:0 auto; padding:24px 16px 48px; }
h1 { font-size:22px; margin:0 0 4px; } h2 { font-size:17px; margin:32px 0 8px; }
.muted { color:var(--muted); }
.cards { display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px;
  margin-top:16px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px; }
.card b { display:block; font-size:24px; }
.wrap { overflow-x:auto; }
table { border-collapse:collapse; width:100%; background:var(--card); font-size:13px; }
th, td { border-bottom:1px solid var(--line); padding:6px 8px; text-align:left;
  white-space:nowrap; }
td:last-child { white-space:normal; min-width:240px; }
th { color:var(--muted); font-weight:600; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.ok { color:var(--ok); } .ng { color:var(--ng); }
tr.sig td { background:var(--ok-bg); }
.figs { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:12px; }
.figs img { width:100%; border:1px solid var(--line); border-radius:8px; background:#fff; }
ul { margin:6px 0; padding-left:20px; }
"""


def esc(v):
    return html.escape('' if v is None else str(v))


def num(v, digits=4):
    return f'{v:.{digits}g}' if isinstance(v, float) else esc(v)


def table(head, rows, row_class=None):
    out = ['<div class="wrap"><table><tr>' + ''.join(f'<th>{esc(h)}</th>' for h in head) + '</tr>']
    for i, r in enumerate(rows):
        cls = f' class="{row_class[i]}"' if row_class and row_class[i] else ''
        out.append(f'<tr{cls}>' + ''.join(
            f'<td class="num">{num(c)}</td>' if isinstance(c, (int, float)) else f'<td>{c}</td>'
            for c in r) + '</tr>')
    return '\n'.join(out) + '</table></div>'


def read_csv(path):
    if not os.path.exists(path):
        return []
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def junit(paths):
    """pytest/colcon junit xml에서 통과·실패·건너뜀 수와 실패 테스트 이름을 모은다."""
    total = failed = skipped = 0
    failures = []
    for p in paths:
        for case in ET.parse(p).getroot().iter('testcase'):
            total += 1
            if case.find('skipped') is not None:
                skipped += 1
            elif case.find('failure') is not None or case.find('error') is not None:
                failed += 1
                failures.append(f"{case.get('classname')}.{case.get('name')}")
    return total, failed, skipped, failures


def md_table(path):
    """Markdown 표와 마지막 'N/M 통과' 줄을 읽는다 (run_sensor_regression.sh 출력)."""
    if not os.path.exists(path):
        return None, None
    with open(path, encoding='utf-8') as f:
        lines = [x.strip() for x in f if x.strip()]
    rows = [[c.strip() for c in x.strip('|').split('|')] for x in lines
            if x.startswith('|') and not set(x) <= set('|-: ')]
    verdict = next((x for x in reversed(lines) if '통과' in x and '/' in x), None)
    return rows, verdict


def card(title, value, ok=None, sub=''):
    cls = '' if ok is None else (' class="ok"' if ok else ' class="ng"')
    return (f'<div class="card"><span class="muted">{esc(title)}</span>'
            f'<b{cls}>{esc(value)}</b><span class="muted">{esc(sub)}</span></div>')


def qos_section(rows, order, figures_dir, out_dir):
    if not rows:
        return ('<h2>QoS 실험</h2><p class="muted">데이터 없음: '
                'scripts/run_experiment.sh 실행 후 다시 생성</p>', None)
    cells = {}
    for r in rows:
        cells.setdefault((r['reliability'], int(r['pub_rate_hz'])), []).append(r)
    n_cells = [len(v) for v in cells.values()]
    blocks = len({r['repetition'] for r in rows})
    seeds = {o['seed'] for o in order}
    parts = ['<h2>QoS 실험 설계</h2><ul>',
             f'<li>요인: Reliability {len({k[0] for k in cells})}수준 × 발행 주기 '
             f'{len({k[1] for k in cells})}수준, 셀 {len(cells)}개</li>',
             f'<li>반복: 셀당 {min(n_cells)}~{max(n_cells)}회, 블록(회차) {blocks}개, '
             f'실행 단위 = 실행 1회 (총 {len(rows)}회)</li>',
             '<li>실행 순서: ' + (f'블록 안 무작위 (SEED {esc(", ".join(sorted(seeds)))})'
                              if order else '<span class="ng">기록 없음 (run_order.csv)</span>')
             + '</li>',
             f'<li>검정력: 큰 효과(Cohen f=0.5) 주효과 검출 확률 '
             f'{power_note(min(n_cells), blocks):.0%} (α={ALPHA})</li>',
             f'<li>환경: {esc(rows[0].get("env_note"))}</li></ul>']

    head = ['조건', 'n'] + [f'{m} 평균 ± SD' for m in METRICS]
    body = []
    for key in sorted(cells):
        vals = cells[key]
        line = [f'{key[0]} {key[1]}Hz', len(vals)]
        for m in METRICS:
            xs = [float(v[m]) for v in vals]
            sd = statistics.stdev(xs) if len(xs) > 1 else 0.0
            line.append(f'{statistics.mean(xs):.4g} ± {sd:.2g}')
        body.append(line)
    parts += ['<h2>조건별 요약</h2>', table(head, body)]

    res = run_stats(rows)
    head = ['지표', '검정', '항', '통계량', 'df', 'p', 'p(Holm)', '효과크기', '95% CI', '비고']
    body, cls = [], []
    for r in res:
        ci = f"[{num(r['ci_low'])}, {num(r['ci_high'])}]" if 'ci_low' in r else ''
        body.append([esc(r['metric']), esc(r['test']), esc(r.get('term')), r.get('statistic', ''),
                     esc(r.get('df')), r.get('p_value', ''), r.get('p_holm', ''),
                     f"{esc(r.get('effect'))} {num(r.get('effect_size'))}", ci,
                     esc(r.get('note'))])
        cls.append('sig' if r.get('significant') else '')
    parts += ['<h2>통계 검정</h2>',
              f'<p class="muted">초록 행 = α={ALPHA}에서 유의. 단순효과(Wilcoxon)는 같은 회차끼리 '
              '짝지어 비교하고 지표 안에서 Holm 보정. 손실률·평균 지연이 주 지표, p95는 탐색 지표.</p>',
              table(head, body, cls)]

    figs = sorted(glob.glob(os.path.join(figures_dir, '*.png')))
    if figs:
        parts.append('<h2>그래프</h2><div class="figs">' + ''.join(
            f'<img src="{esc(os.path.relpath(f, out_dir).replace(os.sep, "/"))}" '
            f'alt="{esc(os.path.basename(f))}">' for f in figs) + '</div>')
    # 블록 항은 QoS 효과가 아니므로 세지 않는다
    return '\n'.join(parts), sum(1 for r in res if r.get('significant') and r['term'] != 'block')


def all_passed(verdict):
    return None if not verdict else verdict.split('/')[0] == verdict.split('/')[1].split()[0]


def md_section(title, path, hint):
    rows, verdict = md_table(path)
    if not rows:
        return f'<h2>{title}</h2><p class="muted">데이터 없음: {esc(hint)}</p>', verdict
    return (f'<h2>{title}</h2>' + table(rows[0], [[esc(c) for c in r] for r in rows[1:]],
                                        ['' if r[-1] == '통과' else 'ng' for r in rows[1:]]),
            verdict)


def trials_section(rows):
    if not rows:
        return ('<h2>회피 성공률</h2><p class="muted">데이터 없음: '
                'scripts/run_avoid_trials.sh 실행 후 다시 생성</p>', None)
    s = summarize(rows)
    head = ['회차', '시작 위치', '이동 (m)', '정면 최소 (m)', '전체 최소 (m)', '최소 방향', '판정', '이유']
    body = [[esc(r['label']), f"({esc(r['x_pose'])}, {esc(r['y_pose'])})", float(r['moved_m']),
             float(r['min_front']), float(r['min_all']), esc(r['min_all_sector']),
             esc(r['verdict']), esc(r['reason'])] for r in rows]
    cls = ['ng' if r['verdict'] == 'fail' else '' for r in rows]
    note = (f"성공 {s['passed']}/{s['n']}회, 95% CI {s['ci_low']:.0%}~{s['ci_high']:.0%} "
            f"(목표 {TARGET:.0%}, CI 하한이 목표 이상이어야 통계적으로 충족)" if s['n'] else '판정 대상 없음')
    return f'<h2>회피 성공률</h2><p class="muted">{note}</p>' + table(head, body, cls), s


def build(a):
    out_dir = os.path.dirname(os.path.abspath(a.out))
    total, failed, skipped, failures = junit([p for g in a.junit for p in glob.glob(g)])
    reg_html, verdict = md_section('센서 이상값 회귀 테스트', a.regression,
                                   f'scripts/run_sensor_regression.sh 출력을 {a.regression}에 저장')
    restart_html, restart = md_section('실행·종료·재실행 테스트', a.restart,
                                       f'scripts/run_restart_test.sh 출력을 {a.restart}에 저장')
    trial_html, ts = trials_section(read_csv(a.trials))
    rows, order = read_csv(a.summary), read_csv(a.order)
    qos_html, n_sig = qos_section(rows, order, a.figures, out_dir)

    cards = [
        card('단위 테스트', f'{total - failed - skipped}/{total - skipped} 통과' if total else '없음',
             None if not total else failed == 0, f'건너뜀 {skipped}' if total else ''),
        card('센서 이상값 회귀', verdict or '없음',
             all_passed(verdict)),
        card('회피 성공', f"{ts['passed']}/{ts['n']}회" if ts and ts['n'] else '없음',
             ts['meets_target'] if ts and ts['n'] else None,
             f"95% CI {ts['ci_low']:.0%}~{ts['ci_high']:.0%}" if ts and ts['n'] else ''),
        card('재실행', restart or '없음', all_passed(restart)),
        card('QoS 실행', f'{len(rows)}회' if rows else '없음', None,
             f'유의한 QoS 효과 {n_sig}건' if n_sig is not None else ''),
    ]
    parts = ['<!doctype html><html lang="ko"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f'<title>테스트 대시보드</title><style>{CSS}</style></head><body><main>',
             '<h1>Smart Navigator 테스트 대시보드</h1>',
             f'<p class="muted">생성 {datetime.now().isoformat(timespec="seconds")}</p>',
             '<div class="cards">' + ''.join(cards) + '</div>']
    if failures:
        parts.append('<h2>실패한 단위 테스트</h2><ul>'
                     + ''.join(f'<li class="ng">{esc(x)}</li>' for x in failures) + '</ul>')
    parts += [trial_html, restart_html, reg_html, qos_html]
    parts.append('</main></body></html>')
    return '\n'.join(parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--summary', default='results/csv/summary.csv')
    p.add_argument('--order', default='results/csv/run_order.csv')
    p.add_argument('--regression', default='results/csv/sensor_regression.md')
    p.add_argument('--restart', default='results/csv/restart_test.md')
    p.add_argument('--trials', default='results/csv/avoid/avoid_trials.csv')
    p.add_argument('--junit', nargs='*', default=['results/junit.xml', 'build/*/pytest.xml'])
    p.add_argument('--figures', default='results/figures')
    p.add_argument('--out', default='results/dashboard.html')
    a = p.parse_args()
    page = build(a)
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write(page)
    print(a.out)


if __name__ == '__main__':
    main()
