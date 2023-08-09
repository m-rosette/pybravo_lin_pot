import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import atexit
import sys
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# import dash
# from dash.dependencies import Output, Input
# import dash_core_components as dcc
# import dash_html_components as html
# import plotly
# import random
# import plotly.graph_objs as go
# from collections import deque

class NI_Device:
    def __init__(self):
        ''' Create a new NI device interface'''
        self.RSE = TerminalConfiguration.RSE
        self._running = False
        self.voltage_reading = [0]

        # Create a new thread to poll the DAQ readings
        self.poll_t = threading.Thread(target=self.read_daq)
        self.poll_t.daemon = True
        
        # Make sure that we shutdown the interface when we exit
        atexit.register(self.stop)

    def start(self) -> None:
        """Start the daq reader."""
        # Start the polling thread
        self._running = True
        self.poll_t.start()

    def stop(self) -> None:
        """Stop the daq reader."""
        # Stop the poll thread loop
        self._running = False
        self.poll_t.join()

    def read_daq(self, physical_chan="Dev1/ai1", num_samples=1):
        """Sample the DAQ at a rate of 100Hz"""
        while self._running:
            with nidaqmx.Task() as task:
                # task.channel_
                # Add channel from daq and set the configuration reader
                task.ai_channels.add_ai_voltage_chan(physical_chan, terminal_config=self.RSE)
                
                # Read the voltage
                self.voltage_reading = task.read(number_of_samples_per_channel=num_samples)

    def plot_data(self, data):
        """Plot the DAQ output voltage"""
        plt.plot(data, '.')
        plt.ylabel('Output voltage (V)')
        plt.show()


if __name__ == '__main__':
    ni_device = NI_Device()
    
    ni_device.start()

    # Let the controller do its thing
    while True:
        try:
            if ni_device.voltage_reading == 0:
                continue
            print(f"The current voltage reading is: {round(ni_device.voltage_reading[0], 3)}")
            time.sleep(0.1)
            
        except KeyboardInterrupt:
            ni_device.stop()
            sys.exit()