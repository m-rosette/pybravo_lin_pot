import matplotlib.pyplot as plt
import time
import threading
import random
from pitch_compliance_copy import PitchCompliance


if __name__ == '__main__':
    pc = PitchCompliance()
    print(pc._ni_device.voltage_reading)