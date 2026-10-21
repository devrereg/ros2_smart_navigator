# test_safety.py - 정지 감지(StuckDetector) 단위 테스트. ROS/Gazebo 없이 실행 가능.
from obstacle_avoider.safety import StuckDetector


def test_first_update_just_starts_window():
    det = StuckDetector(window_s=1.0, move_eps=0.03)
    assert det.update(0.0, 1.0, 2.0) is False


def test_stuck_when_not_moved_for_window():
    det = StuckDetector(window_s=1.0, move_eps=0.03)
    det.update(10.0, 0.0, 0.0)
    assert det.update(10.5, 0.0, 0.0) is False   # 아직 0.5초
    assert det.update(11.0, 0.001, 0.0) is True  # 1초 동안 1mm -> stuck


def test_no_stuck_when_moving():
    det = StuckDetector(window_s=1.0, move_eps=0.03)
    det.update(0.0, 0.0, 0.0)
    assert det.update(1.0, 0.2, 0.0) is False
    assert det.update(2.0, 0.4, 0.0) is False


def test_move_eps_uses_distance_not_axis():
    det = StuckDetector(window_s=1.0, move_eps=0.03)
    det.update(0.0, 0.0, 0.0)
    # x 3cm, y 4cm -> 실제 이동 5cm (축 하나만 보면 놓칠 수 있음)
    assert det.update(1.0, 0.03, 0.04) is False


def test_reset_starts_new_window():
    det = StuckDetector(window_s=1.0, move_eps=0.03)
    det.update(0.0, 0.0, 0.0)
    det.reset()
    assert det.update(0.5, 0.0, 0.0) is False
    assert det.update(1.4, 0.0, 0.0) is False   # 0.9초
    assert det.update(1.5, 0.0, 0.0) is True    # 1.0초


def test_counter_prunes_old_events():
    det = StuckDetector(counter_window_s=180.0, max_count=3)
    assert det.register(0.0) == 1
    assert det.register(10.0) == 2
    assert det.register(20.0) == 3
    # 191초: 0(191초), 10(181초)은 창(180초) 밖, 20(171초)은 남음 -> 2
    assert det.register(191.0) == 2
    # 400초: 이전 기록 모두 창 밖 -> 1
    assert det.register(400.0) == 1


def test_counter_keeps_events_inside_window():
    det = StuckDetector(counter_window_s=180.0, max_count=3)
    det.register(0.0)
    det.register(100.0)
    assert det.register(170.0) == 3
