# utils/serial_reader.py
import re
import numpy as np
from queue import Queue
from threading import Thread
import serial
import time

ANCHORS = [
    (0, 630),
    (5000, 5300),
    (5100, 0),
    (0, 5392)
]

# MAX_RANGE = 8000  

class UWBSerialReader:
    def __init__(self):
        self.serial_controller = serial.Serial()
        self.serial_controller.port = '/dev/ttyACM0'
        self.serial_controller.baudrate = 115200
        self.serial_controller.timeout = 0.01
        self.data_queue = Queue()
        self.position_history = []
        self.is_reading = False
        self.serial_pattern = re.compile(r'0x[\da-f]{4}:\s*=(\d+)')
        self.reader_thread = None

    def start_reading(self):
        try:
            self.serial_controller.open()
        except Exception as e:
            print(f"Serial connection error: {e}")
            return False
        
        self.is_reading = True
        self.reader_thread = Thread(target=self._read_serial, daemon=True)
        self.reader_thread.start()
        return True

    def stop_reading(self):
        self.is_reading = False
        if self.serial_controller.is_open:
            self.serial_controller.close()
        if self.reader_thread:
            self.reader_thread.join(timeout=1.0)

    def _read_serial(self):
        while self.is_reading:
            try:
                line = self.serial_controller.readline().decode('utf-8', errors='replace')
                if line and '=' in line:
                    self.data_queue.put(line)
            except Exception as e:
                print(f"Serial read error: {e}")
                time.sleep(0.01)

    def get_latest_data(self):
        if self.data_queue.empty():
            return None
    
        while self.data_queue.qsize() > 1:
            self.data_queue.get()
        return self.data_queue.get()

    def lse_trilateration(self, distances):
        """Least Squares Estimation"""
        if len(distances) < 4:
            return None
            
        x1, y1 = ANCHORS[0]
        d1 = distances[0]
        A, b = [], []
        
        for i in range(1, 4):
            xi, yi = ANCHORS[i]
            di = distances[i]
            A.append([xi - x1, yi - y1])
            b.append(0.5*(xi**2 + yi**2 - di**2 - (x1**2 + y1**2 - d1**2)))
        
        A, b = np.array(A), np.array(b)
        try:
            return np.linalg.lstsq(A, b, rcond=None)[0]
        except:
            return None

    def process_data(self, raw_data):
        dist = list(map(int, self.serial_pattern.findall(raw_data)))
        if len(dist) < 4 or any(d <= 0 or d > MAX_RANGE for d in dist[:4]):
            return None
        
        pos = self.lse_trilateration(dist[:4])
        if pos is None or np.isnan(pos).any():
            return None
        
        # Median filter
        self.position_history.append(pos)
        if len(self.position_history) > 100:
            self.position_history.pop(0)
        
        return np.median(np.array(self.position_history), axis=0)