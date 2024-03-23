from __future__ import annotations

Seconds = float


def avg(values):
    return sum(values) / len(values)


def hours(v: int) -> Seconds:
    return v * 60 * 60


def minutes(v: int) -> Seconds:
    return v * 60


class RequestsPerTimeBuilder:
    def __init__(self, count: int):
        self.count = count
        self.seconds = 0

    def per_time(self, seconds: Seconds) -> RequestsPerTimeBuilder:
        self.seconds = seconds
        return self

    def avg_spawn_time(self) -> Seconds:
        return self.seconds / self.count

    def avg_spawn_rate(self):
        return self.count / self.seconds


def requests(v: int) -> RequestsPerTimeBuilder:
    return RequestsPerTimeBuilder(v)


