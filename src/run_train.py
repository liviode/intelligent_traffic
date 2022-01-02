import os
import sys
from threading import Thread

from tensorflow.keras.optimizers import Adam

from TrafficEnv import TrafficEnv
from traffic_rl_model import build_model, build_agent

model_dir = os.path.join(os.path.dirname(__file__), "traffic_models")


class TrainingAgentThread(Thread):

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
        dqn.fit(self.env, nb_steps=600, visualize=False, verbose=1)

        save_name = os.path.join(model_dir, env.tm.name, 'out', 'model_dqn_weights.h5f')

        dqn.save_weights(save_name, overwrite=True)
        print(f"Training done, model saved in {os.path.join(env.tm.name, 'out')}")

        # scores = dqn.test(self.env, nb_episodes=50, visualize=False)
        # print(np.mean(scores.history['episode_reward']))
        #
        # _ = dqn.test(self.env, nb_episodes=15, visualize=True)

    def stop(self):
        self.is_stopped = True


if __name__ == '__main__':
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    env = TrafficEnv(model_name=model_name, headless=True, file_name=model_name+"_train.txt")
    agent_thread = TrainingAgentThread(env)
    env.agent_thread = agent_thread
    agent_thread.start()
    print('TrainingAgentThread started')
    env.tk.mainloop()
