# utils/serial_controller.py
import serial
from PyQt5.QtCore import QThread, pyqtSignal

class SerialReaderThread(QThread):
    new_data_received = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, port, baudrate, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self._is_running = True

    def run(self):
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            while self._is_running:
                try:
                    line = self.serial.readline().decode('utf-8', errors='replace')
                    if line:
                        self.new_data_received.emit(line)
                except Exception as e:
                    self.error_occurred.emit(str(e))
        except Exception as e:
            self.error_occurred.emit(f"Serial init error: {e}")
        finally:
            self.finished_signal.emit()

    def stop(self):
        self._is_running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.wait(1000)


class SerialWriterThread(QThread):
    write_success = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baudrate, parent=None):
        super().__init__(parent)
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self._is_running = True
        self._message_queue = []

    def run(self):
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            while self._is_running:
                if self._message_queue:
                    msg = self._message_queue.pop(0)
                    try:
                        self.serial.write(msg.encode())
                        self.write_success.emit(msg)
                    except Exception as e:
                        self.error_occurred.emit(str(e))
                self.msleep(50)
        except Exception as e:
            self.error_occurred.emit(f"Serial init error: {e}")

    def send(self, message):
        self._message_queue.append(message)

    def stop(self):
        self._is_running = False
        if self.serial and self.serial.is_open:
            self.serial.close()
        self.wait(1000)