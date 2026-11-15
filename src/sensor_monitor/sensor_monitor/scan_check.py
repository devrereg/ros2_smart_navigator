# scan_check.py - 감지 검증용 순수 로직 (detection_log, sensor_fault_test가 공유, ROS 불필요)
# rclpy를 쓰지 않으므로 Gazebo 없이 pytest만으로 시험할 수 있다
from collections import deque
import math

# Gazebo 라이다는 샘플 간격이 1.0023도라 +15도 샘플이 15.03도에 놓인다
ANGLE_TOL_DEG = 0.1
INF = float('inf')


def sample_angles_deg(msg):
    """각 샘플의 각도를 -180 ~ 180도로 반환한다. 0도가 로봇 정면이다."""
    angles = []
    for i in range(len(msg.ranges)):
        a = msg.angle_min + i * msg.angle_increment
        # sin·cos을 거쳐 atan2로 되돌리면 360도를 넘는 각도도 -180 ~ 180도로 정규화된다
        angles.append(math.degrees(math.atan2(math.sin(a), math.cos(a))))
    return angles


def is_valid(msg, r):
    # -inf는 '너무 가까운 물체'(REP 117)이므로 장애물 후보로 인정한다
    return r == -INF or msg.range_min < r < msg.range_max


def front_min_by_angle(msg, front_deg=30.0):
    """
    Return the front minimum using sample angles.

    front_min_distance를 검증하려는 독립 구현이다. 인덱스가 아니라 angle_min을
    반영한 실제 각도로 구간을 고른다. 특수값 규칙은 front_min_distance와 같다.
    """
    inc = msg.angle_increment
    if not math.isfinite(inc) or inc <= 0.0 or not math.isfinite(front_deg):
        return None  # 잘못된 스캔: detector_node도 발행하지 않는 경우
    # front_deg는 전체 폭이므로 좌우 한쪽은 절반이다
    half = front_deg / 2 + ANGLE_TOL_DEG
    # 인덱스 계산 없이 각도만으로 전방 샘플을 고른다 (front_min_distance와 다른 방식)
    front = [r for r, a in zip(msg.ranges, sample_angles_deg(msg)) if abs(a) <= half]
    vals = [r for r in front if is_valid(msg, r)]
    if vals:
        return min(vals)
    # 전방 전체가 NaN이면 앞을 못 보는 상태, 그 외에는 장애물 없음(inf)
    if front and all(math.isnan(r) for r in front):
        return None
    return INF


def sector_stats(msg, front_deg=30.0):
    """좌·우·후방 최소 거리와 전방 구간의 특수값 개수를 반환한다."""
    # 측면·후방 값은 5일차 (9.0, -15.0) 회차처럼 전방 밖 접근을 분석할 때 쓴다
    half = front_deg / 2 + ANGLE_TOL_DEG
    mins = {'left_min': INF, 'right_min': INF, 'back_min': INF}
    counts = {'nan': 0, 'pos_inf': 0, 'neg_inf': 0, 'out_of_range': 0}
    inc = msg.angle_increment
    if not math.isfinite(inc) or inc <= 0.0:
        return {**mins, **counts, 'all_min': INF}  # 각도를 믿을 수 없어 구간을 나누지 않는다
    for r, a in zip(msg.ranges, sample_angles_deg(msg)):
        if abs(a) <= half:
            # 전방 구간: 어떤 특수값이 얼마나 들어왔는지 센다
            if math.isnan(r):
                counts['nan'] += 1
            elif r == INF:
                counts['pos_inf'] += 1
            elif r == -INF:
                counts['neg_inf'] += 1
            elif not is_valid(msg, r):
                counts['out_of_range'] += 1
        elif not math.isnan(r) and is_valid(msg, r):
            # 전방 밖: 각도 부호는 왼쪽(+), 오른쪽(-), 90도를 넘으면 후방
            key = 'back_min' if abs(a) > 90.0 else 'left_min' if a > 0 else 'right_min'
            mins[key] = min(mins[key], r)
    # 전체 방향 최소값은 5일차 접촉 의심 판정(0.15 m 이하)과 비교하기 위한 값이다
    front = front_min_by_angle(msg, front_deg)
    all_min = min(list(mins.values()) + ([front] if front is not None else []))
    return {**mins, **counts, 'all_min': all_min}


def same_distance(a, b, tol=1e-3):
    """두 거리가 같은지 본다. None과 ±inf는 값이 정확히 같아야 한다."""
    if a is None or b is None:
        return a is b
    if math.isinf(a) or math.isinf(b):
        return a == b
    # 토픽은 Float32라 double 계산값과 미세하게 다르므로 1 mm 오차를 허용한다
    return abs(a - b) <= tol


