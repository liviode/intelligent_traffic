import json
import time
import io
from functools import partial
from itertools import accumulate
from tkinter import *
from tkinter import ttk

import gym
import numpy as np
from dotmap import DotMap
from gym.utils import seeding
from tkhtmlview import HTMLLabel
from tkinterhtml import HtmlFrame

from traffic_base import tm_get_street, tm_next_step, tm_init, tm_get_action_code, \
    tm_apply_action_code, crossing_get_green_lines, tm_action_shape, tm_decode_action_code
from traffic_base_tk import CrossingButton, TkStreet, get_html
from traffic_rewards import tm_reset_nirvana_rewards, tm_car_crossing_rewards, tm_car_crossing_reset, tm_waiting_array

MIN_REWARD_FOR_RESET = -120



class TrafficEnv(gym.Env):

    def __init__(self, tm=None, model_name=None, headless=False, cycles_per_action=1,
                 sleep_per_step=None, file_name="plot_data.txt"):

        self.tm = tm if model_name is None else load_model(model_name)
        self.last_step_info = []
        self.reward_file = open('../outdata/' + file_name, "w")

        if headless:
            self.tk = None
            self.main_tk = None
            self.bottom_tk = None
        else:
            self.root = Tk()
            self.root.title('Traffic Model: ' + self.tm.name + (
                ' (' + self.tm.description + ')' if 'description' in self.tm else ''))
            self.root.grid_columnconfigure(0, weight=1)
            self.root.grid_rowconfigure(0, weight=1)

            from traffic_base_tk import ScrolledFrame
            sf = ScrolledFrame(self.root)
            sf.grid(column=0, row=0, sticky='news')
            sf.grid_columnconfigure(0, weight=1)
            sf.grid_rowconfigure(0, weight=1)

            # Bind the arrow keys and scroll wheel
            sf.bind_arrow_keys(self.root)
            sf.bind_scroll_wheel(self.root)
            # Create a frame within the ScrolledFrame
            self.tk = sf.display_widget(Frame)

            # self.tk.resizable(True, True)
            # define main and console cell
            self.tk.grid_columnconfigure(0, weight=1)
            self.tk.grid_rowconfigure(0, weight=1)

            _main = LabelFrame(self.tk)
            _main.grid(row=0, column=0, sticky='news', padx=20, pady=10)
            self.main_tk = _main
            self.main_tk.grid_columnconfigure(0, weight=1)

            _bottom = LabelFrame(self.root, text='Dashboard', relief='flat')
            _bottom.grid(padx=10,
                         pady=10,
                         ipadx=10,
                         ipady=10, sticky='ews')
            self.bottom_tk = _bottom

            # create a scrollbar widget and set its command to the text widget
            # scrollbar = ttk.Scrollbar(self.tk, orient='vertical', command=self.main_tk.yview)
            # scrollbar.grid(row=0, column=1, sticky='ns')

            #  communicate back to the scrollbar
            # self.main_tk['yscrollcommand'] = scrollbar.set

        self.is_quit = False
        self.agent_thread = None
        self.cycles_per_action = cycles_per_action
        self.sleep_per_step = sleep_per_step

        self.last_action = -1
        self.observations = None
        self.reward_avg = 0
        self.reward_count = 0

        self.init_gym()

        if self.tk is not None:
            self.observations = []
            self.init_tk()

    def button_callback(self, crossing_index, gs_index):
        self.tm.crossings[crossing_index].green_situations_index = gs_index
        self.tm_refresh_tk()

    def init_tk(self):

        gs_counter = 0
        for crossing_index, crossing in enumerate(self.tm.crossings):
            crossing.tk_buttons = []
            crossing_frame = LabelFrame(self.main_tk, bg='white', borderwidth=2, relief='ridge')
            crossing_frame.pack(
                padx=10,
                pady=10,
                ipadx=10,
                ipady=10,
                fill='x'
            )
            tk_crossing_label = Label(crossing_frame, text=crossing.name, font=("Courier", 20), bg='white')
            tk_crossing_label.grid(row=0, column=0, padx=4, pady=4, sticky=N + W)
            tk_crossing_controls = LabelFrame(crossing_frame, bg='white')
            tk_crossing_controls.grid(row=1, column=1, rowspan=len(crossing.in_list), sticky='news', padx=5,
                                      pady=5)

            index = 0
            for gs_index, gs in enumerate(crossing.green_situations):
                # does not work _command = lambda: self.button_callback(crossing_index, gs_index)
                _command = partial(self.button_callback, crossing_index, gs_index)
                b = CrossingButton(tk_crossing_controls, text="\n".join(gs), command=_command)
                b.pack(padx=2, pady=2, )
                crossing.tk_buttons.append(b)
                index += 1
                gs_counter += 1

            z = 1
            street_set = set()
            for in_street in crossing.in_list:
                street_set.add(in_street)
                street = tm_get_street(self.tm, in_street)
                tk_street_parent = LabelFrame(crossing_frame, bg='white')
                street.tk_street = TkStreet(tk_street_parent, street, text=street.name, bg='white')
                street.tk_street.grid(padx=5, pady=5)
                tk_street_parent.grid(row=z, column=0, sticky='news', padx=10, pady=10)

                street.tk_outs = DotMap()
                lf_out = Frame(tk_street_parent, bg='white')
                lf_out.grid(row=0, column=street.length + 1, rowspan=2, )
                i = 0
                for out_street_name in self.tm.in_outs[street.name]:
                    tk_out_label = Label(lf_out, text=out_street_name, bg="white", fg="white")
                    tk_out_label.grid(row=i, column=0, padx=2, pady=2)
                    street.tk_outs[out_street_name] = tk_out_label
                    i += 1
                z += 1

        # only out streets
        crossing_frame = LabelFrame(self.main_tk, bg='white', text='Streets that are only out streets')
        crossing_frame.pack(
            padx=10,
            pady=10,
            ipadx=10,
            ipady=10,
            fill='x'
        )
        z = 0
        for street in self.tm.streets:
            if 'tk_street' not in street:
                tk_street_parent = LabelFrame(crossing_frame, bg='white')
                street.tk_street = TkStreet(tk_street_parent, street, text=street.name, bg='white')
                street.tk_street.grid(padx=5, pady=5)
                tk_street_parent.grid(row=z, column=0, sticky='news', padx=10,
                                      pady=10)
                z += 1

        self.tm.tk_step = ttk.Button(self.bottom_tk, text="Action !", command=self.fire_action)
        self.tm.tk_step.grid(row=0, column=0, sticky=W, padx=5, pady=5)

        self.tm.rt_counter = 0

        self.tm.tk_reward_avg = Label(self.bottom_tk, text='-score-', font=("Courier", 14), bg='white', width=10)
        self.tm.tk_reward_avg.grid(row=0, column=2, sticky='we', padx=5, pady=5)

        self.tk_console = HTMLLabel(self.bottom_tk, height=4)
        self.tk_console.grid(row=0, column=3, sticky='we', padx=5, pady=5)

        html_window = Toplevel(self.tk)
        html_window.title("Traffic Information")
        html_window.resizable(True, True)
        html_window.grid_columnconfigure(0, weight=1)
        html_window.grid_rowconfigure(1, weight=1)

        Label(html_window, text="Traffic Information").grid(column=0, row=0, sticky='we')

        self.tm.tk_info = HtmlFrame(html_window, horizontal_scrollbar="auto")
        self.tm.tk_info.grid(column=0, row=1, sticky='news')

        def on_window_exit():
            self.is_quit = True
            if self.agent_thread is not None:
                self.agent_thread.stop()
            self.tk.quit()

        self.root.protocol("WM_DELETE_WINDOW", on_window_exit)
        self.is_quit = False
        self.tm_refresh_tk()

    def tm_refresh_tk(self):

        if self.tk is None:
            return

        for street in self.tm.streets:
            for i, car in enumerate(street.slots):
                if 'tk_street' in street:
                    street.tk_street.tk_slots[i].set_car(car)
                if 'tk_outs' in street:
                    for _, _tk_label in street.tk_outs.items():
                        _tk_label.config(bg='red')

        self.tm.tk_reward_avg['text'] = str(round(self.reward_avg, 2))

        for crossing in self.tm.crossings:
            for b in crossing.tk_buttons:
                b.set_red()

            _curr_green_situation = None
            if crossing.green_situations_index != -1:
                print(crossing.name, 'green_situations_index', crossing.green_situations_index)
                _curr_green_situation = crossing.green_situations[crossing.green_situations_index]
                crossing.tk_buttons[crossing.green_situations_index].set_green()
            _green_lines = crossing_get_green_lines(crossing)
            for _green_line in _green_lines:
                _in_street = tm_get_street(self.tm, _green_line['in'])
                if _green_line.out in _in_street.tk_outs:
                    _in_street.tk_outs[_green_line.out].config(bg='green')

        if self.agent_thread is None:
            self.tm.tk_step['state'] = 'normal'
        else:
            self.tm.tk_step['state'] = 'disable'

        html = get_html(self)
        self.tm.tk_info.set_content(html)

        (action, observation, reward, done) = self.last_step_info[-1] if len(self.last_step_info) > 0 else (
            0, 0, 0, None)
        _indexes = tm_decode_action_code(self.tm, action)
        html = f'<div><b>Action</b>:{action} <b>Indexes</b>:{_indexes} <b>Observation</b>:{observation}<b>Reward</b>:{round(reward, 2)}<b>Done</b>:{done}</div>'

        self.tk_console.set_html(html)
        # self.tk_console.fit_height()

    #
    # *** *** ***
    # *** GYM ***
    # *** *** ***
    #

    def init_gym(self):
        print('init_gym')
        nr_of_buttons = 0
        for c in self.tm.crossings:
            nr_of_buttons += len(c.green_situations)

        street_in_dim = []
        for crossing in self.tm.crossings:
            for _ in crossing.lines:
                street_in_dim.append(20)

        _shape = tm_action_shape(self.tm)
        _dim = list(accumulate(_shape))[-1]
        self.action_space = gym.spaces.Discrete(_dim)
        self.observation_space = gym.spaces.MultiDiscrete(street_in_dim)
        self.seed()

    def seed(self, seed=None):
        _, seed = seeding.np_random(seed)
        return [seed]

    def fire_action(self):
        action_code = tm_get_action_code(self.tm)
        (observation, reward, done, _) = self.step(action_code)
        if done:
            self.reset()
        self.tm_refresh_tk()

    def step(self, action):
        print("ciao")
        if action == -1:
            pass
        else:
            tm_apply_action_code(self.tm, action)

        for _ in range(self.cycles_per_action):
            tm_next_step(self.tm)

        # reward...
        _reward = tm_car_crossing_rewards(self.tm)
        tm_reset_nirvana_rewards(self.tm)
        tm_car_crossing_reset(self.tm)
        self.reward_avg = (_reward + (self.reward_count * self.reward_avg)) / (self.reward_count + 1)
        self.reward_count += 1

        done = True if _reward < MIN_REWARD_FOR_RESET else False

        _state = tm_waiting_array(self.tm)
        _observation = np.array(_state)
        None if self.observations is None else self.observations.append(_observation)
        None if self.sleep_per_step is None else time.sleep(self.sleep_per_step / 1000)

        self.last_step_info.append((action, _observation, _reward, done))
        _indexes = tm_decode_action_code(self.tm, action)
        print(f'action: {action}; indexes: {_indexes}; observation: {_observation}; reward: {_reward}; done: {done}')

        self.reward_file.write(str(_reward)+'\n')
        self.reward_file.flush()

        return _observation, _reward, done, {}

    def reset(self):
        print('gym:reset')
        tm_init(self.tm)
        _state = tm_waiting_array(self.tm)
        return np.array(_state)

    def render(self, mode='human'):
        if self.tk is None:
            return
        if self.is_quit:
            return
        # TODO
        # https://stackoverflow.com/questions/64287940/update-tkinter-gui-from-a-separate-thread-running-a-command
        self.tk.after(1, self.tm_refresh_tk)


def load_model(model_name):
    import os
    _dirname = os.path.dirname(__file__)
    traffic_model_file = os.path.join(_dirname, "traffic_models", model_name, 'traffic_model.json')

    f = open(traffic_model_file)
    tm = DotMap(json.load(f))
    tm_init(tm)
    print('traffic_model_file', traffic_model_file)
    return tm
