import time
import atexit

from logger import FileLogger, init_logger
from daq_reader import NI_Device
from bravo_handler import BravoHandler
from config_loader import ArmConfig


class PitchCompliance():
    def __init__(self, desired_config_num=0):
        self._config_loader = ArmConfig()
        self._config_loader._get_config(desired_config_num)


        self._bravo = BravoHandler(self._config_loader.desired_config)
        self._ni_device = NI_Device()

        self._running = False
        self.logger = init_logger("PitchCompliance")
        self._file_logger = FileLogger()

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        self._running = True

        self._bravo.start()
        self._ni_device.start()

        # Delay for sensors to activate
        time.sleep(0.25)
        self._run_controller()
        
        self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable arm control and sensor readings."""
        self._running = False

        self._bravo.stop()
        self._ni_device.stop()

        self.logger.warning("Arm control has been disabled.")

    def _run_controller(self):
        """Send commands to the arm"""
        while self._running:
            
            # Log incomming data
            self._file_logger(
                time.time(),
                self._bravo.joint_positions,
                self._ni_device.voltage_reading,
            )

            # Send command to arm
            self._bravo._run_controller()


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

