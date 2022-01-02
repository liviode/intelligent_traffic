import sys

from TrafficEnv import TrafficEnv

if __name__ == '__main__':
    print('sys.argv', sys.argv)
    model_name = sys.argv[1] if len(sys.argv) > 1 else 'model_01'
    env = TrafficEnv(model_name=model_name, cycles_per_action=1, file_name=model_name+"_manually.txt")
    env.tk.mainloop()
    print('run_manually started')
