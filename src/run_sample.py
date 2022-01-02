import sys
import time
from threading import Thread

from TrafficEnv import TrafficEnv


class SampleAgentThread(Thread):

    def __init__(self, env):
        super().__init__()
        self.env = env
        self.counter = 0
        self.is_stopped = False

    def run(self):
        for i_episode in range(10):
            observation = self.env.reset()
            for t in range(60):
                if self.is_stopped:
                    return
                self.env.render()

                action = env.action_space.sample()
                observation, reward, done, info = self.env.step(action)
                time.sleep(0)
                if done:
                    print("Episode finished after {} timesteps".format(t + 1))
                    break

    def stop(self):
        self.is_stopped = True


if __name__ == '__main__':
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    env = TrafficEnv(model_name=model_name, cycles_per_action=5, sleep_per_step=200, file_name=model_name+"_sample.txt", headless=True)
    agent_thread = SampleAgentThread(env)
    env.agent_thread = agent_thread
    agent_thread.start()
    print('run_sample_agent STARTED')
    env.tk.mainloop()
    print('THE END')
