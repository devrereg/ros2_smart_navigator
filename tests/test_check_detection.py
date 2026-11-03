from collections import Counter
import math
import os
import sys

# scripts/는 패키지가 아니므로 경로를 직접 추가한다
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from check_detection import (  # noqa: E402
    align, EXTRA, expected_front, MATCH, MISMATCH, MISSING, NOT_PUBLISHED, trim_edges, verdict,
)

INF = float('inf')
NAN = float('nan')
INC = math.radians(1.0)  # 1도 해상도 (FakeScan과 같은 조건)
TOL = 1e-3


def front(ranges, angle_min=0.0, inc=INC, front_deg=30.0):
    """측정 범위 0.12 ~ 3.5 m로 expected_front를 호출한다."""
    return expected_front(ranges, angle_min, inc, 0.12, 3.5, front_deg)


def scan(fill=INF, **overrides):
    """360샘플을 fill로 채우고 i15=0.6처럼 지정한 인덱스만 덮어쓴다."""
    ranges = [fill] * 360
    for idx, value in overrides.items():
        ranges[int(idx.lstrip('i'))] = value
    return ranges


def results(expected, observed):
    """정렬 결과에서 판정만 꺼낸다."""
    return [r[2] for r in align(expected, observed, TOL)]


# --- expected_front: 기대값 계산 ---

def test_front_uses_sector_boundary():
    # 좌우 15도는 포함, 16도부터는 제외
    assert front(scan(i15=0.6)) == 0.6
    assert front(scan(i345=0.7)) == 0.7
    assert front(scan(i16=0.3, i344=0.3)) == INF


def test_front_special_values():
    assert front(scan(i0=-INF, i1=2.0)) == -INF  # -inf가 유효값보다 우선
    assert front(scan(i90=-INF)) == INF  # 구간 밖 -inf는 무시
    assert front(scan(fill=NAN)) is None  # 전체 NaN은 발행 안 함
    assert front(scan(fill=NAN, i0=INF)) == INF  # NaN이 아닌 값이 있으면 장애물 없음
    assert front(scan(i0=0.05, i1=9.0, i2=1.5)) == 1.5  # 센서 범위 밖 값 제외


def test_front_invalid_scan():
    assert front(scan(), inc=0.0) is None
    assert front(scan(), inc=NAN) is None
    assert front(scan(), front_deg=INF) is None


def test_front_follows_angle_min():
    # angle_min=-180도이면 정면은 인덱스 180이다
    ranges = scan(i180=0.8, i0=0.3)
    assert front(ranges, angle_min=-math.pi) == 0.8


# --- align: 기대값과 발행값 정렬 ---

def test_all_match():
    assert results([1.0, INF, -INF], [1.0, INF, -INF]) == [MATCH] * 3


def test_wrong_value_is_mismatch_only_at_that_sample():
    assert results([1.0, 1.1, 1.2], [1.0, 1.5, 1.2]) == [MATCH, MISMATCH, MATCH]


def test_inf_and_finite_do_not_match():
    assert results([INF], [3.0]) == [MISMATCH]


def test_tolerance():
    assert results([1.0], [1.0005]) == [MATCH]


def test_dropped_message_does_not_shift_the_rest():
    # 1.1이 누락돼도 뒤의 1.2, 1.3은 일치로 남아야 한다
    assert results([1.0, 1.1, 1.2, 1.3], [1.0, 1.2, 1.3]) == [MATCH, MISSING, MATCH, MATCH]


def test_extra_message_does_not_shift_the_rest():
    # 순서는 정렬 방식에 따라 달라질 수 있어 건수로 확인한다
    assert results([1.0, 1.2], [1.0, 9.0, 1.2])[0] == MATCH
    assert Counter(results([1.0, 1.2], [1.0, 9.0, 1.2])) == {MATCH: 2, EXTRA: 1}


def test_invalid_scan_must_not_publish():
    assert results([1.0, None, 1.2], [1.0, 1.2]) == [MATCH, NOT_PUBLISHED, MATCH]
    # 발행하면 안 되는 스캔 자리에 값이 오면 EXTRA로 잡는다
    assert Counter(results([1.0, None, 1.2], [1.0, 2.0, 1.2])) == {
        MATCH: 2, NOT_PUBLISHED: 1, EXTRA: 1}


# --- trim_edges: 양 끝 샘플 제외 ---

def test_trim_removes_only_edge_samples():
    rows = align([0.9, 1.0, 1.1], [1.0], TOL)
    assert [r[2] for r in trim_edges(rows, 3)] == [MATCH]


def test_trim_keeps_failure_longer_than_edge():
    # 수집 도중 detector가 죽으면 마지막 edge개만 빠지고 나머지는 실패로 남는다
    expected = [1.0 + i / 10 for i in range(10)]
    rows = trim_edges(align(expected, expected[:2], TOL), 3)
    assert Counter(r[2] for r in rows) == {MATCH: 2, MISSING: 5}


def test_trim_keeps_mismatch_at_edge():
    # 값 오류는 수집 경계 때문에 생기지 않으므로 끝에 있어도 남긴다
    rows = align([1.0, 1.1], [1.0, 2.0], TOL)
    assert trim_edges(rows, 3)[-1][2] == MISMATCH


# --- verdict: 최종 판정 ---

def test_verdict():
    assert verdict(Counter({MATCH: 5, NOT_PUBLISHED: 1})) == 'PASS'
    assert verdict(Counter({MATCH: 5, MISSING: 1})) == 'FAIL'
    assert verdict(Counter({MATCH: 5, MISMATCH: 1})) == 'FAIL'
    assert verdict(Counter({MATCH: 5, EXTRA: 1})) == 'FAIL'
    assert verdict(Counter()) == 'INCONCLUSIVE'
    assert verdict(Counter({NOT_PUBLISHED: 3})) == 'INCONCLUSIVE'


def test_detector_not_running_is_not_pass():
    # 발행이 하나도 없으면 양 끝 제외를 거쳐도 FAIL이어야 한다
    rows = trim_edges(align([1.0] * 10, [], TOL), 3)
    assert verdict(Counter(r[2] for r in rows)) == 'FAIL'
