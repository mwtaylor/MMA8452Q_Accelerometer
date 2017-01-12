import threading
import queue
import time
from datetime import datetime
from mma8452q import AccelerometerMMA8452Q, AccelerationRange, DataRate


class AccelerometerCommunication(threading.Thread):
    def __init__(self, acceleration_queue: queue.Queue, command_queue: queue.Queue, i2c_address: int):
        threading.Thread.__init__(self)

        self._address = i2c_address
        self._acceleration_queue = acceleration_queue
        self._command_queue = command_queue

    def run(self):
        accelerometer = AccelerometerMMA8452Q(1, self._address)

        accelerometer.reset()

        data_rate = DataRate.hz6_25
        accelerometer.setup(AccelerationRange.g2, False, data_rate)
        accelerometer.enable()

        expected_period = data_rate.period()

        while True:
            if accelerometer.is_data_ready():
                self._acceleration_queue.put_nowait((datetime.now(), accelerometer.read_acceleration_and_status()))

            if not self._command_queue.empty():
                command = self._command_queue.get_nowait()
                if command == stop_command:
                    return

            time.sleep(expected_period / 5)

stop_command = "stop"
