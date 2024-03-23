### Для начала попробуем найти подходящие параметры модели,
### основываясь на данных, которые у нас есть
import datetime
import random

from matplotlib import pyplot as plt

from uik.qms.request_source import RequestsSource
from uik.qms.server import Server
from uik.qms.time import world_time
from uik.qms.util import hours, requests, Seconds, avg
from uik.uik_analyze_search_model import find_successful
from uik.uik_model import model_uik, START_TIME

### Данные:
##### - Пришедшие до 10 часов быстро всё проходили, они нам не очень интересны
##### - Известно, что бОльшая часть людей пришла в период с 10 до 14, т.к. люди отмечали увеличение очереди
##### - Известно, что УИК выдал избирателям 1830 бюллетеней
##### - Известно так же, что волонтёры опросили 1000 вышедших
##### - в УИК-е на входе стояла охрана, которая во-первых проводила досмотр, во-вторых - просила подождать, контролируя количество людей внутри УИК
##### - максимальная длина очереди была порядка сотен человек, если не тысяч. Можно взять 500 за нижнюю границу.
##### - По опросам:
##### --- в УИК-е было 2 кабинки для голосования
##### --- в УИК-е было 3-4 сотрудника, которые регистрировали голосующих и выдавали бюллетени. Чаще 4
##### --- досмотр проводился от 15 до 60 секунд, среднее время - 27.5
##### --- на досмотре как правило был один человек, остальные ждали * (у одного опрошенного был ответ, что кроме него досмотр проходили 3 человека, но скорее всего он имел ввиду стояние в очереди на досмотре, т.к. сотрудник с ручным металлоискателем был только один)
##### --- внутри УИК-а чаще всего не приходилось ждать вовсе, или приходилось немного подождать кабинку
##### --- время проведённое в очереди - от 4 до 6 часов. Среднее 5.16. 4 часа стояли те, кто пришёл в 11.45. 6 часов стояли те, кто пришёл в 12.30.
##### - Предположения, выдвинутые мной лично, которые попробуем проверить при моделировании:
##### --- В кабинке люди проводили от 5 секунд до 60 секунд.
##### --- Сотрудники УИКа принимали людей от 30 до 120 секунд. Им нужно было записать вручную данные человека и выдать бюллетень.


### Таким образом при моделировании будем учитывать
##### максимальная длина очереди на вход > 500
##### максимальная очередь внутри УИК < 4
##### заявки пришедшие в 11.45 находятся в очереди 4 часа, а 12.30 - 6 часов. +- , конечно
#####
DELTA = 60

### Смоделируем этот процесс, и сравним с вычисляемыми значениями
print("--------")

print("---- Initial ----")
model_uik(
    guard_processing_time=27.5,
    registrator_processing_time=75.5,
    box_processing_time=32.5,
    # requests_before_bq=294,
    # requests_bq=1795,
    # requests_after_bq=365,
    requests_total=1830,
    print_log=True
)

print("---- Slightly modified initial ----")
model_uik(
    guard_processing_time=25.5,
    registrator_processing_time=75.5,
    box_processing_time=32.5,
    # requests_before_bq=294,
    # requests_bq=1795,
    # requests_after_bq=365,
    requests_total=1830,
    print_log=True
)

print("---- Found 1 ----")
delta = 60
_, _, source = model_uik(
    guard_processing_time=23.26,
    registrator_processing_time=87.55,
    box_processing_time=40,
    requests_before_bq=146,
    requests_bq=2159,
    requests_after_bq=573,
    print_log=True,
    delta=delta
)


