import random

from uik.qms.time import world_time
from uik.uik_model import model_uik


def find_successful(attempts=10000):
    # attempts
    successful = []

    for i in range(attempts):
        gpt = random.uniform(5, 200)
        rpt = random.uniform(5, 200)
        bpt = random.uniform(5, 120)
        rbbq = random.uniform(0.1, 0.8)
        rb_beforebq = random.uniform(0.01, 1.0 - rbbq)
        rb_afterbq = 1.0 - rb_beforebq - rbbq
        came = random.randrange(1000, 10000)
        # if i < 10:
        #    print([gpt, rpt, bpt, came, int(came * rb_beforebq), int(came * rbbq), int(came * rb_afterbq)])
        # try:
        ok, max_processed, _ = model_uik(gpt, rpt, bpt, int(came * rb_beforebq), int(came * rbbq),
                                         int(came * rb_afterbq))  # , print_log=i < 10)
        # except ZeroDivisionError:
        #    ok = False
        if ok:
            successful.append(
                [gpt, rpt, bpt, came, int(came * rb_beforebq), int(came * rbbq), int(came * rb_afterbq), max_processed])
        if i > 0 and i % (attempts / 10) == 0:
            print(f"{100 * i / attempts}% found so far: {len(successful)}")

    print("Found: ", len(successful))
    for s in successful:
        print(s)
