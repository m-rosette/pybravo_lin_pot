import time
import atexit
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import socket
import struct

from logger import FileLogger, init_logger
from daq_reader import NI_Device
from bravo_handler import BravoHandler
from config_loader import ArmConfig


class PitchCompliance():
    def __init__(self, desired_config_num=0):
        self._config_loader = ArmConfig()
        self._config_loader._get_config(desired_config_num)

        # self._bravo = BravoHandler(self._config_loader.desired_config)
        self._ni_device = NI_Device()

        self._running = False
        self.logger = init_logger("PitchCompliance")
        self._file_logger = FileLogger("testing.log")

        # Animation Params
        self.init_time = time.time()
        self.xs = []
        self.ys = []
        self.queue_len = 50
        self.f, (self.ax1, self.ax2) = plt.subplots(1, 2)

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        self._running = True

        # self._bravo.start()
        self._ni_device.start()

        # Delay for sensors to activate
        self._run_controller()
        
        self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable arm control and sensor readings."""
        self._running = False

        # self._bravo.stop()
        self._ni_device.stop()

        self.logger.warning("Arm control has been disabled.")

    def _run_controller(self):
        """Send commands to the arm"""
        while self._running:
            
            # Log incomming data
            self._file_logger(
                time.time(),
                self._bravo.joint_positions,
                self._ni_device.voltage_reading,
            )

            # TODO: Need to start the animation earlier on since I am getting some latency between when it starts and how the commands are sent to the arm
            # TODO: Put all of the animating content into its own class
            # TODO: Need to remove the *5 scaling on the voltage input
            # TODO: Convert the incoming voltage readings to pitch
            # Animating the output data
            # def animate(i):

            #     # Log incomming data
            #     self._file_logger(
            #         time.time(),
            #         self._bravo.joint_positions,
            #         self._ni_device.voltage_reading,
            #     )

            #     self.xs.append(time.time() - self.init_time)
            #     self.ys.append(self._ni_device.voltage_reading)

            #     self.xs = self.xs[-self.queue_len:]
            #     self.ys = self.ys[-self.queue_len:]

            #     # Animating pitch over time
            #     self.ax1.cla()
            #     self.ax1.plot(self.xs, self.ys, color='green')
            #     self.ax1.set_title('Measured Pitch')
            #     self.ax1.set_ylabel('Pitch (deg)')
            #     self.ax1.set_xlabel('Time (s)')
            #     # self.ax1.tight_layout()

            #     # Animating pitch model
            #     theta = np.radians(90 - self._ni_device.voltage_reading[0]) * 5
            #     c, s = np.cos(theta), np.sin(theta)
            #     R = np.array(((c, -s), (s, c)))
            #     x = [0]
            #     y = [0]
            #     point = np.array([1, 0])
            #     point_rot = R * point
                
            #     x.append(point_rot[0][0])
            #     y.append(point_rot[1][0])
                
            #     self.ax2.cla()
            #     self.ax2.set(xlim=(0, 1), ylim=(0, 1))
            #     self.ax2.plot(x, y, color='blue')
            #     self.ax2.set_title('Pitching Frame')
            #     self.ax2.set_ylabel('z')
            #     self.ax2.set_xlabel('x')
            #     self.ax2.legend([f"Pitch (deg): {round(self._ni_device.voltage_reading[0] * 5, 3)}"])
            
            # ani = FuncAnimation(plt.gcf(), animate, interval=10)
            # plt.tight_layout()
            # plt.show()
            # time.sleep(10)

            # Send command to arm
            # print('here')
            # self._bravo._run_controller()


if __name__ == "__main__":
    config_num = int(input("Enter the desired configuration #: "))
    pitch_compliance = PitchCompliance(config_num)

    # Enable the controller
    pitch_compliance.enable()

    # Let the controller do its thing
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            pitch_compliance.disable()
            exit()

