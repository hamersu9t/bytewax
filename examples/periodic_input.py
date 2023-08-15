from datetime import datetime, timedelta, timezone

from bytewax.connectors.stdio import StdOutput
from bytewax.dataflow import Dataflow
from bytewax.inputs import (
    DynamicInput,
    PartitionedInput,
    StatefulSource,
    StatelessSource,
)


class PeriodicSource(StatelessSource):
    def __init__(self, frequency):
        self.frequency = frequency
        self._next_awake = datetime.now(timezone.utc)
        self._counter = 0

    def next_awake(self):
        return self._next_awake

    def next_batch(self):
        self._counter += 1
        if self._counter >= 10:
            raise StopIteration()
        # Calculate the delay between when this was supposed
        # to  be called, and when it is actually called
        delay = datetime.now(timezone.utc) - self._next_awake
        self._next_awake += self.frequency
        return [f"delay (ms): {delay.total_seconds() * 1000:.3f}"]


class PeriodicInput(DynamicInput):
    def __init__(self, frequency):
        self.frequency = frequency

    def build(self, worker_index, worker_count):
        return PeriodicSource(frequency=self.frequency)


stateless_flow = Dataflow()
stateless_flow.input("periodic", PeriodicInput(timedelta(seconds=1)))
stateless_flow.output("stdout", StdOutput())


class StatefulPeriodicSource(StatefulSource):
    def __init__(self, frequency, next_awake, counter):
        self.frequency = frequency
        self._next_awake = next_awake
        self._counter = counter

    def next_batch(self):
        self._counter += 1
        if self._counter >= 10:
            raise StopIteration()
        # Calculate the delay between when this was supposed
        # to  be called, and when it is actually called
        delay = datetime.now(timezone.utc) - self._next_awake
        self._next_awake += self.frequency
        return [f"delay (ms): {delay.total_seconds() * 1000:.3f}"]

    def snapshot(self):
        return {
            "next_awake": self._next_awake.isoformat(),
            "counter": self._counter,
        }

    def next_awake(self):
        return self._next_awake


class PeriodicPartitionedInput(PartitionedInput):
    def __init__(self, frequency):
        self.frequency = frequency

    def list_parts(self):
        return ["singleton"]

    def build_part(self, for_part, resume_state):
        assert for_part == "singleton"
        resume_state = resume_state or {}
        next_awake = datetime.fromisoformat(
            resume_state.get("next_awake", datetime.now(timezone.utc).isoformat())
        )
        counter = resume_state.get("counter", 0)
        return StatefulPeriodicSource(self.frequency, next_awake, counter)


stateful_flow = Dataflow()
stateful_flow.input("periodic", PeriodicPartitionedInput(timedelta(seconds=1)))
stateful_flow.output("stdout", StdOutput())
