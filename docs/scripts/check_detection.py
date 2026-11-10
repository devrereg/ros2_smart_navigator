"""/scan으로 다시 계산한 전방 거리와 /obstacle/front_distance의 일치 여부를 확인한다."""
import argparse
from collections import Counter
import csv
from datetime import datetime
import math
import os
import sys
import time

# 샘플별 판정 값. CSV의 result 열과 화면 집계에 그대로 쓰인다.
MATCH = 'MATCH'                  # 값 일치
MISMATCH = 'MISMATCH'            # 발행됐지만 값이 다름
MISSING = 'MISSING'              # 발행돼야 하는데 없음
EXTRA = 'EXTRA'                  # 대응하는 스캔이 없는 발행
NOT_PUBLISHED = 'NOT_PUBLISHED'  # 잘못된 스캔이라 발행하지 않음 (정상)

# 결과 CSV의 열 순서
FIELDS = ['scan_seq', 'scan_stamp', 'expected', 'observed', 'result']
BAND_MARGIN = 50  # 정렬할 때 허용하는 앞뒤 어긋남(샘플)


def expected_front(ranges, angle_min, inc, range_min, range_max, front_deg=30.0):
    """
    스캔에서 기대하는 전방 거리를 계산한다.

    검증 대상과 같은 함수를 쓰면 계산 오류를 잡지 못하므로 front_min_distance를
    호출하지 않는다. 정면도 인덱스 0으로 가정하지 않고 angle_min으로 찾는다.
    잘못된 스캔이나 전방 전체 NaN이면 None(발행 안 함이 정상)을 반환한다.
    """
    # 각도 정보가 잘못된 스캔은 구간을 정할 수 없다
    if not all(math.isfinite(v) for v in (angle_min, inc, front_deg)) or inc <= 0.0:
        return None
    n = len(ranges)
    # half: 정면에서 좌우로 포함할 샘플 수. detector_node와 같은 반올림 규칙을 쓴다
    half = round(math.radians(front_deg / 2) / inc)
    # center: 각도가 0도인 샘플의 인덱스 (angle_min=0이면 인덱스 0)
    center = round(-angle_min / inc) % n if n else 0
    # 스캔은 원형이므로 인덱스 거리는 양쪽 방향 중 짧은 쪽으로 잰다 (359번은 0번의 바로 옆)
    sector = [r for i, r in enumerate(ranges)
              if min((i - center) % n, (center - i) % n) <= half]

    # 특수값 우선순위: -inf(너무 가까움) > 유효 거리 > 전체 NaN > 그 외(장애물 없음)
    if float('-inf') in sector:
        return float('-inf')
    # 경계값은 제외한다. NaN과 +inf는 이 비교를 통과하지 못해 자동으로 빠진다
    valid = [r for r in sector if range_min < r < range_max]
    if valid:
        return min(valid)
    if sector and all(math.isnan(r) for r in sector):
        return None
    return float('inf')


def same(a, b, tol):
    """두 거리가 오차 안에서 같은지 판단한다. inf는 부호까지 같아야 같은 값이다."""
    if math.isinf(a) or math.isinf(b):
        return a == b
    return abs(a - b) <= tol


def align(expected, observed, tol):
    """
    기대값과 발행값을 순서를 유지한 채 맞춰 (스캔 번호, 발행 번호, 판정) 목록을 반환한다.

    Float32에는 stamp가 없어 시각으로 짝지을 수 없고, 단순 순번 비교는 한 건만
    빠져도 뒤가 전부 어긋난다. 그래서 불일치 건수가 최소인 정렬을 찾는다.
    """
    # cost[i, j]: 스캔 앞 i개와 발행 앞 j개를 맞췄을 때의 최소 불일치 건수 (동적 계획법)
    # back[i, j]: 그 최소값이 나온 직전 칸과 판정. 끝에서 되짚어 결과를 만든다
    n, m = len(expected), len(observed)
    # 대각선 근처만 계산해 긴 수집에서도 느려지지 않게 한다.
    # 폭이 건수 차이 이상이어야 (n, m)까지 가는 경로가 항상 존재한다
    band = abs(n - m) + BAND_MARGIN
    cost = {(0, 0): 0}
    back = {}
    for i in range(n + 1):
        for j in range(max(0, i - band), min(m, i + band) + 1):
            if i == 0 and j == 0:
                continue
            options = []  # (직전 칸, 추가 비용, 판정) 후보
            # 스캔과 발행을 짝짓는 경우. None 스캔은 발행이 없어야 하므로 짝짓지 않는다
            if i and j and expected[i - 1] is not None:
                ok = same(expected[i - 1], observed[j - 1], tol)
                options.append(((i - 1, j - 1), 0 if ok else 1, MATCH if ok else MISMATCH))
            # 스캔만 소비하는 경우: None 스캔이면 정상, 아니면 누락
            if i:
                none = expected[i - 1] is None
                options.append(((i - 1, j), 0 if none else 1, NOT_PUBLISHED if none else MISSING))
            # 발행만 소비하는 경우: 대응하는 스캔이 없는 발행
            if j:
                options.append(((i, j - 1), 1, EXTRA))
            # 폭 밖의 칸은 계산하지 않았으므로 후보에서 뺀다
            options = [o for o in options if o[0] in cost]
            prev, step, result = min(options, key=lambda o: cost[o[0]] + o[1])
            cost[i, j] = cost[prev] + step
            back[i, j] = (prev, result)

    # 끝 칸에서 시작점까지 되짚는다. 없는 쪽의 번호는 None으로 둔다
    rows = []
    pos = (n, m)
    while pos != (0, 0):
        prev, result = back[pos]
        rows.append((
            pos[0] - 1 if result != EXTRA else None,
            pos[1] - 1 if result not in (MISSING, NOT_PUBLISHED) else None,
            result,
        ))
        pos = prev
    rows.reverse()  # 끝에서부터 모았으므로 시간 순서로 되돌린다
    return rows