class ScanTopicMatcher:
    """
    Pair each scan with the topic value that detector_node produced from it.

    Float32에는 타임스탬프가 없어 수신 시각이 window_s 안인 것끼리 순서대로 짝짓는다.
    5 Hz 스캔의 주기는 0.2초이므로 기본값 0.1초면 이웃한 스캔과 섞이지 않는다.
    반환 행의 status는 다음 중 하나다.
      match: 값 일치 / mismatch: 값 불일치 / skip_ok: 잘못된 스캔이라 미발행(정상)
      no_topic: 발행되어야 하는데 수신 없음 / extra_topic: 대응하는 스캔이 없는 토픽
    """

    def __init__(self, window_s=0.1):
        self.window_s = window_s
        # 아직 짝을 찾지 못한 스캔과 토픽을 도착 순서대로 보관한다
        self.scans = deque()
        self.topics = deque()

    def add_scan(self, t, calc, info):
        self.scans.append((t, calc, info))
        return self.poll(t)

    def add_topic(self, t, value):
        self.topics.append((t, value))
        return self.poll(t)

    def poll(self, now):
        """짝이 확정된 항목을 행으로 반환한다. 스캔과 토픽은 어느 쪽이 먼저 와도 된다."""
        rows = []
        # 양쪽의 가장 오래된 항목끼리 비교한다
        while self.scans and self.topics:
            ts, tt = self.scans[0][0], self.topics[0][0]
            if abs(ts - tt) <= self.window_s:
                _, calc, info = self.scans.popleft()
                value = self.topics.popleft()[1]
                ok = same_distance(calc, value)
                rows.append(self._row('match' if ok else 'mismatch', calc, value, info))
            # 시각 차이가 크면 더 오래된 쪽은 짝이 없는 것이다. 이렇게 버려야
            # 기록 시작 시점의 어긋남이 이후 행까지 밀리지 않는다
            elif ts < tt:
                rows.append(self._no_topic(self.scans.popleft()))
            else:
                rows.append(self._row('extra_topic', None, self.topics.popleft()[1], {}))
        # 상대가 오지 않은 채 window_s가 지난 항목도 짝 없음으로 확정한다
        while self.scans and now - self.scans[0][0] > self.window_s:
            rows.append(self._no_topic(self.scans.popleft()))
        while self.topics and now - self.topics[0][0] > self.window_s:
            rows.append(self._row('extra_topic', None, self.topics.popleft()[1], {}))
        return rows

    def _no_topic(self, scan):
        _, calc, info = scan
        # calc가 None이면 detector_node가 발행하지 않는 게 정상이다
        return self._row('skip_ok' if calc is None else 'no_topic', calc, None, info)

    @staticmethod
    def _row(status, calc, topic, info):
        return {'status': status, 'calc': calc, 'topic': topic, **info}


SAMPLES = 360
INCREMENT = 6.28 / (SAMPLES - 1)  # models/turtlebot3_burger/model.sdf의 라이다 설정과 같다
RANGE_MIN = 0.12
RANGE_MAX = 3.5
NAN = float('nan')


def scenario(name, fill=INF, values=None, expected=INF, increment=INCREMENT):
    return {'name': name, 'fill': fill, 'values': values or {},
            'expected': expected, 'increment': increment}


# 11일차 회귀 시나리오. values는 {샘플 인덱스: 거리}, expected None은 '발행 없음'
SCENARIOS = [
    scenario('clear'),
    scenario('front_near', values={0: 0.35}, expected=0.35),
    scenario('front_far', values={0: 1.5}, expected=1.5),
    scenario('edge_left_in', values={15: 0.6}, expected=0.6),
    scenario('edge_left_out', values={16: 0.3}),
    scenario('edge_right_in', values={345: 0.7}, expected=0.7),
    scenario('edge_right_out', values={344: 0.3}),
    scenario('side_closer', values={0: 1.13, 90: 0.2}, expected=1.13),
    scenario('too_close', values={0: -INF, 1: 2.0}, expected=-INF),
    scenario('nan_mixed', values={0: NAN, 1: INF, 2: 2.0}, expected=2.0),
    scenario('all_nan', fill=NAN, expected=None),
    scenario('below_range_min', values={0: 0.05}),
    scenario('above_range_max', values={0: 9.0}),
    scenario('bad_increment', increment=0.0, expected=None),
]


def scenario_ranges(sc):
    ranges = [sc['fill']] * SAMPLES
    for i, value in sc['values'].items():
        ranges[i] = value
    return ranges


# 회피 시험 판정 기준 (5일차 test_plan.md와 같은 값)
CONTACT_DIST = 0.15  # 전체 방향 최소 거리가 이 값 이하이면 접촉 의심
STOP_DIST = 0.5  # avoider stop_dist. 전방 거리가 이보다 작아진 적이 있어야 정지 동작을 시험한 것
SPAWN_MOVE_MIN = 0.05  # 회차 전체 이동 거리가 이보다 작으면 스폰 직후 끼임


def trial_verdict(min_front, min_all, moved):
    """회피 시험 1회 판정: pass / fail / excluded와 이유를 반환한다."""
    if moved < SPAWN_MOVE_MIN:
        return 'excluded', '스폰 직후 움직이지 못함 (스폰 위치 불량)'
    if min_all <= CONTACT_DIST:
        return 'fail', f'전체 방향 최소 거리 {min_all:.3f} m <= {CONTACT_DIST} m (접촉 의심)'
    if min_front >= STOP_DIST:
        return 'excluded', '정면 장애물을 만나지 못해 정지 동작 미발동'
    return 'pass', ''
