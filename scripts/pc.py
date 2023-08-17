import time
import atexit
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import threading
import socket
import struct

from logger import FileLogger, init_logger
from daq_reader import NI_Device
from bravo_handler import BravoHandler
from config_loader import ArmConfig
# from live_plot2 import LivePlotter

# from multiprocessing import Process,Queue,Pipe


class PitchCompliance():
    def __init__(self, desired_config_num):
        self._config_loader = ArmConfig()
        self._config_loader._get_config(desired_config_num)
        self.desired_config = self._config_loader.desired_config

        self._bravo = BravoHandler()
        self._ni_device = NI_Device()

        self._running = False
        # self.logger = init_logger("PitchCompliance")
        # self._file_logger = FileLogger('testing_eod.log')

        # Run the controller in it's own thread
        # self.sensor_t = threading.Thread(target=self._run_sensors)
        # self.sensor_t.daemon = True

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        self._running = True

        self._bravo.start()
        self._ni_device.start()
        # self.sensor_t.start()

        # self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable arm control and sensor readings."""
        self._running = False

        self._bravo.stop()
        self._ni_device.stop()
        # self.sensor_t.join()

        # self.logger.warning("Arm control has been disabled.")

    # def _run_sensors(self):
    #     """Send commands to the arm"""
    #     while self._running:          
    #         # # Log incomming data
    #         # self._file_logger(
    #         #     time.time(),
    #         #     self._bravo.joint_positions,
    #         #     self._ni_device.voltage_reading,
    #         # )
            
    #         print('Delay before arm controller...')
    #         time.sleep(10)
            
    #         print("Running controller:")
    #         self._bravo._run_controller(self.desired_config)
    #         time.sleep(1)


if __name__ == "__main__":    
    config_num = int(input("Enter the desired configuration #: "))
    pitch_compliance = PitchCompliance(config_num)

    # logger = init_logger("PitchCompliance")
    # _file_logger = FileLogger(f'hinsdale_out_of_plane_config_{config_num}.log')
    # _file_logger = FileLogger(f'real_video_config_{config_num}.log')
    # _file_logger = FileLogger('testing.log')

    init_time = time.time()
    running_arm = True

    volt_min = -4.262
    volt_max = -1.48
    extension_min = 0 # inches
    extension_max = 11.25 # inches
    sensor_mount_height = 27.75 # inches

    # Enable the controller
    pitch_compliance.enable()

    # Let the controller do its thing
    while True:
        try:
            _file_logger(
                time.time(),
                pitch_compliance._bravo.joint_positions,
                pitch_compliance._ni_device.voltage_reading,
            )

            # Map voltage to linear extension
            linear_data = np.interp(pitch_compliance._ni_device.voltage_reading, [volt_min, volt_max], [extension_min, extension_max])

            # Map linear extension to pitch angle
            pitch = np.rad2deg(linear_data / sensor_mount_height)
            print(f"Pitch: {np.round(pitch, 3)}")

            if time.time() - init_time > 10 and running_arm:
                pitch_compliance._bravo._run_controller(pitch_compliance.desired_config)
                running_arm = False # Reset bool
                time.sleep(0.1)

            time.sleep(0.05)

        except KeyboardInterrupt:
            pitch_compliance.disable()
            exit()

