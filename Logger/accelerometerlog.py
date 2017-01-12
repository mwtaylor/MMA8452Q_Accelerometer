from accelerometercommunication import AccelerometerCommunication, stop_command
from mma8452q import AccelerationStatus
import queue
import csv
from datetime import datetime
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Log data from the connected accelerometer")
    parser.add_argument("--file", dest="output_file", required=True,
                        help="The file where the acceleration data will be stored (in CSV format).")
    parser.add_argument("--duration", dest="run_duration", required=True, type=int,
                        help="How long to collect acceleration data (in seconds)")
    parser.add_argument("--address", dest="device_address", type=int, default=0x1D,
                        help="The i2c address of the accelerometer")
    args = parser.parse_args()

    acceleration_queue = queue.Queue()
    command_queue = queue.Queue()

    accelerometer = AccelerometerCommunication(acceleration_queue, command_queue, args.device_address)
    accelerometer.start()

    start_time = datetime.now()

    with open(args.output_file, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)

        while (datetime.now() - start_time).seconds < args.run_duration:
            while not acceleration_queue.empty():
                queue_value = acceleration_queue.get_nowait()

                if isinstance(queue_value[0], datetime):
                    data_time = queue_value[0]
                    formatted_date = data_time.strftime("%m/%d/%Y %H:%M:%S.%f")
                else:
                    formatted_date = ""

                if isinstance(queue_value[1], AccelerationStatus):
                    acceleration_status = queue_value[1]
                    if acceleration_status.x is not None:
                        x = acceleration_status.x
                    else:
                        x = ""
                    if acceleration_status.y is not None:
                        y = acceleration_status.y
                    else:
                        y = ""
                    if acceleration_status.z is not None:
                        z = acceleration_status.z
                    else:
                        z = ""
                else:
                    x = ""
                    y = ""
                    z = ""

                csv_writer.writerow([formatted_date, x, y, z])

    command_queue.put_nowait(stop_command)

    accelerometer.join()
