import math

from obstacle_detector.front_distance import front_min_distance
import pytest
from sensor_monitor.scan_check import (front_min_by_angle, INCREMENT, RANGE_MAX, RANGE_MIN,
                                       same_distance, ScanTopicMatcher, scenario_ranges,
                                       SCENARIOS, sector_stats)

INF = float('inf')


class FakeScan:

    def __init__(self, ranges, increment=INCREMENT, angle_min=0.0):
        self.ranges = ranges
        self.angle_min = angle_min
        self.angle_increment = increment
        self.range_min = RANGE_MIN
        self.range_max = RANGE_MAX


def from_scenario(sc):
    return FakeScan(scenario_ranges(sc), increment=sc['increment'])


@pytest.mark.parametrize('sc', SCENARIOS, ids=lambda sc: sc['name'])
def test_detector_and_independent_calc_agree_with_expected(sc):
    msg = from_scenario(sc)
    assert same_distance(front_min_distance(msg), sc['expected'])
    assert same_distance(front_min_by_angle(msg), sc['expected'])


def test_angle_min_mismatch_is_detected():
    """라이다 0번 샘플이 정면이 아니면 두 계산이 달라져 불일치로 드러나야 한다."""
    ranges = [INF] * 360
    ranges[0] = 0.5  # 이 샘플은 실제로는 후방
    msg = FakeScan(ranges, angle_min=-math.pi)
    assert front_min_distance(msg) == 0.5
    assert front_min_by_angle(msg) == INF


def test_sector_stats():
    ranges = [INF] * 360
    ranges[0] = float('nan')
    ranges[1] = 0.05
    ranges[2] = -INF
    ranges[89] = 0.4  # 인덱스 90은 90.2도라 후방에 들어간다
    ranges[270] = 0.3
    ranges[180] = 0.2
    stats = sector_stats(FakeScan(ranges))
    assert stats['left_min'] == 0.4
    assert stats['right_min'] == 0.3
    assert stats['back_min'] == 0.2
    assert stats['all_min'] == -INF
    assert (stats['nan'], stats['neg_inf'], stats['out_of_range']) == (1, 1, 1)
    assert stats['pos_inf'] == 28  # 전방 31개 샘플 중 위 3개를 뺀 나머지


def statuses(rows):
    return [row['status'] for row in rows]


def test_matcher_pairs_in_either_arrival_order():
    m = ScanTopicMatcher()
    assert m.add_scan(0.0, 1.0, {}) == []
    assert statuses(m.add_topic(0.01, 1.0)) == ['match']
    assert m.add_topic(0.2, 2.0) == []
    assert statuses(m.add_scan(0.21, 2.0, {})) == ['match']


def test_matcher_reports_mismatch():
    m = ScanTopicMatcher()
    m.add_scan(0.0, 1.0, {})
    assert statuses(m.add_topic(0.01, 1.5)) == ['mismatch']


def test_matcher_recovers_after_startup_offset():
    m = ScanTopicMatcher()
    m.add_topic(0.0, 9.0)  # 기록 시작 전 스캔의 결과
    assert statuses(m.add_scan(0.2, 1.0, {})) == ['extra_topic']
    assert statuses(m.add_topic(0.21, 1.0)) == ['match']


def test_matcher_unpaired_scan():
    m = ScanTopicMatcher()
    assert m.add_scan(0.0, None, {}) == []
    assert statuses(m.add_scan(0.2, 1.0, {})) == ['skip_ok']
    assert m.poll(0.25) == []
    assert statuses(m.poll(0.5)) == ['no_topic']


def test_matcher_infinities():
    m = ScanTopicMatcher()
    m.add_scan(0.0, -INF, {})
    assert statuses(m.add_topic(0.01, -INF)) == ['match']
    m.add_scan(0.2, INF, {})
    assert statuses(m.add_topic(0.21, -INF)) == ['mismatch']


def test_trial_verdict():
    from sensor_monitor.scan_check import trial_verdict
    assert trial_verdict(0.48, 0.45, 3.0)[0] == 'pass'
    assert trial_verdict(0.49, 0.12, 3.0)[0] == 'fail'
    assert trial_verdict(INF, 0.21, 5.0)[0] == 'excluded'  # 정면 장애물 없음
    assert trial_verdict(INF, 0.12, 0.0)[0] == 'excluded'  # 스폰 끼임은 접촉보다 먼저 본다
