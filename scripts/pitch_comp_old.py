import time
import atexit

from logger import FileLogger, init_logger
from daq_reader import NI_Device
from config_loader import ArmConfig
from bravo_handler import BravoHandler


class PitchCompliance():
    def __init__(self, desired_config_num=0):
        self._bravo = BravoHandler()
        self._ni_device = NI_Device()
        self._config_loader = ArmConfig()

        self.desired_config_num = desired_config_num # User selected arm configuration
        self.desired_config = self._config_loader.initial_config

        self._running = False
        self.logger = init_logger("PitchCompliance")
        self._file_logger = FileLogger()

        self._get_config()

        # Make sure that we shutdown the interface when we exit
        atexit.register(self.disable)

    def enable(self) -> None:
        """Enable arm control and sensor readings."""
        self._running = True
        self.logger.warning("Arm control has been enabled.")

    def disable(self) -> None:
        """Disable arm control and sensor readings."""
        self._running = False
        self.logger.warning("Arm control has been disabled.")
    
    def _get_config(self):
        """Load predetermined configurations of the arm"""
        all_configs = self._config_loader.load_matfile_data()
        self.desired_config = all_configs[self.desired_config_num]

    def _run_controller(self):
        """Send commands to the arm"""
        while self._running:
            
            # Log incomming data
            self._file_logger(
                time.time(),
                self._bravo.joint_positions,
                self._ni_device.voltage_reading,
            )

            # Delay for sensors to activate
            time.sleep(0.25)

            # Send command to arm
            self._bravo._run_controller(self.desired_config)


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

