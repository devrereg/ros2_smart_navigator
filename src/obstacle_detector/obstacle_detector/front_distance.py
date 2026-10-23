# front_distance.py - 전방 최소 유효 거리 계산 (detector_node와 LaserScan_sub가 공유)
import math


def front_min_distance(msg, front_deg=30.0):
    """
    Return the minimum valid distance in the front sector of a LaserScan.

    LaserScan 정면 기준 전체 폭 front_deg 구간의 최소 유효 거리를 반환한다.

    - 구간은 인덱스 0(정면)을 중심으로 좌우 front_deg / 2 도이다.
    - 특수값은 REP 117 의미대로 구별한다.
      -inf(측정하기엔 너무 가까운 물체): range_min 거리의 장애물로 본다.
      +inf(범위 내 물체 없음): 장애물 후보에서 제외한다.
      NaN(측정 오류): 장애물 후보에서 제외한다.
    - 센서 측정 범위(range_min ~ range_max) 밖의 유한값은 제외한다.
    - 구간에 유효값이 하나도 없으면 float('inf')를 반환한다.
      단, 구간 전체가 NaN이면 앞을 못 보는 상태이므로 None을 반환한다.
    - angle_increment가 0 이하이거나 NaN/inf인 잘못된 스캔,
      또는 front_deg가 NaN/inf이면 None을 반환한다.
    """
    inc = msg.angle_increment
    if not math.isfinite(inc) or inc <= 0.0 or not math.isfinite(front_deg):
        return None
    n = len(msg.ranges)
    # 부동소수점 오차(14.9999...)로 경계 샘플이 빠지지 않도록 반올림한다
    half = round(math.radians(front_deg / 2) / inc)
    idx = list(range(0, min(half + 1, n))) + list(range(max(0, n - half), n))
    vals = []
    nan_count = 0
    for i in idx:
        r = msg.ranges[i]
        if math.isnan(r):
            nan_count += 1
        elif r == float('-inf'):
            vals.append(msg.range_min)
        elif r == float('inf'):
            continue
        elif msg.range_min < r < msg.range_max:
            vals.append(r)
    if vals:
        return min(vals)
    if idx and nan_count == len(idx):
        return None
    return float('inf')
