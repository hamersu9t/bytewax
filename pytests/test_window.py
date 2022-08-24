from collections import defaultdict
from datetime import timedelta, datetime

from bytewax.dataflow import Dataflow
from bytewax.execution import run_main
from bytewax.inputs import TestingInputConfig
from bytewax.outputs import TestingOutputConfig
from bytewax.window import TestingClockConfig, TumblingWindowConfig


def test_tumbling_window():
    flow = Dataflow()

    def gen():
        for _ in range(4):
            yield ("ALL", 1)

    flow.input("inp", TestingInputConfig(gen()))

    start_at = datetime(2022, 1, 1)
    # This will result in times for events of +0, +4, +8, +12.
    clock_config = TestingClockConfig(item_incr=timedelta(seconds=4), start_at=start_at)
    # And since the window is +10, we should get a window with value
    # of 3 and then 1.
    window_config = TumblingWindowConfig(
        length=timedelta(seconds=10), start_at=start_at
    )

    def add(acc, x):
        return acc + x

    flow.reduce_window("sum", clock_config, window_config, add)

    out = []
    flow.capture(TestingOutputConfig(out))

    run_main(flow)

    assert sorted(out) == sorted([("ALL", 3), ("ALL", 1)])


def test_fold_window():
    def gen():
        yield from [
            {"user": "a", "type": "login"},
            {"user": "a", "type": "post"},
            {"user": "a", "type": "post"},
            {"user": "b", "type": "login"},
            {"user": "a", "type": "post"},
            {"user": "b", "type": "post"},
            {"user": "b", "type": "post"},
        ]

    def extract_id(event):
        return (event["user"], event)

    def build():
        return defaultdict(lambda: 0)

    def count(results, event):
        results[event["type"]] += 1
        return results

    start_at = datetime(2022, 1, 1)
    # This will result in times for events of +0, +4, +8, +12.
    clock_config = TestingClockConfig(
        item_incr=timedelta(seconds=4), start_at=start_at
    )
    # And since the window is +10, we should get a window with value
    # of 3 and then 1.
    window_config = TumblingWindowConfig(length=timedelta(seconds=10), start_at=start_at)

    flow = Dataflow()
    flow.input("inp", TestingInputConfig(gen()))
    flow.map(extract_id)
    flow.fold_window("sum", clock_config, window_config, build, count)

    out = []
    flow.capture(TestingOutputConfig(out))

    run_main(flow)

    assert len(out) == 3
    assert ("a", {"login": 1, "post": 2}) in out
    assert ("a", {"post": 1}) in out
    assert ("b", {"login": 1, "post": 2}) in out
