from random import uniform, randrange
import itertools
from dotmap import DotMap

MAX_VELOCITY = 10
HIT_BREAK_PERCENTAGE = 0.0


def tm_init(tm):
    tm.step = 0
    tm.all_cars = []
    tm.car_counter = 0
    tm.green_in_outs = None

    tm.nirvana = DotMap()
    tm.nirvana.name = "nirvana"
    tm.nirvana.length = 10
    tm.nirvana.slots = create_new_slots(tm.nirvana.length)
    tm.nirvana.density = 0

    for street in tm.streets:
        street.slots = create_new_slots(street.length)

    tm.in_outs = DotMap()
    for crossing in tm.crossings:
        crossing.green_situations_index = -1
        in_set = set()
        for line in crossing.lines:
            _in = line["in"]
            tm.in_outs[_in] = [] if _in not in tm.in_outs else tm.in_outs[_in]
            tm.in_outs[_in].append(line.out)
            in_set.add(_in)
        crossing.in_list = list(in_set)
        crossing.in_list.sort()

    tm_consolidate_streets_and_cars(tm)

    # statistics data for reward function RF
    from traffic_rewards import tm_car_crossing_init, tm_reset_nirvana_rewards
    tm_car_crossing_init(tm)
    tm_reset_nirvana_rewards(tm)

    return tm


def tm_create_cars(tm):
    for street in tm.streets:
        if 'density' in street:
            if street.slots[0] is None and uniform(0, 1) <= street.density:
                car = new_car(tm)
                car.street = street.name
                car.pos = 0
                street.slots[0] = car


def tm_consolidate_streets_and_cars(tm):
    tm_create_cars(tm)
    for street in tm.streets:
        street.slots = create_new_slots(street.length)
        outs = tm.in_outs[street.name] if street.name in tm.in_outs else None
        for car in tm.all_cars:
            if car.street == street.name:
                street.slots[car.pos] = car
                if car.next_street == "":
                    if outs is not None:
                        ri = randrange(0, len(outs))
                        car.next_street = outs[ri]
                    else:
                        car.next_street = tm.nirvana.name


def new_car(tm):
    car = DotMap()
    car.nr = tm.car_counter
    car.velocity = 0
    car.street = ''
    car.pos = -1
    car.next_street = ""
    tm.car_counter += 1
    tm.all_cars.append(car)
    # RF
    car.rf_start_step = tm.step
    car.rf_end_step = -1
    car.rf_waiting = 0
    return car


def tm_update_green_in_outs(tm):
    tm.green_in_outs = DotMap()
    for crossing in tm.crossings:
        green_lines = []
        if crossing.green_situations_index != -1:
            green_lines = crossing.green_situations[crossing.green_situations_index]
        for line in crossing.lines:
            line_in = line['in']
            if line_in not in tm.green_in_outs:
                tm.green_in_outs[line_in] = []
            if line.name in green_lines:
                tm.green_in_outs[line_in].append(line.out)


def next_free_slot(start_pos, slots):
    d = 0

    while True:
        d += 1
        if start_pos + d < len(slots):
            if slots[start_pos + d] is None:
                pass
            else:
                break
        else:
            break
    return d - 1


def tm_get_street(tm, name):
    if name == tm.nirvana.name:
        return tm.nirvana
    return [street for street in tm.streets if street.name == name][0]


def tm_next_step_street(tm, street, green_streets):
    for slot in street.slots:
        if slot is not None:
            car = slot
            n = []
            if car.next_street in green_streets:
                n = tm_get_street(tm, car.next_street).slots
            concat_slots = street.slots + n
            d0 = next_free_slot(car.pos, concat_slots)

            # RF
            if d0 == 0:
                car.rf_waiting += 1
            else:
                car.rf_waiting = 0

            t = min(car.velocity + 1, d0, MAX_VELOCITY)
            velocity = max(car.velocity - 1, 0) if uniform(0, 1) < HIT_BREAK_PERCENTAGE else t
            car.velocity = velocity
            new_pos = car.pos + car.velocity
            if new_pos < len(street.slots):
                car.pos = new_pos
            else:
                car.street = car.next_street
                car.pos = new_pos - len(street.slots)
                car.next_street = ""
                # RF
                if car.street == tm.nirvana.name:
                    car.rf_end_step = tm.step
                else:
                    tm.rf_car_crossing += 1


def tm_next_step(tm):
    tm_update_green_in_outs(tm)
    tm.step += 1

    for street in tm.streets:
        out_greens = [tm.nirvana.name]
        if street.name in tm.in_outs:
            out_greens = tm.green_in_outs[street.name]
        tm_next_step_street(tm, street, out_greens)

    tm_consolidate_streets_and_cars(tm)

    return tm


def create_new_slots(length):
    return [None] * length


def tm_get_green_streets(tm):
    green_streets = set()
    for crossing in tm.crossings:
        if crossing.green_situations_index != -1:
            for gs in crossing.green_situations[crossing.green_situations_index]:
                for line in crossing.lines:
                    if line.name == gs:
                        green_streets.add(line['in'])
    return green_streets


def tm_get_action_code(tm):
    shape = []
    indexes = []
    for crossing in tm.crossings:
        shape.append(len(crossing.green_situations))
        indexes.append(0 if crossing.green_situations_index == -1 else crossing.green_situations_index)
    return to_green_situation_action(indexes, shape)


def tm_action_shape(tm):
    shape = []
    for crossing in tm.crossings:
        shape.append(len(crossing.green_situations))
    return shape


def tm_apply_action_code(tm, action_code):
    indexes = tm_decode_action_code(tm, action_code)
    for i, index in enumerate(indexes):
        tm.crossings[i].green_situations_index = index

def tm_decode_action_code(tm, action_code):
    shape = tm_action_shape(tm)
    indexes = to_green_situation_indexes(action_code, shape)
    return indexes


def crossing_get_green_lines(crossing):
    _green_lines = []
    if crossing.green_situations_index == -1:
        return _green_lines
    _green_line_name_set = set(crossing.green_situations[crossing.green_situations_index])
    for line in crossing.lines:
        if line.name in _green_line_name_set:
            _green_lines.append(line)
    return _green_lines


def to_green_situation_action(indexes, shape):
    arg0 = [range(x) for x in shape]
    table = list(itertools.product(*arg0))
    tu = tuple(indexes)
    return table.index(tu)


def to_green_situation_indexes(action, shape):
    arg0 = [range(x) for x in shape]
    table = list(itertools.product(*arg0))
    return list(table[action])

def tm_max_encoded_index(tm):
    max = 1
    for crossing in tm.crossings:
        max = max * len(crossing.green_situations)
    return max

