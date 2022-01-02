import os
import sys
from threading import Thread

from tensorflow.keras.optimizers import Adam

from TrafficEnv import TrafficEnv
from traffic_rl_model import build_model, build_agent

model_dir = os.path.join(os.path.dirname(__file__), "traffic_models")


class TrainingAgentThread(Thread):

    def __init__(self, env, mode='train'):
        super().__init__()
        self.env = env
        self.mode = mode

    def run(self):
        states = self.env.observation_space.shape[0]

        actions = self.env.action_space.n

        model = build_model(states, actions)
        model.summary()

        dqn = build_agent(model, actions)
        dqn.compile(Adam(lr=1e-3), metrics=['mae'])
        name = env.tm.name

        save_name = os.path.join(model_dir, name, 'out', 'model_dqn_weights.h5f')

        if self.mode == 'train':
            dqn.fit(self.env, nb_steps=5000, visualize=True, verbose=1)
            dqn.save_weights(save_name, overwrite=True)
            print(f'Training done for {name}')
        else:
            dqn.load_weights(save_name)
            _ = dqn.test(self.env, nb_episodes=15, visualize=True)
            print(f'Test done for {name}')




if __name__ == '__main__':
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    mode = sys.argv[2] if len(sys.argv) > 2 else 'test'
    env = TrafficEnv(model_name=model_name, headless=False, sleep_per_step=200, file_name=model_name+"_model.txt")
    agent_thread = TrainingAgentThread(env, mode=mode)
    env.agent_thread = agent_thread
    agent_thread.start()
    print(f'TrainingAgentThread started. model_name: {model_name} mode: {mode}')
    env.tk.mainloop()
