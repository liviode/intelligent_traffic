import sys
import time
from threading import Thread
from traffic_base import tm_max_encoded_index

from TrafficEnv import TrafficEnv


class RoundRobinAgentThread(Thread):

    def __init__(self, env):
        super().__init__()
        self.env = env
        self.counter = 0
        self.is_stopped = False

    def run(self):
        max = tm_max_encoded_index(self.env.tm)
        for i_episode in range(10):
            observation = self.env.reset()
            for t in range(60):
                if self.is_stopped:
                    return
                self.env.render()

                action = t % max
                observation, reward, done, info = self.env.step(action)
                # time.sleep(0)
                if done:
                    print("Episode finished after {} timesteps".format(t + 1))
                    break

    def stop(self):
        self.is_stopped = True


if __name__ == '__main__':
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    headless = True if len(sys.argv) > 2 and sys.argv[2] == 'headless' else False
    env = TrafficEnv(model_name=model_name, cycles_per_action=5, sleep_per_step=200,
                     file_name=model_name + "_round_robin.txt", headless=headless)
    agent_thread = RoundRobinAgentThread(env)
    env.agent_thread = agent_thread
    agent_thread.start()
    print('run_round_robin_agent STARTED')
    env.tk.mainloop()
    print('THE END')
