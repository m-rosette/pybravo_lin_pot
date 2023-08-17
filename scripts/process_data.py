import numpy as np
import kinpy as kp
from scipy.spatial.transform import Rotation as R
import matplotlib.pyplot as plt


class ProcessData():
    def __init__(self, urdf_fp='urdf/bravo7.urdf') -> None:
        self.volt_min = -4.262 # volts
        self.volt_max = -1.48 # volts
        self.extension_min = 0 # inches
        self.extension_max = 11.25 # inches
        self.sensor_mount_height = 27.75 # inches

        # Load predicted pitch values
        self.pred_pitch = self.read_csv()

        # Get the serial chain using the Bravo 7 URDF
        self.serial_chain = kp.build_serial_chain_from_urdf(open(urdf_fp).read(), "ee_link")

    def parse_data_file(self, filename, remove_header=True, num_initial_line_skip=0):
        data = []
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
                data.append(line_data)
        return data
    
    def extract_elements(self, data, timestamp_file_column=0, num_joints=7, lin_pot_file_column=8, norm_time=True, clamp_joint_4=True):
        # Convert list to np array
        data_arr = np.array(data)

        # Extract each variable
        timestamp = data_arr[:, timestamp_file_column]
        joint_positions = data_arr[:, timestamp_file_column+1:num_joints+1]
        voltage_reading = data_arr[:, lin_pot_file_column]

        # Normalize time data
        if norm_time:
            timestamp = timestamp - timestamp[0]

        if clamp_joint_4:
            joint_positions[:, 3] = 0

        return timestamp, joint_positions, voltage_reading

    def volt_to_linear_map(self, voltage_reading, lin_min=0.0, lin_max=11.25, volt_min=-4.262, volt_max=-1.48):
        """Maps voltage readings to a specified range"""
        return np.interp(voltage_reading, [volt_min, volt_max], [lin_min, lin_max])
    
    def pitch_extrapolation(self, mapped_reading, spring_mount_height=27.75, rad2deg=False):
        """Converting the linear potentiometer readings to pitch angle"""
        # Using arc length
        pitch = mapped_reading / spring_mount_height

        if rad2deg:
            pitch = np.degrees(pitch)
        
        return pitch
    
    def read_csv(self, filename='arm_camera_hardware_pitch_data.csv'):
        data = []
        with open(f'data/{filename}','r') as file:
            for _, line in enumerate(file):
                line_data = line.strip()
                data.append(float(line_data))
        return data
    
    def del_initial(self, time, pitch, joint_pos, num_to_del=3):
        pitch_trim = np.delete(pitch, range(num_to_del), 0)
        time_trim = np.delete(time, range(num_to_del), 0)
        joint_pos_trim = np.delete(joint_pos, range(num_to_del), 0)
        return time_trim, pitch_trim, joint_pos_trim
    
    def truncate(self, time, pitch, joint_pos, trunc_time=15, rtol=0.005):
        trunc_idx = np.where(np.isclose(trunc_time, time, rtol=rtol) == True)[0][0]
        pitch_trunc = pitch[:trunc_idx]
        time_trunc = time[:trunc_idx]
        joint_pos_trunc = joint_pos[:trunc_idx]
        return trunc_idx, time_trunc, pitch_trunc, joint_pos_trunc
    
    def exp_stats(self, time, pitch1, pitch2, pitch3):
        pitch_std = []
        pitch_avg = []
        timestamp_trim = []
        for i in range(min(len(pitch1), len(pitch2), len(pitch3))):
            pitch_std.append(np.std([pitch1[i], pitch2[i], pitch3[i]]))
            pitch_avg.append(np.average([pitch1[i], pitch2[i], pitch3[i]]))
            timestamp_trim.append(time[i])
        return pitch_avg, pitch_std, timestamp_trim

    def fk_from_urdf(self, joint_positions):
        # Get the end-effector poses in the base frame as a numpy array
        xe_rot = []
        xe = []
        for i in range(len(joint_positions)):
            xe_transform = self.serial_chain.forward_kinematics(joint_positions[i][::-1])
            x_to_array = [*xe_transform.pos]
            xe.append(x_to_array)
        return np.array(xe)

    def plot_data(self, x, y, title='', ylabel='', xlabel='', legend=[]):
        plt.plot(x, y)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend(legend, loc='right')
        plt.grid(color='black', linestyle='-', linewidth=0.1)
        # plt.show()

    def plot_single_exp(self, config_num, filename="logs/hinsdale_out_of_plane_config_2.log", del_init=True, initial_trim=3):
        pass

    def plot_all_exp(self, config_num, file_text_name='logs/hinsdale_config', redo_1=False, redo_2=False, redo_3=False, truncate=True, del_init=True, initial_trim=3, waves=False, plot=True):
        if redo_1:
            data1 = self.parse_data_file(f'{file_text_name}_{config_num}_redo.log')
        else:
            data1 = self.parse_data_file(f'{file_text_name}_{config_num}.log')
        
        if redo_2:
            data2 = self.parse_data_file(f'{file_text_name}_{config_num}_2_redo.log')
        else:
            data2 = self.parse_data_file(f'{file_text_name}_{config_num}_2.log')

        if redo_3:          
            data3 = self.parse_data_file(f'{file_text_name}_{config_num}_3_redo.log')
        else:
            data3 = self.parse_data_file(f'{file_text_name}_{config_num}_3.log')

        timestamp1, joint_positions1, volt_reading1 = self.extract_elements(data1)
        timestamp2, joint_positions2, volt_reading2 = self.extract_elements(data2)
        timestamp3, joint_positions3, volt_reading3 = self.extract_elements(data3)    

        mapped_reading1 = self.volt_to_linear_map(volt_reading1)    
        mapped_reading2 = self.volt_to_linear_map(volt_reading2)
        mapped_reading3 = self.volt_to_linear_map(volt_reading3)

        pitch1 = self.pitch_extrapolation(mapped_reading1, rad2deg=True)
        pitch2 = self.pitch_extrapolation(mapped_reading2, rad2deg=True)
        pitch3 = self.pitch_extrapolation(mapped_reading3, rad2deg=True)

        xe = self.fk_from_urdf(joint_positions1)
        xe = np.delete(xe, range(initial_trim), 0)

        if waves:
            data_waves = self.parse_data_file(f'logs/video_config_{config_num}.log')
            time_waves, joint_pos_waves, volt_waves = self.extract_elements(data_waves)
            map_reading_waves = self.volt_to_linear_map(volt_waves)
            pitch_waves = self.pitch_extrapolation(map_reading_waves, rad2deg=True)

            if del_init:
                time_waves, pitch_waves, joint_pos_waves = self.del_initial(time_waves, pitch_waves, joint_pos_waves, num_to_del=initial_trim)

            if truncate:
                _, time_waves, pitch_waves, joint_pos_waves = self.truncate(time_waves, pitch_waves, joint_pos_waves)

        if del_init:
            timestamp1, pitch1, joint_positions1 = self.del_initial(timestamp1, pitch1, joint_positions1, num_to_del=initial_trim)
            timestamp2, pitch2, joint_positions2 = self.del_initial(timestamp2, pitch2, joint_positions2, num_to_del=initial_trim)
            timestamp3, pitch3, joint_positions3 = self.del_initial(timestamp3, pitch3, joint_positions3, num_to_del=initial_trim)

        if config_num == 2 or config_num == 4 or config_num == 6 or config_num == 7 or config_num == 9:
            range_val = 554
            if config_num == 2:
                init_val = 10.0573
            elif config_num == 4:
                init_val = 9.85
            elif config_num == 6:
                init_val = 10.549
            elif config_num == 7:
                init_val = 10.423
                range_val = 553
            elif config_num == 9:
                init_val = 10.423
                range_val = 477

            pitch1_new = pitch1
            for i in range(range_val):
                pitch1_new = np.insert(pitch1_new, 0, init_val)
        else:
            pitch1_new = pitch1

        if truncate:
            _, timestamp1, pitch1, joint_positions1 = self.truncate(timestamp1, pitch1, joint_positions1)
            trunc_idx_2, timestamp2, pitch2, joint_positions2 = self.truncate(timestamp2, pitch2, joint_positions2)
            _, timestamp3, pitch3, joint_positions3 = self.truncate(timestamp3, pitch3, joint_positions3)

            pitch1_new = pitch1_new[:trunc_idx_2]

        pitch_avg, pitch_std, timestamp_trim = self.exp_stats(timestamp2, pitch1_new, pitch2, pitch3)

        if plot:
            # Plot data
            plt.figure() # initialize figure
            plt.suptitle(f"Configuration #{config_num}", fontsize=14)

            # First subplot
            if waves:
                plt.subplot(141)
            else:
                plt.subplot(131) 
            plt.plot(timestamp1, joint_positions1[:, 2], color='purple')
            plt.plot(timestamp1, joint_positions1[:, 4], color='red')
            plt.plot(timestamp1, joint_positions1[:, 5], color='black')
            plt.xlabel('Time (s)')
            plt.ylabel('Position (rad)')
            plt.title('Bravo Trajectory')
            plt.legend(['joint 1', 'joint 2', 'joint 3'])
            plt.grid(color='black', linestyle='-', linewidth=0.1)

            # Second subplot
            if waves:
                plt.subplot(142) 
            else:
                plt.subplot(132)
            plt.plot(xe[:, 0], xe[:, 2])
            plt.xlabel('x (m)')
            plt.ylabel('y (m)')
            plt.title('End-Effector Position')
            plt.legend(['bravo traj'])
            plt.grid(color='black', linestyle='-', linewidth=0.1)

            # plt.plot(timestamp1, pitch1)
            # plt.plot(timestamp2, pitch2)
            # plt.plot(timestamp3, pitch3)
            # plt.xlabel('Time (s)')
            # plt.ylabel('Pitch (deg)')
            # plt.title('Frame Pitch over Bravo Trajectory')
            # plt.legend(['Exp. 1', 'Exp. 2', 'Exp. 3'])
            # plt.grid(color='black', linestyle='-', linewidth=0.1)

            # Third subplot
            if waves:
                plt.subplot(143) 
            else:
                plt.subplot(133)
            plt.plot(timestamp_trim, pitch_avg, color='black')
            plt.fill_between(timestamp_trim, np.subtract(pitch_avg, pitch_std), np.add(pitch_avg, pitch_std), color='black', alpha=0.4)
            plt.plot(timestamp_trim, [np.rad2deg(self.pred_pitch[config_num])] * len(timestamp_trim), '--')
            plt.xlabel('Time (s)')
            plt.ylabel('Pitch (deg)')
            plt.title('Average Frame Pitch')
            plt.legend(['Avg', 'Std', f'Pred: {round(np.rad2deg(self.pred_pitch[config_num]), 1)}'])
            plt.grid(color='black', linestyle='-', linewidth=0.1)

            if waves:
                plt.subplot(144) 
                plt.plot(timestamp_trim, pitch_avg, color='black')
                plt.fill_between(timestamp_trim, np.subtract(pitch_avg, pitch_std), np.add(pitch_avg, pitch_std), color='black', alpha=0.4)
                plt.plot(timestamp_trim, [np.rad2deg(self.pred_pitch[config_num])] * len(timestamp_trim), '--')
                plt.plot(time_waves, pitch_waves)
                plt.xlabel('Time (s)')
                plt.ylabel('Pitch (deg)')
                plt.title('Pitch Comparision - Waves')
                plt.legend(['Avg', 'Std', f'Pred: {round(np.rad2deg(self.pred_pitch[config_num]), 1)}'], 'Waves')
                plt.grid(color='black', linestyle='-', linewidth=0.1)

            plt.show()


if __name__ == '__main__':    
    pdata = ProcessData()
    
    # pdata.plot_all_exp(config_num=1, redo_1=True, redo_2=True, redo_3=True, waves=True)
    # pdata.plot_all_exp(config_num=2, initial_trim=10)
    # pdata.plot_all_exp(config_num=3, redo_1=True, redo_2=True, redo_3=True, waves=True)
    # pdata.plot_all_exp(config_num=4, initial_trim=10)
    # pdata.plot_all_exp(config_num=6, initial_trim=10, waves=True)
    # pdata.plot_all_exp(config_num=7, initial_trim=10)
    # pdata.plot_all_exp(config_num=9, redo_1=True, redo_2=False, redo_3=False)
    pdata.plot_all_exp(config_num=10, initial_trim=10)
    