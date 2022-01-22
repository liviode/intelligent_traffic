import os
import sys
from threading import Thread

from tensorflow.keras.optimizers import Adam

from TrafficEnv import TrafficEnv
from traffic_rl_model import build_model, build_agent

model_dir = os.path.join(os.path.dirname(__file__), "traffic_models")


class TestAgentThread(Thread):

    def __init__(self, env):
        super().__init__()
        self.env = env

    def run(self):
        states = self.env.observation_space.shape[0]

        actions = self.env.action_space.n

        model = build_model(states, actions)
        model.summary()

        dqn = build_agent(model, actions)
        dqn.compile(Adam(lr=1e-3), metrics=['mae'])
        name = env.tm.name

        save_name = os.path.join(model_dir, name, 'out', 'model_dqn_weights.h5f')

        dqn.load_weights(save_name)
        _ = dqn.test(self.env, nb_episodes=15, visualize=True)
        print(f'Test done for {name}')


if __name__ == '__main__':
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    headless = True if len(sys.argv) > 2 and sys.argv[2] == 'headless' else False
    sleep_per_step = 0 if headless else 1000
    env = TrafficEnv(model_name=model_name,
                     headless=headless,
                     sleep_per_step=sleep_per_step,
                     file_name=model_name + "_model.txt")
    agent_thread = TestAgentThread(env)
    env.agent_thread = agent_thread
    agent_thread.start()
    print(f'TestAgentThread started. model_name: {model_name}')
    env.tk.mainloop()
