# utils/serial_reader.py
import re
import numpy as np
from queue import Queue
from threading import Thread, Event
import serial
import time

ANCHORS = [
    (1600, 0),
    (0, 1300),
    (0, 0),
    (1600, 1300)
]

MAX_RANGE = 8000  

class UWBSerialReader:
    def __init__(self, port='/dev/ttyACM0', baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_controller = None
        self.data_queue = Queue()
        self.position_history = []
        self.is_reading = False
        self.serial_pattern = re.compile(r'0x[\da-f]{4}:\s*=(\d+)')
        self.reader_thread = None
        self.stop_event = Event()

    def start_reading(self):
        try:
            self.serial_controller = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
        except Exception as e:
            print(f"Serial connection error: {e}")
            return False
        
        self.is_reading = True
        self.stop_event.clear()
        self.reader_thread = Thread(target=self._read_serial, daemon=True)
        self.reader_thread.start()
        return True

    def stop_reading(self):
        self.is_reading = False
        self.stop_event.set()
        if self.serial_controller and self.serial_controller.is_open:
            self.serial_controller.close()
        if self.reader_thread:
            self.reader_thread.join(timeout=1.0)

    def _read_serial(self):
        while self.is_reading and not self.stop_event.is_set():
            try:
                line = self.serial_controller.readline().decode('utf-8', errors='replace')
                if line and '=' in line:
                    self.data_queue.put(line)
            except Exception as e:
                if "timed out" not in str(e):
                    print(f"Serial read error: {e}")
                time.sleep(0.01)

    def get_latest_data(self):
        if self.data_queue.empty():
            return None
        
        # get latest data
        while self.data_queue.qsize() > 1:
            self.data_queue.get()
        return self.data_queue.get()

    def lse_trilateration(self, distances):
        """LSE"""
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
            sol, *_ = np.linalg.lstsq(A, b, rcond=None)
            return sol
        except:
            return np.array([np.nan, np.nan])

    def process_data(self, raw_data):
        # get raw distance
        dist = list(map(int, self.serial_pattern.findall(raw_data)))
        if len(dist) < 4 or any(d <= 0 or d > MAX_RANGE for d in dist[:4]):
            return None
        
        # LSE
        pos = self.lse_trilateration(dist[:4])
        if np.isnan(pos).any():
            return None
        
        # Median filter
        self.position_history.append(pos)
        if len(self.position_history) > 100:
            self.position_history.pop(0)
        
        return np.median(np.array(self.position_history), axis=0)