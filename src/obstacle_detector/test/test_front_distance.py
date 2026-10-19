import math

from obstacle_detector.front_distance import front_min_distance


class FakeScan:
    """360샘플, 1도 해상도, 측정 범위 0.12 ~ 3.5 m인 LaserScan 대용."""

    def __init__(self, ranges, increment=math.radians(1.0)):
        self.ranges = ranges
        self.angle_increment = increment
        self.range_min = 0.12
        self.range_max = 3.5


def scan(fill=float('inf'), **overrides):
    ranges = [fill] * 360
    for idx, value in overrides.items():
        ranges[int(idx.lstrip('i'))] = value
    return FakeScan(ranges)


def test_returns_min_in_front():
    assert front_min_distance(scan(i0=1.0, i5=0.8)) == 0.8


def test_both_sides_within_15_deg():
    assert front_min_distance(scan(i15=0.6)) == 0.6
    assert front_min_distance(scan(i345=0.7)) == 0.7


def test_ignores_outside_front_range():
    assert front_min_distance(scan(i16=0.3, i344=0.3, i90=0.3, i180=0.3)) == float('inf')


def test_ignores_inf_and_nan():
    assert front_min_distance(scan(i0=float('nan'), i1=float('inf'), i2=2.0)) == 2.0


def test_ignores_out_of_sensor_range():
    assert front_min_distance(scan(i0=0.05, i1=9.0, i2=1.5)) == 1.5


def test_no_valid_value_is_inf():
    assert front_min_distance(scan()) == float('inf')


def test_invalid_scan_is_none():
    assert front_min_distance(FakeScan([1.0] * 360, increment=0.0)) is None


def test_front_deg_parameter():
    assert front_min_distance(scan(i20=0.5), front_deg=60.0) == 0.5
    assert front_min_distance(scan(i20=0.5), front_deg=30.0) == float('inf')
