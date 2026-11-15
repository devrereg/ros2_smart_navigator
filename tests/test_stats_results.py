import os
import random
import sys

pytest = __import__('pytest')
pytest.importorskip('scipy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from stats_results import analyze_metric, holm, power_note  # noqa: E402


def make_rows(effect, reps=10, seed=0):
    """RELIABLE이 effect만큼 큰 가짜 summary 행. 블록마다 0.3씩 드리프트를 넣는다."""
    rnd = random.Random(seed)
    rows = []
    for rep in range(1, reps + 1):
        for rel in ('RELIABLE', 'BEST_EFFORT'):
            for rate in (10, 50):
                y = 1.0 + (effect if rel == 'RELIABLE' else 0) + 0.3 * rep + rnd.gauss(0, 0.2)
                rows.append({'reliability': rel, 'pub_rate_hz': str(rate), 'repetition': str(rep),
                             'm': f'{y:.4f}', 'zero': '0.0'})
    return rows


def term(results, name):
    return next(r for r in results if r.get('term') == name)


def test_large_effect_is_significant():
    res = analyze_metric(make_rows(effect=1.0), 'm')
    assert term(res, 'reliability')['p_value'] < 0.001
    assert term(res, 'block')['p_value'] < 0.001  # 드리프트는 블록 항이 흡수한다
    assert term(res, 'RELIABLE-BEST_EFFORT @ 10Hz')['significant']
    assert term(res, 'RELIABLE-BEST_EFFORT @ 10Hz')['ci_low'] > 0


def test_no_effect_is_not_significant():
    res = analyze_metric(make_rows(effect=0.0, seed=3), 'm')
    assert term(res, 'reliability')['p_value'] > 0.05
    assert not term(res, 'RELIABLE-BEST_EFFORT @ 50Hz')['significant']


def test_constant_metric_is_skipped():
    res = analyze_metric(make_rows(effect=1.0), 'zero')
    assert len(res) == 1 and '검정 불필요' in res[0]['note']


def test_unbalanced_design_still_runs():
    rows = make_rows(effect=1.0)[1:]  # 실패한 실행 1회가 빠진 경우
    assert term(analyze_metric(rows, 'm'), 'reliability')['p_value'] < 0.001


def test_holm_and_power():
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert power_note(10, 10) > 0.8 > power_note(3, 3)
