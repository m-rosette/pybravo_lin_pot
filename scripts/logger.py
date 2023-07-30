import logging
import os
from datetime import datetime

import numpy as np


def init_logger(name: str, log_level: int = logging.INFO) -> logging.Logger:
    logging.basicConfig()
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    return logger


class FileLogger:
    """File logging handler."""

    def __init__(self, filename: str | None = None) -> None:
        log_dir = os.path.join(os.getcwd(), "logs")

        if not os.path.isdir(log_dir):
            os.mkdir(log_dir)

        if filename is None:
            filename = os.path.join(
                log_dir, f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log"
            )
        else:
            filename = os.path.join(log_dir, filename)

        self.log_file = open(filename, "w")  # type: ignore

        self.log_file.write(
            "timestamp,joint_position,linear_potentiometer\n"
        )

        return

    def __call__(
        self,
        timestamp: float,
        joint_positions: np.ndarray,
        linear_potentiometer: float,
    ) -> None:
        self.log_file.write(
            f"{timestamp},{joint_positions},{linear_potentiometer}\n"
        )

        return
