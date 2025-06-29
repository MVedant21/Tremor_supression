import serial
import serial.tools.list_ports
import joblib
import numpy as np
import re
import threading
import queue
import time
import csv


def find_serial_port(preferred_port=None):
    ports = serial.tools.list_ports.comports()
    available = [p.device for p in ports]
    if preferred_port in available:
        return preferred_port
    return available[0] if available else None

model = joblib.load("optimized_rf_model.pkl")
scaler = joblib.load("scaler.pkl")
mean_ = scaler.mean_
scale_ = scaler.scale_

log_file = open("imu_log_pre.csv", "w", newline="")
csv_writer = csv.writer(log_file)
csv_writer.writerow(["elapsed_sec", "raw_x", "raw_y", "raw_z"])

BAUD_RATE = 115200
IMU_PORT = find_serial_port("COM8")
MOTOR_PORT = find_serial_port("COM5")
if not IMU_PORT or not MOTOR_PORT:
    print("ERROR: required serial ports not found.")
    exit(1)

imu_arduino = serial.Serial(IMU_PORT,   BAUD_RATE, timeout=0.01)
motor_arduino = serial.Serial(MOTOR_PORT, BAUD_RATE, timeout=0.01)
time.sleep(2)  
print(f"Connected to IMU:{IMU_PORT} and MOTOR:{MOTOR_PORT}")

data_pattern = re.compile(
    r"Time: [\d\.]+ \| Raw: X = ([-\d\.]+), Y = ([-\d\.]+), Z = ([-\d\.]+) "
)

window_size = 50
buffer = np.zeros(window_size, dtype=float)
idx = 0
filled = False
data_q = queue.Queue(maxsize=5)
stop_event = threading.Event()

def read_sensor():
    global idx, filled
    start_time = time.time()
    last_sample_time = start_time
    target_interval  = 1.0 / 100  

    while not stop_event.is_set():
        now = time.time()
        if now - last_sample_time < target_interval:
            time.sleep(0.001)
            continue

        line = imu_arduino.readline().decode("utf-8", errors="ignore")
        m = data_pattern.search(line)
        if not m:
            continue

        raw_x = float(m.group(1))
        raw_y = float(m.group(2))
        raw_z = float(m.group(3))

        rel_time = now - start_time
        csv_writer.writerow([f"{rel_time:.3f}", raw_x, raw_y, raw_z])
        if idx % 20 == 0:
            log_file.flush()

        buffer[idx] = raw_z
        idx = (idx + 1) % window_size
        if idx == 0:
            filled = True

        if filled and (idx % 10 == 0) and not data_q.full():
            window = np.concatenate((buffer[idx:], buffer[:idx]))
            feat   = (window - mean_) / scale_
            pred   = model.predict(feat.reshape(1, -1))[0]
            data_q.put(pred)

        last_sample_time = now

def send_to_motor():
    last_pred = 0
    last_sent = 0.0
    interval  = 0.02  

    while not stop_event.is_set():
        now = time.time()
        try:
            last_pred = data_q.get_nowait()
        except queue.Empty:
            pass

        if now - last_sent >= interval:
            motor_arduino.write(f"{last_pred}\n".encode())
            motor_arduino.flush()
            last_sent = now

        time.sleep(0.001)

sensor_thread = threading.Thread(target=read_sensor, daemon=True)
motor_thread  = threading.Thread(target=send_to_motor, daemon=True)

sensor_thread.start()
motor_thread.start()

print("Threads started. Press Ctrl+C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopping...")
    stop_event.set()
    sensor_thread.join()
    motor_thread.join()
finally:
    imu_arduino.close()
    motor_arduino.close()
    log_file.close()
    print("Clean exit. Data logged to imu_log.csv.")