# xx = [datetime.datetime.combine(datetime.date.today(), datetime.time(START_TIME)) + datetime.timedelta(
#    seconds=r.enter_time) for r in source.stats_produced_requests if len(r.queue_waitings)]
def chart(source):
    start_datetime = datetime.datetime.combine(datetime.date.today(), datetime.time(START_TIME))

    xx = [start_datetime + datetime.timedelta(seconds=r.enter_time) for r in source.stats_produced_requests if
          r.exit_time > 0]
    xx = [x.strftime("%H:%M") for x in xx]
    # yy = [(r.queue_waitings[0]) for r in source.stats_produced_requests if len(r.queue_waitings)]
    yy = [start_datetime + datetime.timedelta(seconds=r.exit_time) for r in source.stats_produced_requests if
          r.exit_time > 0]
    yy = [y.strftime("%H:%M") for y in yy]

    # print(len(source.stats_produced_requests))
    # print(len([s for s in source.stats_produced_requests if len(s.queue_waitings)]))
    fig, ax = plt.subplots(2, 1)
    fig.set_figwidth(10)
    fig.set_figheight(20)
    # ax = fig.add_subplot()
    ax[0].plot(xx, yy)
    ax[0].set_xlabel('Время захода')
    ax[0].set_ylabel('Время выхода')
    xticks = ax[0].get_xticks()
    ax[0].set_xticks(xticks[::int(len(xticks) / 13)])
    ax[0].set_yticks(ax[0].get_yticks()[::(delta)])
    ax[0].grid(which='major', alpha=0.5)
    # plt.plot(source.next.stats_queue_lengths)

    yy = source.next.stats_queue_lengths
    xx = [start_datetime + datetime.timedelta(seconds=r * delta) for r, _ in enumerate(source.next.stats_queue_lengths)]
    xx = [x.strftime("%H:%M") for x in xx]

    ax[1].plot(xx, yy)
    ax[1].set_xlabel('Время')
    ax[1].set_ylabel('Длина очереди')
    xticks = ax[1].get_xticks()
    ax[1].set_xticks(xticks[::int(len(xticks) / 13)])
    # ax[1].set_xticks(ax[0].get_xticks()[::30])
    # ax[1].set_yticks(ax[0].get_yticks()[::60])
    ax[1].grid(which='major', alpha=0.5)

    plt.show()

chart(source)

model_uik(
    guard_processing_time=23.26,
    registrator_processing_time=87.55,
    box_processing_time=40,
    requests_before_bq=146,
    requests_bq=2159,
    requests_after_bq=573,
    print_log=False,
    delta=60 * 2 + 3,
    # animate_and_save_to="uik_1",
    separate_frames=False
)

print("---- Found - avg ----")
model_uik(
    guard_processing_time=23.26,
    registrator_processing_time=87.55,
    box_processing_time=40,
    requests_total=146 + 2159 + 573,
    print_log=True
)

## на ночь запустить с большим количеством, и большим диапазоном ожидаемых  обработанных реквестов
seed = 5
random.seed(seed)
print(f"seed: {seed}")
# find_successful(100_000)

### Попробуем ответить на вопросы

### 1. Мог ли УИК при таких вводных обработать 1800 желающих проголосовать?

### 2. А сколько мог максимально?

### 3. Мог ли УИК при таких вводных данных обработать столько желающих, сколько было бюллетеней?

### 4. При каких условиях ему это удалось бы?

# если надо обратать 7500 человек, то это у нас в среднем 0.16025641025641024 человека в секунду.

print("--- 7500 --- ")
model_uik(
    guard_processing_time=23.26,
    registrator_processing_time=87.55,
    box_processing_time=40,
    #requests_total=7500,
    requests_before_bq=2000,
    requests_bq=3500,
    requests_after_bq=2000,
    print_log=True,

    guards_count=4,
    registrator_count=15,
    boxes_count=7,

    # delta=60*5+1,
    # animate_and_save_to="uik_7500"
)

print("---- Found 4 ----")
delta = 60
_, _, source = model_uik(
    guard_processing_time=24.71,
    registrator_processing_time=77.47,
    box_processing_time=22.24,
    requests_before_bq=410,
    requests_bq=1810,
    #requests_after_bq=6789,
    requests_after_bq=100,
    print_log=True,
    delta=delta
)

chart(source)


print("----- Found Min -----")
# 196.28	159.09	74.34	1033	12	269	751	210

_, _, source = model_uik(
    guard_processing_time=196.28,
    registrator_processing_time=159.09,
    box_processing_time=74.34,
    requests_before_bq=12,
    requests_bq=269,
    requests_after_bq=751,
    print_log=True,
    delta=delta
)
chart(source)

print("----- Found Max ------")
#8.55  12.07  15.09 7330 880 5761 687 5470

_, _, source = model_uik(
    guard_processing_time=8.55,
    registrator_processing_time=12.07,
    box_processing_time=15.09,
    requests_before_bq=880,
    requests_bq=5761,
    requests_after_bq=687,
    print_log=True,
    delta=delta
)