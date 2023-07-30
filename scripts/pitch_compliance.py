import struct
import sys
import time
import numpy as np
import threading
import atexit
import nidaqmx
from nidaqmx.constants import TerminalConfiguration

from daq_reader import NI_Device
from config_loader import ArmConfig

sys.path.append("..")

from logger import FileLogger, init_logger

from pybravo import BravoDriver, DeviceID, Packet, PacketID

class PitchCompliance():
    def __init__(self, desired_config_num=0):
        self._bravo = BravoDriver()
        self._config_loader = ArmConfig()

        # Initialize joint position data
        self.num_joints = 7
        self.joint_positions = [0.0] * self.num_joints
        self.desired_config_num = desired_config_num # User selected arm configuration
        self.desired_config = self._config_loader.initial_config

        self._bravo.attach_callback(PacketID.POSITION, self.read_joint_position_cb)
        
        # Initialize NI Device data
        self.RSE = TerminalConfiguration.RSE
        self.voltage_reading = 0

        self._running = False
        self.logger = init_logger("PitchCompliance")
        self._file_logger = FileLogger()

        # Create a new thread to poll the joint angles
        self.poll_joint_t = threading.Thread(target=self.poll_joint_angles)
        self.poll_joint_t.daemon = True

        # Create a new thread to poll the DAQ readings
        self.poll_daq_t = threading.Thread(target=self.read_daq)
        self.poll_daq_t.daemon = True

        # Run the controller in it's own thread
        self.controller_t = threading.Thread(target=self._run_controller)
        self.controller_t.daemon = True

        self._get_config()

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        # Start the connection to the Bravo
        self._bravo.connect()

        # Start the polling threads
        self._running = True

        self.poll_daq_t.start()
        self.poll_joint_t.start()
        self.controller_t.start()

        self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable arm control and sensor readings."""
        # Stop the poll thread loop
        self._running = False

        # Disconnect the bravo driver
        self._bravo.disconnect()
        
        self.poll_joint_t.join()
        self.poll_daq_t.join()
        self.controller_t.join()

        self.logger.warning("Arm control has been disabled.")

    def poll_joint_angles(self) -> None:
        """Request the current joint positions at a rate of 100 Hz."""
        while self._running:
            request = Packet(
                DeviceID.ALL_JOINTS, PacketID.REQUEST, bytes([PacketID.POSITION.value])
            )
            self._bravo.send(request)
            time.sleep(0.01)

    def read_joint_position_cb(self, packet: Packet) -> None:
        """Handle the joint position reading.

        Args:
            packet: A packet with a joint position measurement.
        """
        # The unpacking order will need to change according to the system on which the
        # data is received (i.e., Windows vs Linux)
        position: float = struct.unpack("<f", packet.data)[0]

        # The jaws are a linear joint; convert from mm to m
        if packet.device_id == DeviceID.LINEAR_JAWS:
            position *= 0.001

        # Save the joint positions at the same index as their ID
        self.joint_positions[packet.device_id.value - 1] = position

    def read_daq(self, physical_chan="Dev1/ai1", num_samples=1):
        # TODO: Need to see if I can get rid of the num_samples since I have while loop
        while self._running:
            with nidaqmx.Task() as task:
                task.ai_channels.add_ai_voltage_chan(physical_chan, terminal_config=self.RSE)
                
                self.voltage_reading = task.read(number_of_samples_per_channel=num_samples)
            # time.sleep(0.01)    # Does this go under the "with"???
            # TODO: Might need to add a 0.01 delay to match the incoming joint data (time.sleep(0.01))
    
    def _get_config(self):
        all_configs = self._config_loader.load_matfile_data()
        self.desired_config = all_configs[self.desired_config_num]

    def _run_controller(self):
        """Send commands to the arm"""
        while self._running:
    
            self._file_logger(
                time.time(),
                self.joint_positions,
                self.voltage_reading,
            )

            # Create the packets and send them to the Bravo   
            # TODO: Try and see if you can send the Packet to ALL_JOINTS instead of individually 
            for i, position in enumerate(self.desired_config):
                packet = Packet(DeviceID(i+1), PacketID.POSITION, struct.pack("<f", position))
                self._bravo.send(packet)

            # Could maybe try replacing "DeviceID.ALL_JOINTS" with "8"
            # one, two, three, four, five, six, seven = self.desired_config
            # packet = Packet(DeviceID.ALL_JOINTS, PacketID.POSITION, struct.pack("<fffffff", one, two, three, four, five, six, seven))
            # print(packet)
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

