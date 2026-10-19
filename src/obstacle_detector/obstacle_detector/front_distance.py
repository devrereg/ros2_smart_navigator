# front_distance.py - 전방 최소 유효 거리 계산 (detector_node와 LaserScan_sub가 공유)
import math


def front_min_distance(msg, front_deg=30.0):
    """
    Return the minimum valid distance in the front sector of a LaserScan.

    LaserScan 정면 기준 전체 폭 front_deg 구간의 최소 유효 거리를 반환한다.

    - 구간은 인덱스 0(정면)을 중심으로 좌우 front_deg / 2 도이다.
    - inf, NaN, 센서 측정 범위(range_min ~ range_max) 밖의 값은 제외한다.
    - 구간에 유효값이 하나도 없으면 float('inf')를 반환한다.
    - angle_increment가 0 이하인 잘못된 스캔이면 None을 반환한다.
    """
    inc = msg.angle_increment
    if inc <= 0.0:
        return None
    n = len(msg.ranges)
    # 부동소수점 오차(14.9999...)로 경계 샘플이 빠지지 않도록 반올림한다
    half = round(math.radians(front_deg / 2) / inc)
    idx = list(range(0, min(half + 1, n))) + list(range(max(0, n - half), n))
    vals = [
        msg.ranges[i] for i in idx
        if math.isfinite(msg.ranges[i]) and msg.range_min < msg.ranges[i] < msg.range_max
    ]
    return min(vals) if vals else float('inf')
