from uik.qms.time import SecondsProvider, world_time


class ServerNode:
    def __init__(self, processing_time: SecondsProvider, parent_server):
        self.processing_time = processing_time
        self.request = None
        self.remaining_time = 0
        self.this_request_processing_time = 0
        self.parent_server = parent_server

        self.stats_total_processing_time = 0
        self.stats_total_idle_time = 0
        self.stats_total_passed_requests_count = 0

    def reset_stats(self):
        self.stats_total_processing_time = 0
        self.stats_total_idle_time = 0
        self.stats_total_passed_requests_count = 0

    def tick(self):
        remaining_delta = world_time.delta
        while remaining_delta > 0:
            if self.request is not None:
                # continue processing of same request
                if self.remaining_time >= remaining_delta:
                    self.remaining_time -= remaining_delta
                    self.stats_total_processing_time += remaining_delta
                    remaining_delta = 0
                else:
                    self.stats_total_processing_time += self.remaining_time
                    remaining_delta -= self.remaining_time
                    self.remaining_time = 0
                    self.parent_server.exit(self.request)
                    self.request = None
                    self.stats_total_passed_requests_count += 1
            elif len(self.parent_server.queue) > 0:
                # get next
                self.request = self.parent_server.queue.pop(0)
                self.request.on_server_processing_enter()
                self.this_request_processing_time = float(self.processing_time)
                self.remaining_time += self.this_request_processing_time
            else:
                # idle
                self.stats_total_idle_time += remaining_delta
                break
