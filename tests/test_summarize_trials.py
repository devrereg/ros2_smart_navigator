import os
import sys

import pytest

pytest.importorskip('scipy')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from summarize_trials import summarize  # noqa: E402


def rows(passed, failed, excluded=0):
    return ([{'verdict': 'pass'}] * passed + [{'verdict': 'fail'}] * failed
            + [{'verdict': 'excluded'}] * excluded)


def test_day5_result_meets_target_but_ci_is_wide():
    s = summarize(rows(9, 1, excluded=5))
    assert (s['n'], s['passed'], s['excluded']) == (10, 9, 5)
    assert s['meets_target'] and not s['ci_above_target']
    assert s['ci_low'] == pytest.approx(0.555, abs=1e-3)


def test_many_trials_can_prove_target():
    assert summarize(rows(58, 2))['ci_above_target']


def test_no_judged_trials():
    assert summarize(rows(0, 0, excluded=3)) == {'n': 0, 'passed': 0, 'excluded': 3}
