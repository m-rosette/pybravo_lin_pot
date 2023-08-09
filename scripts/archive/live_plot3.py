import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import style
import numpy as np
import time
from itertools import count
import sys
from process_data import ProcessData


if __name__ == "__main__":
    pdata = ProcessData()
    style.use('fivethirtyeight')

    fig = plt.figure()
    ax1 = fig.add_subplot(1, 1, 1)

    init_time = time.time()

    def animate(i):
        # graph_data = open('logs/2023-07-31-09-04-29.log', 'r').read()
        pdata.parse_data_file('logs/testing.log')
        pdata.extract_elements()
        
        ax1.clear()
        ax1.plot(pdata.timestamp - init_time, pdata.voltage_reading, '.')

    ani = FuncAnimation(fig, animate, interval=1)
    plt.show()

