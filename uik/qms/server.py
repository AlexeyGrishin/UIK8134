import random

from uik.qms.request import Request
from uik.qms.server_node import ServerNode
from uik.qms.time import SecondsProvider


class Server:
    def __init__(self, nodes_count: int, processing_time: SecondsProvider):
        self.nodes = []
        for i in range(nodes_count):
            self.nodes.append(ServerNode(processing_time, self))
        self.queue = []
        self.next = None

        self.stats_queue_waiting_times = []
        self.stats_total_passed_requests_count = 0
        self.stats_queue_lengths = []

    def reset_stats(self):
        self.stats_queue_waiting_times = []
        self.stats_total_passed_requests_count = 0
        self.stats_queue_lengths = []
        for n in self.nodes:
            n.reset_stats()
        if self.next:
            self.next.reset_stats()

    def enter(self, request: Request):
        request.on_server_queue(self)
        self.queue.append(request)

    def exit(self, request: Request):
        request.on_server_exit()
        self.stats_total_passed_requests_count += 1
        self.stats_queue_waiting_times.append(request.server_processing_enter_time - request.server_queue_time)
        if self.next is not None:
            self.next.enter(request)
        else:
            request.exit()

    def tick(self):
        nodes = self.nodes.copy()
        random.shuffle(nodes)
        for node in nodes:
            node.tick()
        self.stats_queue_lengths.append(len(self.queue))
        if self.next:
            self.next.tick()

    def connect(self, next):
        self.next = next
        return self


def calculate_load(server: Server):
    idle = 0.0
    processing = 0.0
    for n in server.nodes:
        idle += n.stats_total_idle_time
        processing += n.stats_total_processing_time
    return processing / (idle + processing)
