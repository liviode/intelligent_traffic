from traffic_base import tm_get_street


def tm_reset_nirvana_rewards(tm):
    tm.rf_nirvana_sync_steps = tm.step


def tm_nirvana_rewards(tm):
    reward = 0
    for car in tm.all_cars:
        reward += 1 if car.rf_end_step > tm.rf_nirvana_sync_steps else 0
    return reward - tm_waiting_cars(tm)[0]


def tm_waiting_cars(tm):
    w1 = w2 = 0
    for car in tm.all_cars:
        if car.street != tm.nirvana.name and car.next_street != tm.nirvana.name:
            w1 += 1 if car.velocity == 0 else 0
            w2 += car.rf_waiting
    return w1, w2


def tm_car_crossing_reset(tm):
    tm.rf_car_crossing = 0


def tm_car_crossing_init(tm):
    tm.rf_car_crossing = 0
    tm.rf_car_crossing_average = 0
    tm.rf_car_crossing_last_step = 0


def tm_car_crossing_rewards(tm):
    waiting_sum = 0
    from traffic_base import tm_get_street
    for car in tm.all_cars:
        if car.rf_waiting > 0 and tm_get_street(tm, car.street).length == car.pos + 1:
            waiting_sum += car.rf_waiting

    current_car_crossing_award = tm.rf_car_crossing - waiting_sum
    diff_steps = tm.step - tm.rf_car_crossing_last_step
    tm.rf_car_crossing_average = \
        tm.rf_car_crossing_last_step * tm.rf_car_crossing_average + diff_steps * current_car_crossing_award
    tm.rf_car_crossing_average = tm.rf_car_crossing_average / tm.step if tm.step > 0 else 0
    tm.rf_car_crossing_last_step = tm.step
    return current_car_crossing_award


def tm_waiting_array(tm):
    _state = []
    for crossing in tm.crossings:
        for line in crossing.lines:
            in_street = tm_get_street(tm, line['in'])
            last_slot = in_street.slots[-1]
            waiting = 0 if last_slot is None else min(last_slot.rf_waiting, 20)
            _state.append(waiting)
    return _state
