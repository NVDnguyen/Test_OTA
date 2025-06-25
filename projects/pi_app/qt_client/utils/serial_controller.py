# utils/serial_controller.py

import time
import serial
from PyQt5.QtCore import QThread, pyqtSignal

class SerialReaderThread(QThread):
    """
    A QThread to read from the serial port continuously.
    Emits a signal with the data read.
    """
    new_data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, port, baudrate, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.running = True
        self.ser = None

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            self.new_data_received.emit(f"Successfully connected to {self.port}\n")
            while self.running:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='replace').rstrip()
                    self.new_data_received.emit(line + "\n")
                time.sleep(0.1) # Small delay to prevent high CPU usage
        except serial.SerialException as e:
            self.error_occurred.emit(f"Serial Error: {e}\n")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
                self.new_data_received.emit(f"Serial port {self.port} closed.\n")
            self.finished_signal.emit()

    def stop(self):
        self.running = False

class SerialWriterThread(QThread):
    """
    A QThread to write data to the serial port.
    Emits signals for success or error.
    """
    write_success = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, port, baudrate, timeout=1):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.data_queue = []
        self.running = True

    def run(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            while self.running:
                if self.data_queue:
                    data = self.data_queue.pop(0)
                    try:
                        self.ser.write(data.encode('utf-8'))
                        self.write_success.emit(f"Sent: {data}")
                    except serial.SerialException as e:
                        self.error_occurred.emit(f"Write Error: {e}")
                time.sleep(0.05)
        except serial.SerialException as e:
            self.error_occurred.emit(f"Serial Error: {e}")
        finally:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.finished_signal.emit()

    def send(self, data):
        self.data_queue.append(data)

    def stop(self):
        self.running = False
