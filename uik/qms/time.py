from uik.qms.util import Seconds


class Time:
    time: Seconds
    delta: Seconds

    def __init__(self):
        self.time = 0.0
        self.delta = 0.0

    def tick(self, delta):
        self.delta = float(delta)
        self.time += float(delta)

    def reset(self):
        self.time = 0.0


SecondsProvider = any

world_time = Time()
