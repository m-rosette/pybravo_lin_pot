import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import time
import sys
import nidaqmx
from nidaqmx.constants import TerminalConfiguration

# from daq_reader import NI_Device


class LivePlotter():
    def __init__(self, queue_len=20) -> None:
        # self._ni_device = NI_Device()
        self.RSE = TerminalConfiguration.RSE
        # self._ni_device.start()
        self.voltage_reading = 0
        # Animation Params
        self.init_time = time.time()
        self.xs = []
        self.ys = []
        self.queue_len = queue_len
        self.f, (self.ax1, self.ax2) = plt.subplots(1, 2)
        self._running = True

    def read_daq(self, physical_chan="Dev1/ai1:2", num_samples=1):
        """Sample the DAQ at a rate of 100Hz"""
        while self._running:
            with nidaqmx.Task() as task:
                # Add channel from daq and set the configuration reader
                task.ai_channels.add_ai_voltage_chan(physical_chan, terminal_config=self.RSE)
                
                # Read the voltage
                self.voltage_reading = task.read(number_of_samples_per_channel=num_samples)

    def animate_plot(self):
        
        # self.read_daq()
        # print(self.voltage_reading)

        def animate(i):
            with nidaqmx.Task() as task:
                # Add channel from daq and set the configuration reader
                task.ai_channels.add_ai_voltage_chan("Dev1/ai1:2", terminal_config=self.RSE)
                
                # Read the voltage
                self.voltage_reading = task.read(number_of_samples_per_channel=1)
                print(self.voltage_reading)

            if self.voltage_reading == 0:
                self.voltage_reading = [0]

            self.xs.append(time.time() - self.init_time)
            self.ys.append(self.voltage_reading[0][0])

            self.xs = self.xs[-self.queue_len:]
            self.ys = self.ys[-self.queue_len:]

            # Animating pitch over time
            self.ax1.cla()
            self.ax1.plot(self.xs, self.ys, color='green')
            self.ax1.set_title('Measured Pitch')
            self.ax1.set_ylabel('Pitch (deg)')
            self.ax1.set_xlabel('Time (s)')
            # self.ax1.tight_layout()

            # Animating pitch model
            theta = np.radians(90 - self.voltage_reading[0][0]) * 5
            c, s = np.cos(theta), np.sin(theta)
            R = np.array(((c, -s), (s, c)))
            x = [0]
            y = [0]
            point = np.array([1, 0])
            point_rot = R * point
            
            x.append(point_rot[0][0])
            y.append(point_rot[1][0])
            
            self.ax2.cla()
            self.ax2.set(xlim=(0, 1), ylim=(0, 1))
            self.ax2.plot(x, y, color='blue')
            self.ax2.set_title('Pitching Frame')
            self.ax2.set_ylabel('z')
            self.ax2.set_xlabel('x')
            self.ax2.legend([f"Pitch (deg): {round(self.voltage_reading[0][0] * 5, 3)}"])
        
        ani = FuncAnimation(self.f, animate, interval=10)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    lp = LivePlotter()
    
    while True:
        try:
            lp.animate_plot()
            time.sleep(0.1)
        except KeyboardInterrupt:
            sys.exit()