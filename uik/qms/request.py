from uik.qms.time import world_time


class Request:
    def __init__(self):
        self.enter_time = world_time.time
        self.exit_time = -1

        self.server_queue_time = -1
        self.server_processing_enter_time = -1
        self.server_exit_time = -1

        self.servers_passed = []
        self.queue_waitings = []

    def exit(self):
        self.exit_time = world_time.time

    def on_server_queue(self, server):
        self.server_queue_time = world_time.time
        self.servers_passed.append(server)

    def on_server_processing_enter(self):
        self.server_processing_enter_time = world_time.time
        self.queue_waitings.append(self.server_processing_enter_time - self.server_queue_time)

    def on_server_exit(self):
        self.server_exit_time = world_time.time