def trim_edges(rows, edge):
    """수집 시작·종료 순간에 한쪽 토픽만 잡힌 샘플을 양 끝에서 edge개까지 제외한다."""
    # MISMATCH는 실제 값 오류이므로 끝에 있어도 제외하지 않는다
    start, end = 0, len(rows)
    while start < min(edge, end) and rows[start][2] in (MISSING, EXTRA):
        start += 1
    tail = 0
    while tail < edge and end > start and rows[end - 1][2] in (MISSING, EXTRA):
        end -= 1
        tail += 1
    return rows[start:end]


def verdict(counts):
    """집계로 최종 판정을 낸다. 일치 건수가 0이면 확인한 것이 없으므로 PASS가 아니다."""
    if counts[MISMATCH] or counts[MISSING] or counts[EXTRA]:
        return 'FAIL'
    return 'PASS' if counts[MATCH] else 'INCONCLUSIVE'


def fmt(value):
    """CSV에 쓸 거리 문자열을 만든다. 값이 없으면 빈 칸이다."""
    return '' if value is None else f'{value:.4f}'


def write_csv(path, scans, observed, rows):
    """정렬 결과를 샘플당 한 행으로 저장한다."""
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for si, oi, result in rows:
            # EXTRA는 대응하는 스캔이 없어 스캔 쪽 열을 비운다
            seq, stamp, exp = scans[si] if si is not None else ('', '', None)
            w.writerow({
                'scan_seq': seq,
                'scan_stamp': stamp,
                # 'none'은 발행하지 않는 것이 정상인 스캔, 빈 칸은 스캔 자체가 없는 행이다
                'expected': 'none' if si is not None and exp is None else fmt(exp),
                'observed': fmt(observed[oi]) if oi is not None else '',
                'result': result,
            })


def collect(duration, front_deg):
    """두 토픽을 구독해 (스캔 목록, 발행값 목록)을 반환한다."""
    # 계산 함수는 ROS 없이 테스트할 수 있도록 rclpy는 여기서만 불러온다
    import rclpy
    from rclpy.executors import ExternalShutdownException
    from rclpy.node import Node
    from sensor_msgs.msg import LaserScan
    from std_msgs.msg import Float32

    # seen: 첫 메시지가 도착한 토픽 이름
    scans, observed, seen = [], [], set()

    def on_scan(msg):
        seen.add('scan')
        if len(seen) < 2:  # 두 토픽이 모두 연결된 뒤부터 기록한다
            return
        stamp = msg.header.stamp.sec + msg.header.stamp.nanosec / 1e9
        exp = expected_front(msg.ranges, msg.angle_min, msg.angle_increment,
                             msg.range_min, msg.range_max, front_deg)
        scans.append((len(scans), f'{stamp:.3f}', exp))

    def on_distance(msg):
        seen.add('distance')
        if len(seen) == 2:
            observed.append(msg.data)

    rclpy.init()
    node = Node('detection_checker')
    # 검증 노드 쪽에서 메시지를 버리지 않도록 큐를 크게 잡는다 (QoS는 기본 Reliable)
    node.create_subscription(LaserScan, '/scan', on_scan, 100)
    node.create_subscription(Float32, '/obstacle/front_distance', on_distance, 100)
    node.get_logger().info(f'{duration:.0f}초 동안 수집합니다. Ctrl+C로 먼저 끝낼 수 있습니다.')
    deadline = time.monotonic() + duration
    try:
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.1)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass  # Ctrl+C로 끝내도 그때까지 모은 데이터는 분석한다
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    return scans, observed


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--duration', type=float, default=60.0, help='수집 시간(초)')
    p.add_argument('--front-deg', type=float, default=30.0, help='detector_node의 front_deg')
    p.add_argument('--tolerance', type=float, default=1e-3, help='일치로 보는 오차(m)')
    p.add_argument('--edge', type=int, default=3, help='양 끝에서 제외할 수 있는 샘플 수')
    p.add_argument('--out', default=None, help='결과 CSV 경로')
    a = p.parse_args()

    # 수집이 끝난 뒤 한 번에 분석한다
    scans, observed = collect(a.duration, a.front_deg)
    expected = [s[2] for s in scans]
    all_rows = align(expected, observed, a.tolerance)
    rows = trim_edges(all_rows, a.edge)
    counts = Counter(r[2] for r in rows)

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out = a.out or f'results/csv/detection_check_{stamp}.csv'
    write_csv(out, scans, observed, rows)

    # 값 분포를 함께 출력한다. 범위가 좁으면 로봇이 멈춘 채 비교했다는 뜻이다
    finite = [e for e in expected if e is not None and math.isfinite(e)]
    print(f'스캔 {len(scans)}건, 발행 {len(observed)}건, 양 끝 제외 {len(all_rows) - len(rows)}건')
    for name in (MATCH, MISMATCH, MISSING, EXTRA, NOT_PUBLISHED):
        print(f'{name}: {counts[name]}')
    if finite:
        print(f'유한 거리 범위: {min(finite):.3f} ~ {max(finite):.3f} m')
    print(f'+inf: {expected.count(float("inf"))}, -inf: {expected.count(float("-inf"))}, '
          f'발행 안 함: {expected.count(None)}')
    print(f'CSV: {out}')
    result = verdict(counts)
    print(f'판정: {result}')
    # 종료 코드로도 판정을 알린다
    sys.exit({'PASS': 0, 'FAIL': 1, 'INCONCLUSIVE': 2}[result])


if __name__ == '__main__':
    main()
