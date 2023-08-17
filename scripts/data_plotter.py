import matplotlib.pyplot as plt
import socket
import struct
import sys
import time
import numpy as np


class LivePlot:
    def __init__(self, queue_len=1) -> None:
        self.xs = []
        self.ys = []
        self.queue_len = queue_len
        self.init_time = time.time()
        self.f, (self.ax1, self.ax2) = plt.subplots(1, 2)

        self.ax1.set_title('Measured Pitch')
        self.ax1.set_ylabel('Pitch (deg)')
        self.ax1.set_xlabel('Time (s)')

        self.ax2.set_title('Pitching Frame')
        self.ax2.set_ylabel('z')
        self.ax2.set_xlabel('x')

        # plt.show()

    def plotter(self, data):
        self.xs.append(time.time() - self.init_time)
        self.ys.append(data)

        self.xs = self.xs[-self.queue_len:]
        self.ys = self.ys[-self.queue_len:]

        # Animating pitch over time
        # self.ax1.cla()
        self.ax1.plot(self.xs, self.ys, color='green')
        # self.ax1.draw()
        # self.ax1.tight_layout()

        # Animating pitch model
        theta = np.radians(90 - data)
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, -s), (s, c)))
        x = [0]
        y = [0]
        point = np.array([1, 0])
        point_rot = R * point
        
        x.append(point_rot[0][0])
        y.append(point_rot[1][0])
        
        # self.ax2.cla()
        self.ax2.set(xlim=(0, 1), ylim=(0, 1))
        self.ax2.plot(x, y, color='blue')
        self.ax2.legend([f"Pitch (deg): {round(data, 3)}"])
        # plt.show()


if __name__ == "__main__":
    volt_min = -4.262
    volt_max = -1.48
    extension_min = 0 # inches
    extension_max = 11.25 # inches
    sensor_mount_height = 27.75 # inches

    xs = []
    ys = []
    queue_len = 50
    init_time = time.time()
    f, (ax1, ax2) = plt.subplots(1, 2)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((socket.gethostname(), 6969))

    recv_size = sys.getsizeof(struct.pack('d', float(0)))

    while True:
        raw_bytes = sock.recv(recv_size)
        try:
            data = struct.unpack('d', raw_bytes)[0]
        except:
            continue

        if data == 0:
            continue
        
        # Map voltage to linear extension
        linear_data = np.interp(data, [volt_min, volt_max], [extension_min, extension_max])

        # Map linear extension to pitch angle
        pitch = np.rad2deg(linear_data / sensor_mount_height)

        # Set x and y values
        xs.append(time.time() - init_time)  # Appending live plot timer
        ys.append(pitch)                    # Appending pitch

        # Implement window size
        xs = xs[-queue_len:]
        ys = ys[-queue_len:]

        # Animating pitch over time
        ax1.cla()
        ax1.plot(xs, ys, color='green')
        ax1.set_title('Measured Pitch')
        ax1.set_ylabel('Pitch (deg)')
        ax1.set_xlabel('Time (s)')
        # ax1.set(ylim=(0, 20))

        # Animating pitch frame
        c, s = np.cos(pitch), np.sin(pitch)
        R = np.array(((c, -s), (s, c)))
        x = [0]
        y = [0]
        point = np.array([1, 0])
        point_rot = R * point
        
        x.append(point_rot[0][0])
        y.append(point_rot[1][0])
        
        ax2.cla()
        ax2.set(xlim=(0, 1), ylim=(0, 1))
        ax2.plot(x, y, color='blue')
        ax2.legend([f"Pitch (deg): {round(pitch, 3)}"])
        ax2.set_title('Pitching Frame')
        ax2.set_ylabel('z')
        ax2.set_xlabel('x')

        plt.pause(0.01)