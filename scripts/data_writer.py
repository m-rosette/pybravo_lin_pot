import socket
import numpy as np
import struct
from time import sleep


if __name__ == "__main__":
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((socket.gethostname(), 6969))
        sock.listen()
        conn, addr = sock.accept()
        while True:
            for datapoint in np.append(np.linspace(0, 2*np.pi, 10), np.linspace(2*np.pi, 0, 10)):
                raw_bytes = struct.pack('d', datapoint)
                conn.send(raw_bytes)
                sleep(0.1)
