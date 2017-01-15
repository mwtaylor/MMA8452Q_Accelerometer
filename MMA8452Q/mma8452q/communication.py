import threading
import queue
import time
from datetime import datetime
from .device import AccelerometerMMA8452Q


class AccelerometerCommunication(threading.Thread):
    def __init__(self,
                 acceleration_queue: queue.Queue,
                 command_queue: queue.Queue,
                 accelerometer: AccelerometerMMA8452Q):
        threading.Thread.__init__(self)

        self._acceleration_queue = acceleration_queue
        self._command_queue = command_queue
        self._accelerometer = accelerometer

    def run(self):
        self._accelerometer.enable()

        expected_period = self._accelerometer.data_rate.period()

        while True:
            if self._accelerometer.is_data_ready():
                self._acceleration_queue.put_nowait(
                    (datetime.now(), self._accelerometer.read_acceleration_and_status()))

            if not self._command_queue.empty():
                command = self._command_queue.get_nowait()
                if command == stop_command:
                    return

            time.sleep(expected_period / 5)

stop_command = "stop"
