import csv
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from analyze_results import analyze, write_summary  # noqa: E402


def write_raw(directory, name, seqs):
    path = os.path.join(directory, name)
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['seq', 'send_time_ns', 'recv_time_ns', 'latency_ms', 'payload_bytes'])
        for seq in seqs:
            w.writerow([seq, 1_000_000_000 + seq, 1_001_000_000 + seq, f'{seq + 1:.3f}', 64])
    return path


def test_no_loss(tmp_path):
    path = write_raw(tmp_path, 'raw_reliable_10hz_1.csv', range(10))
    row, missing = analyze(path, 1.0)
    assert missing == []
    assert (row['sent_count'], row['received_count'], row['loss_count']) == (10, 10, 0)
    assert (row['receive_rate'], row['loss_rate']) == (1.0, 0.0)
    assert (row['reliability'], row['pub_rate_hz'], row['repetition']) == ('RELIABLE', 10, 1)


def test_middle_and_tail_loss(tmp_path):
    path = write_raw(tmp_path, 'raw_best_effort_10hz_2.csv', [0, 1, 3, 4, 5, 6, 7])
    row, missing = analyze(path, 1.0)
    assert missing == [2, 8, 9]
    assert (row['received_count'], row['loss_count']) == (7, 3)
    assert (row['receive_rate'], row['loss_rate']) == (0.7, 0.3)


def test_duplicates_and_reordering(tmp_path):
    path = write_raw(tmp_path, 'raw_reliable_10hz_1.csv', [0, 2, 1, 2, 3, 4, 5, 6, 7, 8, 9])
    row, missing = analyze(path, 1.0)
    assert missing == []
    assert (row['received_count'], row['duplicate_count']) == (10, 1)
    assert row['out_of_order_count'] == 1


def test_latency_uses_all_rows(tmp_path):
    path = write_raw(tmp_path, 'raw_reliable_10hz_1.csv', range(10))
    row, _ = analyze(path, 1.0)
    assert row['latency_mean_ms'] == 5.5
    assert (row['latency_p95_ms'], row['latency_max_ms']) == (9.0, 10.0)


def test_wrong_duration_is_rejected(tmp_path):
    path = write_raw(tmp_path, 'raw_reliable_10hz_1.csv', range(20))
    with pytest.raises(SystemExit):
        analyze(path, 1.0)


def test_summary_replaces_same_run(tmp_path):
    summary = tmp_path / 'summary.csv'
    first = write_raw(tmp_path, 'raw_reliable_10hz_1.csv', range(9))
    other = write_raw(tmp_path, 'raw_reliable_10hz_2.csv', range(10))
    write_summary(summary, [analyze(first, 1.0)[0], analyze(other, 1.0)[0]])
    write_raw(tmp_path, 'raw_reliable_10hz_1.csv', range(10))
    write_summary(summary, [analyze(first, 1.0)[0]])
    with open(summary, newline='') as f:
        rows = list(csv.DictReader(f))
    assert [r['received_count'] for r in rows] == ['10', '10']
