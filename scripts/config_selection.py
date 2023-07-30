import struct
import sys
import time
import mat73
import numpy as np

sys.path.append("..")

from pybravo import BravoDriver, DeviceID, Packet, PacketID


if __name__ == "__main__":
    bravo = BravoDriver()
    
    # Start the bravo connection
    bravo.connect()
    time.sleep(0.05)

    # Specify the desird positions
    initial_config = [0, 1.57, 2.64, 0, 0.6, 3.04, 3.14]
    configs_file = mat73.loadmat('data/hardware_configs.mat')
    configs = configs_file['configs']
    configs_fl = np.fliplr(configs)
    final_configs_fl = np.insert(configs_fl, 0, initial_config, 0)

    control_type = input("Enter desired control type (s or t): ")
    if control_type == "t":
        traj_number = int(input(f"Enter configuration number (0-{len(final_configs_fl)-1}): "))
        desired_positions = final_configs_fl[traj_number]

        # Create the packets and send them to the Bravo    
        for i, position in enumerate(desired_positions):
            packet = Packet(DeviceID(i+1), PacketID.POSITION, struct.pack("<f", position))
            bravo.send(packet)

    elif control_type == "s":
        # Send singular joint commands
        print("Joints: End-effector = 1, ... Base = 7")
        joint_id = int(input("Joint to Control: "))
        joint_pos = float(input("Desired Position: "))
        packet = Packet(DeviceID(joint_id), PacketID.POSITION, struct.pack("<f", joint_pos))
        bravo.send(packet)
        time.sleep(1)

    # Shutdown the connection
    bravo.disconnect()
