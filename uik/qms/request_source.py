from __future__ import annotations
from uik.qms.request import Request
from uik.qms.time import world_time, SecondsProvider
from uik.qms.util import RequestsPerTimeBuilder


class RequestsSource:
    def __init__(self, producing_time: SecondsProvider, stop_after: int = 999999999):
        self.producing_time = producing_time
        self.remaining_time = 0
        self.next = None
        self.remaining_count = stop_after

        self.stats_produced_requests = []

    @staticmethod
    def new(r: RequestsPerTimeBuilder) -> RequestsSource:
        return RequestsSource(r.avg_spawn_time(), r.count)

    def set(self, r: RequestsPerTimeBuilder):
        self.producing_time = r.avg_spawn_time()
        self.remaining_count = r.count

    def connect(self, next):
        self.next = next

    def tick(self):
        remaining_delta = world_time.delta
        while remaining_delta > 0 and self.remaining_count > 0:
            if self.remaining_time <= remaining_delta:
                new_request = Request()
                self.stats_produced_requests.append(new_request)
                self.remaining_count -= 1
                if self.next is not None:
                    self.next.enter(new_request)
                else:
                    new_request.exit()
                remaining_delta -= self.remaining_time
                self.remaining_time = float(self.producing_time)
            else:
                self.remaining_time -= remaining_delta
                break
        if self.next:
            self.next.tick()
