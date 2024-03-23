import os
import shutil
from collections import namedtuple
from typing import Union, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageColor

from uik.qms.time import world_time

FigServer = namedtuple('FigServer',
                       ['object', 'name', 'size', 'color', 'coord', 'horizontal'],
                       defaults=[None, "", 0.1, "blue", (0.5, 0.5), True])

FigArea = namedtuple('FigArea', ['coords', 'color'])

FigWay = namedtuple('FigWay', ['from_obj', 'to_obj', 'points'], defaults=[None, None, None])


class QmsRenderer:
    def __init__(self, dir_path: str, size: int, render_size: int = 1000):
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            shutil.rmtree(dir_path)

        os.makedirs(dir_path, exist_ok=True)
        self.dir_path = dir_path
        self.size = size
        self.render_size = render_size
        self.img = Image.new("RGBA", (render_size, render_size), "white")
        self.img_draw = ImageDraw.Draw(self.img)
        self.servers = []
        self.areas = []
        self.ways = []
        self.entry_point = (0, 0)
        self.exit_point = (1, 1)
        self.request_size = 0.1
        self.pad = 0.02
        self.frame_nr = 0
        self.line_width = int(render_size / size)
        self.way_color = (128, 128, 0, 32)

        self.request_processing_color = "blue"
        self.request_queue_color = "purple"
        font_size = 200
        self.font = ImageFont.load_default(size=font_size)
        while self.img_draw.textlength("www|", font=self.font) > self.request_size * self.render_size * 1.6:
            font_size -= 1
            self.font = ImageFont.load_default(size=font_size)
        self.frame_images = []
        self.start_time = None

    def add_server(self, server: FigServer):
        self.servers.append(server)

    def add_way(self, way: FigWay):
        if way.points is None:
            s1 = [self.request_node_coord(s, 0) for s in self.servers if s.object == way.from_obj][
                0] if way.from_obj is not None else self.entry_point
            s2 = [self.request_queue_coord(s) for s in self.servers if s.object == way.to_obj][
                0] if way.to_obj is not None else self.exit_point
            way = FigWay(way.from_obj, way.to_obj, [s1, s2, ])
        self.ways.append(way)

    def add_area(self, area: FigArea):
        self.areas.append(area)

    def start_frame(self):
        self.img_draw.rectangle((0, 0, self.render_size, self.render_size), fill="white")
        for area in self.areas:
            self.img_draw.rectangle(self.pix(area.coords), fill=area.color)
        for way in self.ways:
            for i in range(len(way.points) - 1):
                self.img_draw.line([self.pix(way.points[i]), self.pix(way.points[i + 1])], fill=self.way_color,
                                   width=self.line_width)

    def pix(self, x: Union[float, int, Tuple[float, float], Tuple[float, float, float, float]]):
        if type(x) is float or (type(x) is int):
            return x * self.render_size
        else:
            return tuple(map(lambda x: self.pix(x), list(x)))

    def rect(self, coord, size):
        cx, cy = coord
        cx = self.pix(cx)
        cy = self.pix(cy)
        s = self.pix(size)

        return cx - s / 2, cy - s / 2, cx + s / 2, cy + s / 2

    def render_system(self, spawner):
        draw_next = spawner.next
        last_server = None
        while draw_next:
            self.draw_server(draw_next)
            last_server = draw_next
            draw_next = draw_next.next
        if last_server:
            cx, cy = self.pix(self.exit_point)
            w = self.font.getlength("www")
            self.img_draw.rounded_rectangle((cx - w * 0.6, cy - w / 2, cx + w * 0.6, cy + w / 2),
                                            fill=(255, 255, 0, 32))
            self.img_draw.text((cx - w / 2, cy - w / 2), str(last_server.stats_total_passed_requests_count),
                               fill=(64, 74, 0), font=self.font)

        if self.start_time:
            seconds_passed = world_time.time + self.start_time
            h = str(int(seconds_passed / 60 / 60))
            m = str(int((seconds_passed / 60) % 60))
            if len(h) == 1:
                h = "0" + h
            while len(m) < 2:
                m = "0" + m
            self.img_draw.text(self.pix((0.84, 0.9)), f"{h}:{m}", fill="black", font=self.font)

    def end_frame(self):
        frame = Image.new('RGBA', (self.size, self.size), "white")
        frame = Image.alpha_composite(frame, self.img.resize((self.size, self.size)))
        # frame = self.img.resize((self.size, self.size))
        frame = frame.convert("RGB")
        self.frame_images.append(frame)
        self.frame_nr += 1

    def render_system_frame(self, spawner, save_separate_frames=True):
        self.start_frame()
        self.render_system(spawner)
        self.end_frame()
        if save_separate_frames:
            self.save_frame()

    def draw_server(self, obj):
        for s in self.servers:
            if s.object == obj:
                idx = 0
                for n in obj.nodes:
                    (x, y) = self.node_coord(s, idx)
                    fill = s.color if n.request else "white"
                    self.img_draw.rectangle(self.rect((x, y), s.size), outline=s.color, fill=fill,
                                            width=self.line_width)

                    if n.request:
                        self.draw_request_animated(n.request, s, n, idx)
                    idx += 1
                for r in obj.queue:
                    self.draw_request_animated(r, s, None, -1)
                self.draw_queue_requests(self.request_queue_coord(s), len(obj.queue))

    def draw_request_animated(self, request, s, n, nidx):
        progress = (1 - n.remaining_time / n.this_request_processing_time) if n is not None else 0.0
        if progress >= 0.9 and s.object.next is None:
            # exit
            moving = (1.0 - progress) / 0.1
            prev_server = s.object
            this_server = None
            ways = [w for w in self.ways if w.from_obj == prev_server and w.to_obj == this_server]
            if len(ways):
                way = ways[0]
                # TODO: multi-line
                (x0, y0) = way.points[0]
                (x1, y1) = way.points[1]
                x1 = x0 + (x1 - x0) * moving
                y1 = y0 + (y1 - y0) * moving
                self.draw_request((x1, y1), 0.0)
                return

        if progress <= 0.1:  # first 10% of time
            queued_for_seconds = world_time.time - request.server_queue_time
            if queued_for_seconds < 5:
                moving = max(queued_for_seconds / 5, progress / 0.1)
                prev_server = request.servers_passed[-2] if len(request.servers_passed) > 1 else None
                this_server = request.servers_passed[-1]
                ways = [w for w in self.ways if w.from_obj == prev_server and w.to_obj == this_server]
                if len(ways):
                    way = ways[0]
                    # TODO: multi-line
                    (x0, y0) = way.points[0]
                    (x1, y1) = way.points[1]
                    x1 = x0 + (x1 - x0) * moving
                    y1 = y0 + (y1 - y0) * moving
                    self.draw_request((x1, y1), 0.0)
                    return

        if n is None:
            return
        self.draw_request(self.request_node_coord(s, nidx),
                          (1 - n.remaining_time / n.this_request_processing_time))

    def draw_request(self, coord, fillness):
        x, y = coord
        size1 = self.rect(coord, self.request_size)
        size2 = self.rect(coord, self.request_size * fillness)
        self.img_draw.ellipse(size1, outline=self.request_processing_color, width=self.line_width)
        self.img_draw.ellipse(size2, fill=self.request_processing_color)

    def draw_queue_requests(self, coord, count):
        size1 = self.rect(coord, self.request_size * 1.2)
        if count > 0:
            self.img_draw.ellipse(size1, outline=self.request_queue_color, width=self.line_width)
            x, y = self.pix(coord)
            y -= self.pix(self.request_size * 1.2 / 2)
            text_width = self.img_draw.textlength(str(count), font=self.font)
            self.img_draw.text((x - text_width / 2, y), str(count), fill=self.request_queue_color, font=self.font)
        else:
            r, g, b = ImageColor.getrgb(self.request_queue_color)
            self.img_draw.ellipse(size1, outline=(r, g, b, 64), width=self.line_width)

    def node_coord(self, s: FigServer, idx: int):
        (x, y) = s.coord
        pad_between = self.pad
        if s.size < self.request_size:
            pad_between += (self.request_size - s.size)
        if s.horizontal:
            x += idx * (s.size + pad_between)
        else:
            y += idx * (s.size + pad_between)
        return x, y

    def request_queue_coord(self, s: FigServer):
        (x, y) = s.coord
        pad_between = self.pad
        if s.size < self.request_size:
            pad_between += (self.request_size - s.size)

        if s.horizontal:
            x = x + (s.size / 2 + pad_between / 2) * (len(s.object.nodes) - 1)
            y = y + (self.pad + self.request_size) * 2.5
        else:
            y = y + (s.size / 2 + pad_between / 2) * (len(s.object.nodes) - 1)
            x = x - (self.pad + self.request_size) * 2.5
        return x, y

    def request_node_coord(self, s: FigServer, idx: int):
        (x, y) = self.node_coord(s, idx)
        if s.horizontal:
            return x, y + s.size / 2 + self.pad + self.request_size / 2
        else:
            return x - s.size / 2 - self.pad - self.request_size / 2, y

    def save_frame(self):
        self.frame_images[-1].save(self.dir_path + "/frame" + str(self.frame_nr) + ".png")

    def save_animation(self):
        self.frame_images[0].save(self.dir_path + "/animation.gif", format='GIF', save_all=True,
                                  append_images=self.frame_images[1:], loop=True)
