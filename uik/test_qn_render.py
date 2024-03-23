from uik.pil_qms_renderer import QmsRenderer, FigServer, FigArea, FigWay
from uik.qms.request_source import RequestsSource
from uik.qms.server import Server
from uik.qms.time import world_time
from uik.qms.util import requests

server1 = Server(2, 7)
server2 = Server(4, 12)

source = RequestsSource.new(requests(100).per_time(100))

source.connect(server1.connect(server2))

renderer = QmsRenderer("test1", 200)

renderer.entry_point = (0.26, 1.0)
renderer.exit_point = (0.9, 0.2)
renderer.add_area(FigArea((0, 0, 1, 0.5), (0, 0, 255, 16)))
renderer.add_server(FigServer(server1, "Server 1", 0.1, "navy", (0.5, 0.7), horizontal=False))
renderer.add_server(FigServer(server2, "Server 2", 0.06, "blue", (0.1, 0.1), horizontal=True))
renderer.add_way(FigWay(None, server1))
renderer.add_way(FigWay(server1, server2))
renderer.add_way(FigWay(server2, None))
renderer.request_processing_color = "green"
renderer.request_queue_color = "red"

for i in range(150):
    world_time.tick(1)
    source.tick()
    renderer.render_system_frame(source, False)

renderer.save_animation()