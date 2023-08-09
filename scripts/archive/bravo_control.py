import atexit
import struct
import sys
import threading
import time

from pybravo import BravoDriver, DeviceID, Packet, PacketID
from config_loader import ArmConfig


class BravoControl:
    """Sends position messages to the Bravo."""

    def __init__(self, desired_config_num) -> None:
        """Create a new joint position interface."""
        self._config_loader = ArmConfig()
        self._config_loader._get_config(desired_config_num)
        self.desired_config = self._config_loader.desired_config

        self._bravo = BravoDriver()

        self._running = False

        # Run the controller in it's own thread
        self.controller_t = threading.Thread(target=self._run_controller)
        self.controller_t.daemon = True

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.stop)

    def start(self) -> None:
        """Start the bravo controller thread"""
        # Start the polling thread
        self._running = True
        self.controller_t.start()

    def stop(self) -> None:
        """Stop the bravo controller thread"""
        # Stop the polling thread
        self._running = False
        self.controller_t.join()

    def _run_controller(self):
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
    bravo_controller = BravoControl(config_num)

    # Enable the controller
    bravo_controller.start()

    # Let the controller do its thing
    while True:
        try:
            time.sleep(0.01)
        except KeyboardInterrupt:
            bravo_controller.stop()
            exit()