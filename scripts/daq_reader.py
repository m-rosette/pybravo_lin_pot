import nidaqmx
from nidaqmx.constants import TerminalConfiguration
import atexit
import sys
import threading
import time
import matplotlib.pyplot as plt


class NI_Device:
    def __init__(self):
        ''' Create a new NI device interface'''
        # self.ni_
        self.RSE = TerminalConfiguration.RSE
        self._running = False
        self.voltage_reading = 0

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
        """Sample the DAQ and read its value"""
        while self._running:
            with nidaqmx.Task() as task:
                # Add channel from daq and set the configuration reader
                task.ai_channels.add_ai_voltage_chan(physical_chan, terminal_config=self.RSE)
                
                # Read the voltage
                self.voltage_reading = task.read(number_of_samples_per_channel=num_samples)
    
    def plot_data(self, data):
        plt.plot(data, '.')
        plt.ylabel('Output voltage (V)')
        plt.show()


if __name__ == '__main__':
    ni = NI_Device()
    
    ni.start()

    while True:
        try:
            print(f"The current voltage reading is: {ni.voltage_reading}")
            time.sleep(0.1)
        except KeyboardInterrupt:
            ni.stop()
            sys.exit()