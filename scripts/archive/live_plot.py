import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np
import time
from itertools import count
import sys
import threading
import atexit

from daq_reader import NI_Device


class LivePlotter():
    def __init__(self, queue_len=20) -> None:
        # Animation Params
        self.init_time = time.time()
        self.xs = []
        self.ys = []
        self.queue_len = queue_len
        self.f, (self.ax1, self.ax2) = plt.subplots(1, 2)
        plt.show()

        self._ni_device = NI_Device()

        self._running = False

        # Run the controller in it's own thread
        self.plot_t = threading.Thread(target=self._run_plotter)
        self.plot_t.daemon = True

        atexit.register(self.stop)

    def start(self) -> None:
        # Start the polling thread
        self._running = True
        self.plot_t.start()
        self._ni_device.start()

    def stop(self) -> None:
        # Stop the poll thread loop
        self._running = False
        self.plot_t.join()
        self._ni_device.stop()

    def animate_plot(self):
        if self._ni_device.voltage_reading == 0:
            self._ni_device.voltage_reading = [0]

        def animate(i):
            self.xs.append(time.time() - self.init_time)
            self.ys.append(self._ni_device.voltage_reading[0])

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
            theta = np.radians(90 - self._ni_device.voltage_reading[0]) * 5
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
            self.ax2.legend([f"Pitch (deg): {round(self._ni_device.voltage_reading[0] * 5, 3)}"])
        
        ani = FuncAnimation(self.f, animate, interval=10)
        # plt.tight_layout()
        plt.show()

    def _run_plotter(self):
        while self._running:
            self.animate_plot()
            # self.f.show()


if __name__ == "__main__":
    lp = LivePlotter()

    lp.start()

    # To read joint positions
    while True:
        try:
            # print(f"The current joint positions are: {handler.joint_positions}")
            time.sleep(0.01)
        except KeyboardInterrupt:
            lp.stop()
            sys.exit()