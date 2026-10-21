# safety.py - 정지 감지(StuckDetector). ROS와 분리해 단위 테스트가 쉽도록 만든다.
import math


class StuckDetector:
    """
    전진 명령 중 실제 이동 거리를 감시해 정지(stuck)를 판정한다.

    - window_s 동안 이동 거리가 move_eps보다 작으면 stuck으로 본다.
    - register()는 stuck 발생 시각을 시간창(counter_window_s) 안에서 세어
      재시도 횟수를 제한할 때 쓴다.
    """

    def __init__(self, window_s=1.0, move_eps=0.03,
                 counter_window_s=180.0, max_count=3):
        self.window_s = float(window_s)
        self.move_eps = float(move_eps)
        self.counter_window_s = float(counter_window_s)
        self.max_count = int(max_count)
        self._start = None   # (시각, x, y)
        self._times = []     # stuck 발생 시각 목록

    @property
    def count(self):
        """기록된 stuck 횟수(시간창 밖 기록은 register 때 정리된다)."""
        return len(self._times)

    def reset(self):
        """이동 감시 창을 새로 시작한다 (상태 전환, odom 끊김 때)."""
        self._start = None

    def update(self, now_s, x, y):
        """현재 위치를 넣고, 창이 끝났을 때 정지로 판정되면 True를 반환한다."""
        if self._start is None:
            self._start = (now_s, x, y)
            return False

        start_t, start_x, start_y = self._start
        if now_s - start_t < self.window_s:
            return False

        moved = math.hypot(x - start_x, y - start_y)
        self._start = (now_s, x, y)  # 다음 창 시작
        return moved < self.move_eps

    def register(self, now_s):
        """Stuck 발생을 기록하고, 시간창 안의 누적 횟수를 반환한다."""
        self._times = [t for t in self._times
                       if now_s - t <= self.counter_window_s]
        self._times.append(now_s)
        return len(self._times)
