import mat73
import numpy as np
import sys

sys.path.append("..")


class ArmConfig:
    def __init__(self):
        self.initial_config = np.array([0, 1.57, 2.64, 0, 0.6, 3.04, 3.14])

    def load_matfile_data(self, data_file="C:/Users/marcu/OneDrive/Documents/GitHub/pybravo_linear_potentiometer/scripts/data/hardware_configs.mat", flip_joint_order=True, add_home=True):
        # Load file from file path
        file = mat73.loadmat(data_file)

        # Extract the configuration data
        configs = file['configs']

        # Flip order of joint angles?
        if flip_joint_order:
            configs = np.fliplr(configs)

        # Add home arm configuration
        if add_home:
            configs = np.insert(configs, 0, self.initial_config, 0)
        
        return configs
    

if __name__ == '__main__':
    arm_configs = ArmConfig()
    config_data = arm_configs.load_matfile_data()
    print(config_data)