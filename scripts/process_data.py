import numpy as np
import matplotlib.pyplot as plt


class ProcessData():
    def __init__(self) -> None:
        self.data = []
        self.data_arr = None

        self.timestamp = None
        self.joint_positions = None
        self.voltage_reading = None

    def parse_data_file(self, filename, remove_header=True, num_initial_line_skip=0):
        with open(filename,'r') as file:
            for i, line in enumerate(file):

                # Remove header
                if remove_header and i == 0:
                    continue
                
                # Skip any additional lines
                if i <= num_initial_line_skip:
                    continue

                line_data = line.strip()
                line_data = list(map(float, line.replace('[', '').replace(']', '').split(',')))
                self.data.append(line_data)
    
    def extract_elements(self, timestamp_file_column=0, num_joints=7, lin_pot_file_column=8, norm_time=True, clamp_joint_4=True):
        # Convert list to np array
        self.data_arr = np.array(self.data)

        # Extract each variable
        self.timestamp = self.data_arr[:, timestamp_file_column]
        self.joint_positions = self.data_arr[:, timestamp_file_column+1:num_joints+1]
        self.voltage_reading = self.data_arr[:, lin_pot_file_column]

        # Normalize time data
        if norm_time:
            self.timestamp = self.timestamp - self.timestamp[0]

        if clamp_joint_4:
            self.joint_positions[:, 3] = 0

    def plot_data(self, x, y, title='', ylabel='', xlabel='', legend=[]):
        plt.plot(x, y)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend(legend)

        plt.show()


if __name__ == '__main__':    
    pdata = ProcessData()

    filename = "logs/2023-07-29-18-13-04.log"
    pdata.parse_data_file(filename, num_initial_line_skip=10)
    pdata.extract_elements()

    pdata.plot_data(pdata.timestamp, pdata.voltage_reading, 
                    title='Voltage over Bravo Trajectory', 
                    ylabel='Voltage (V)', 
                    xlabel='Time (s)')
    
    pdata.plot_data(pdata.timestamp, pdata.joint_positions, 
                    title='Bravo Trajectory', 
                    ylabel='Position (rad)', 
                    xlabel='Time (s)',
                    legend=['joint 1', 'joint 2', 'joint 3', 'joint 4', 'joint 5', 'joint 6', 'joint 7'])

    

