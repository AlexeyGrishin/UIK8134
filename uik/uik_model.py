from uik.pil_qms_renderer import QmsRenderer, FigArea, FigServer, FigWay
from uik.qms.request_source import RequestsSource
from uik.qms.server import Server, calculate_load
from uik.qms.time import world_time
from uik.qms.util import requests, hours, Seconds, avg

START_TIME = 8
END_TIME = 21
TOTAL_TIME = END_TIME - START_TIME

BIG_Q_START = 10
BIG_Q_END = 14

DELTA = 60


def model_uik(
        guard_processing_time,
        registrator_processing_time,
        box_processing_time,
        requests_before_bq=None,
        requests_bq=None,
        requests_after_bq=None,

        requests_total=None,
        print_log=False,
        delta=DELTA,
        animate_and_save_to=None,
        separate_frames=False,

        guards_count=1,
        registrator_count=4,
        boxes_count=2
):
    world_time.reset()
    if requests_total is not None:
        requests_before_bq = requests_total * (BIG_Q_START - START_TIME) / TOTAL_TIME
        requests_bq = requests_total * (BIG_Q_END - BIG_Q_START) / TOTAL_TIME
        requests_after_bq = requests_total * (END_TIME - BIG_Q_END) / TOTAL_TIME

    if requests_bq <= 0 or requests_after_bq <= 0 or requests_before_bq <= 0:
        return False, 0, None

    guard = Server(guards_count, guard_processing_time)
    registrators = Server(registrator_count, registrator_processing_time)
    boxes = Server(boxes_count, box_processing_time)

    if animate_and_save_to:
        renderer = QmsRenderer(animate_and_save_to, 256, 1024)
        renderer.start_time = hours(START_TIME)
        renderer.add_area(FigArea((0, 0, 1, 0.5), (0, 0, 255, 32)))
        renderer.add_server(FigServer(guard, "guard", 0.2, "brown", (0.5, 0.7), horizontal=False))
        renderer.add_server(FigServer(registrators, "registrators", 0.1, "navy", (0.15, 0.1), horizontal=True))
        renderer.add_server(FigServer(boxes, "boxes", 0.12, "blue", (0.9, 0.2), horizontal=False))

        renderer.way_color = (0, 128, 0, 128)
        renderer.entry_point = (0.205, 1.0)
        renderer.exit_point = (0.85, 0.7)
        renderer.add_way(FigWay(None, guard))
        renderer.add_way(FigWay(guard, registrators))
        #renderer.add_way(FigWay(registrators, boxes))
        renderer.add_way(FigWay(boxes, None, [(0.8, 0.4), renderer.exit_point]))
    else:
        renderer = None

    source = RequestsSource.new(requests(requests_before_bq).per_time(hours(BIG_Q_START - START_TIME)))
    source.connect(guard.connect(registrators.connect(boxes)))
    for _ in range(0, hours(BIG_Q_START - START_TIME), delta):
        world_time.tick(delta)
        source.tick()
        if renderer:
            renderer.render_system_frame(source, separate_frames)

    source.set(requests(requests_bq).per_time(hours(BIG_Q_END - BIG_Q_START)))
    for _ in range(0, hours(BIG_Q_END - BIG_Q_START), delta):
        world_time.tick(delta)
        source.tick()
        if renderer:
            renderer.render_system_frame(source, separate_frames)

    source.set(requests(requests_after_bq).per_time(hours(END_TIME - BIG_Q_END)))
    for _ in range(0, hours(END_TIME - BIG_Q_END), delta):
        world_time.tick(delta)
        source.tick()
        if renderer:
            renderer.render_system_frame(source, separate_frames)

    max_guard_queue_length = max(*guard.stats_queue_lengths)
    max_guard_queue_waiting_time = max(*guard.stats_queue_waiting_times)

    max_uik_queue_length = max(*registrators.stats_queue_lengths) + max(*boxes.stats_queue_lengths)

    max_processed_requests = boxes.stats_total_passed_requests_count

    T1145: Seconds = (11 - START_TIME) * 60 * 60 + 45 * 60
    T1230: Seconds = (12 - START_TIME) * 60 * 60 + 30 * 60

    w1145 = []
    w1230 = []
    for r in source.stats_produced_requests:
        if len(r.queue_waitings) == 0:
            continue
        if abs(r.enter_time - T1145) < 30 * 60:
            w1145.append(r.queue_waitings[0])
        if abs(r.enter_time - T1230) < 30 * 60:
            w1230.append(r.queue_waitings[0])

    avg_waiting_1145 = avg(w1145) if len(w1145) > 0 else -1
    avg_waiting_1230 = avg(w1230) if len(w1230) > 0 else -1

    def ok(flag):
        return "[OK]" if flag else "[xx]"

    guard_queue_length_ok = max_guard_queue_length > 500
    uik_queue_length_ok = max_uik_queue_length < 4
    guard_queue_waiting_time_ok = max_guard_queue_waiting_time < hours(8)
    waiting_1145_ok = abs(avg_waiting_1145 - hours(4)) < 30 * 60
    waiting_1230_ok = abs(avg_waiting_1230 - hours(6)) < 30 * 60
    max_processed_requests_ok = 0 <= max_processed_requests <= 10000
    #max_processed_requests_ok = 1000 <= max_processed_requests <= 8000
    # max_processed_requests_ok = 1800 <= max_processed_requests <= 1900

    if renderer:
        renderer.save_animation()

    if print_log:
        print(f"{ok(guard_queue_length_ok)} Max Guard Queue Length: {max_guard_queue_length}")
        print(f"{ok(uik_queue_length_ok)} Max UIK queue Length: {max_uik_queue_length}")
        print(
            f"{ok(guard_queue_waiting_time_ok)} Max Guard Queue Waiting Time: {max_guard_queue_waiting_time / 60 / 60:.2f}h")
        print(f"{ok(waiting_1145_ok)} 11:45 Queue Waiting Time: {avg_waiting_1145 / 60 / 60:.2f}h")
        print(f"{ok(waiting_1230_ok)} 12:30 Queue Waiting Time: {avg_waiting_1230 / 60 / 60:.2f}h")
        print(f"{ok(max_processed_requests_ok)} Processed: {max_processed_requests}")
        print(f"    Came: {len(source.stats_produced_requests)}")
        print(f"    Guard Load: {calculate_load(guard) * 100:.2f}%")
        print(f"    Registrators Load: {calculate_load(registrators) * 100:.2f}%")
        print(f"    Boxes Load: {calculate_load(boxes) * 100:.2f}%")

    oks = [guard_queue_waiting_time_ok, uik_queue_length_ok, guard_queue_length_ok, waiting_1145_ok, waiting_1230_ok,
           max_processed_requests_ok]
    count_ok = len([ok for ok in oks if ok])
    count = len(oks)
    if count_ok + 1 == count and False:
        if not guard_queue_waiting_time_ok: print("only guard_queue_waiting_time_ok = false")
        if not uik_queue_length_ok: print("only uik_queue_length_ok = false")
        if not guard_queue_length_ok: print("only guard_queue_length_ok = false")
        if not waiting_1145_ok: print("only waiting_1145_ok = false")
        if not waiting_1230_ok: print("only waiting_1230_ok = false")
        if not max_processed_requests_ok: print("only max_processed_requests_ok = false")
    return (
            guard_queue_waiting_time_ok and uik_queue_length_ok and guard_queue_length_ok and waiting_1145_ok and waiting_1230_ok and max_processed_requests_ok), max_processed_requests, source
