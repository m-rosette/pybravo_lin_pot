# This file is based on the example file "read_joint_positions.py" from pybravo

import atexit
import struct
import sys
import threading
import time

from pybravo import BravoDriver, DeviceID, Packet, PacketID


class JointReader:
    """Demonstrates how to request position messages from the Bravo."""

    def __init__(self) -> None:
        """Create a new joint position interface."""
        self._bravo = BravoDriver()
        self._running = False
        self.num_joints = 7
        self.joint_positions = [0.0] * self.num_joints

        self._bravo.attach_callback(PacketID.POSITION, self.read_joint_position_cb)

        # Create a new thread to poll the joint angles
        self.poll_t = threading.Thread(target=self.poll_joint_angles)
        self.poll_t.daemon = True

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.stop)

    def start(self) -> None:
        """Start the joint position reader."""
        # Start a connection to the Bravo
        self._bravo.connect()

        # Start the polling thread
        self._running = True
        self.poll_t.start()

    def stop(self) -> None:
        """Stop the joint position reader."""
        # Stop the poll thread loop
        self._running = False

        # Disconnect the bravo driver
        self._bravo.disconnect()

        self.poll_t.join()

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

        # # The jaws are a linear joint; convert from mm to m
        # if packet.device_id == DeviceID.LINEAR_JAWS:
        #     position *= 0.001

        # Save the joint positions at the same index as their ID
        self.joint_positions[packet.device_id.value - 1] = position


if __name__ == "__main__":
    reader = JointReader()

    reader.start()

    while True:
        try:
            print(f"The current joint positions are: {reader.joint_positions}")
            time.sleep(0.1)
        except KeyboardInterrupt:
            reader.stop()
            sys.exit()