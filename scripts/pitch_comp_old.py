import struct
import sys
import time
import numpy as np
import threading
import atexit
from argparse import ArgumentParser, Namespace

from daq_reader import NI_Device
from read_joint_positions import JointReader
from config_loader import ArmConfig

from logger import FileLogger, init_logger

sys.path.append("..")

# from utils import FileLogger, init_logger
from pybravo import BravoDriver, DeviceID, Packet, PacketID

class PitchCompliance():
    def __init__(self, desired_config_num=0):
        self._bravo = BravoDriver()
        self._joint_reader = JointReader() # Has the joint angles coming in on its own thread
        self._ni_device = NI_Device() # Has the voltages coming in on its own thread
        self._config_loader = ArmConfig()

        self.desired_config_num = desired_config_num # User selected arm configuration
        self.desired_config = self._config_loader.initial_config

        self._running = False
        self.logger = init_logger("PitchCompliance")
        self._file_logger = FileLogger()

        # Run the controller in it's own thread
        self.controller_t = threading.Thread(target=self._run_controller)
        self.controller_t.daemon = True

        self._get_config()

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        self._running = True
        self._bravo.connect()
        # self._joint_reader.poll_t.start()
        # self._ni_device.poll_t.start()
        self._ni_device.start()
        self._joint_reader.start()
        self.controller_t.start()

        self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable admittance control."""
        self._running = False
        self._bravo.disconnect()
        # self._joint_reader.poll_t.join()
        # self._ni_device.poll_t.join()
        self.controller_t.join()

        self.logger.warning("Arm control has been disabled.")
    
    def _get_config(self):
        all_configs = self._config_loader.load_matfile_data()
        self.desired_config = all_configs[self.desired_config_num]

    def _run_controller(self):
        """Send commands to the arm"""
        while self._running:
    
            # self._file_logger(
            #     time.time(),
            #     self._joint_reader.joint_positions,
            #     self._ni_device.voltage_reading,
            # )

            # print(self._joint_reader.joint_positions, self._ni_device.voltage_reading)
            # time.sleep(0.1)

            # Create the packets and send them to the Bravo   
            # TODO: Try and see if you can send the Packet to ALL_JOINTS instead of individually 
            for i, position in enumerate(self.desired_config):
                print(position)
                time.sleep(1)
                packet = Packet(DeviceID(i+1), PacketID.POSITION, struct.pack("<f", position))
                self._bravo.send(packet)

            # self._file_logger(
            #     time.time(),
            #     self._joint_reader.joint_positions,
            #     self._ni_device.voltage_reading,
            # )

            # print(self._joint_reader.joint_positions)
            # print(self._ni_device.voltage_reading)
            # time.sleep(0.1)

            # Could maybe try replacing "DeviceID.ALL_JOINTS" with "8"
            # one, two, three, four, five, six, seven = self.desired_config
            # packet = Packet(DeviceID.ALL_JOINTS, PacketID.POSITION, struct.pack("<fffffff", one, two, three, four, five, six, seven))
            # self._bravo.send(packet)
        

if __name__ == "__main__":
    config_num = int(input("Enter the desired configuration #: "))
    pitch_compliance = PitchCompliance(config_num)

    # Enable the controller
    pitch_compliance.enable()

    # Let the controller do its thing
    while True:
        try:
            time.sleep(0.01)
        except KeyboardInterrupt:
            pitch_compliance.disable()
            exit()

