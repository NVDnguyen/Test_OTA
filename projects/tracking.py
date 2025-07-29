import sys
import serial
import time
import threading
import re
import numpy as np
from queue import Queue
from PyQt5 import QtWidgets, QtCore
from PIL import Image
import pyqtgraph as pg

Image.MAX_IMAGE_PIXELS = None

ANCHORS = [
    (0, 630),
    (5000, 5300),
    (5100, 0),
    (0, 5392)

]

SERIAL_PORT = 'COM4'
BAUDRATE = 115200
MAX_RANGE = 8000

class FPTTracker(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time UWB Tracking")
        self.setGeometry(100, 100, 800, 800)

        self.data_queue = Queue()
        self.position_history = []
        self.trail_history = []

        self.serial_pattern = re.compile(r'0x[\da-f]{4}:\s*=(\d+)')

        # Thiết lập serial và giao diện
        self.init_serial()
        self.init_ui()
        self.start_serial_thread()

        # Timer 50 ms → ~20 FPS
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)

        self.fps_time = time.time()

    def init_serial(self):
        try:
            self.ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUDRATE,
                timeout=0.1
            )
        except Exception as e:
            print("Không thể mở cổng serial:", e)
            sys.exit(1)

    def init_ui(self):
        # 1) Tạo PlotWidget, ẩn axis
        self.plot_widget = pg.PlotWidget()
        # self.plot_widget.hideAxis('bottom')
        # self.plot_widget.hideAxis('left')
        self.setCentralWidget(self.plot_widget)

        # 2) Load ảnh và đặt background
        img = Image.open(r'C:\Users\Ponpon\Documents\test.png')
        arr = np.array(img)
        # Nếu cần xoay, uncomment:
        arr = np.rot90(arr, k=3)

        bg = pg.ImageItem(arr)
        bg.setZValue(-100)
        bg.setRect(QtCore.QRectF(0, 0, 5700, 7000))
        self.plot_widget.addItem(bg)

        # 3) Set range & limits
        self.plot_widget.setXRange(0, 5700)
        self.plot_widget.setYRange(0, 7000)
        self.plot_widget.setLimits(
            xMin=0, xMax=5700,
            yMin=0, yMax=7000
        )
        # anchor_x, anchor_y = zip(*ANCHORS)
        # self.plot_widget.plot(
        #     anchor_x, anchor_y,
        #     pen=None, symbol='o',
        #     symbolSize=20, symbolBrush='b'
        # )
        # 4) Bắt click để chọn target
        self.plot_widget.scene().sigMouseClicked.connect(self.on_click)
        self.target = None
        self.target_scatter = self.plot_widget.plot(
            [], [], pen=None, symbol='x', symbolSize=20,
            symbolBrush='g'
        )
        self.path_curve = self.plot_widget.plot(
            [], [], pen=pg.mkPen('r', width=4)
        )

        # 5) Scatter/tag, trail, text
        self.fpt_scatter = self.plot_widget.plot(
            [], [], pen=None,
            symbol='o', symbolSize=40,
            symbolBrush='cyan'
        )
        self.trail_curve = self.plot_widget.plot(
            [], [], pen=pg.mkPen('cyan', width=1)
        )
        self.fpt_text = pg.TextItem(
            text="SCI", color='w',
            anchor=(0.5, -1.0)
        )
        self.plot_widget.addItem(self.fpt_text)

    def on_click(self, ev):
        pos = ev.scenePos()
        vb = self.plot_widget.getViewBox()
        mp = vb.mapSceneToView(pos)
        x, y = mp.x(), mp.y()
        if 0 <= x <= 5700 and 0 <= y <= 7000:
            self.target = np.array([x, y])
            self.target_scatter.setData([x], [y])
            self.path_curve.setData([], [])

    def start_serial_thread(self):
        threading.Thread(target=self.serial_reader,
                         daemon=True).start()

    def serial_reader(self):
        while True:
            try:
                line = self.ser.readline().decode('utf-8',
                                                 errors='replace')
                if line and '=' in line:
                    self.data_queue.put(line)
            except Exception as e:
                print("Serial error:", e)

    def lse_trilateration(self, distances):
        x1, y1 = ANCHORS[0]
        d1 = distances[0]
        A, b = [], []
        for i in range(1, 4):
            xi, yi = ANCHORS[i]
            di = distances[i]
            A.append([xi - x1, yi - y1])
            b.append(0.5*(xi**2 + yi**2 - di**2
                          - (x1**2 + y1**2 - d1**2)))
        A, b = np.array(A), np.array(b)
        try:
            sol, *_ = np.linalg.lstsq(A, b, rcond=None)
            return sol
        except:
            return np.array([np.nan, np.nan])

    def update_plot(self):
        if self.data_queue.empty():
            return
        while self.data_queue.qsize() > 1:
            self.data_queue.get()
        raw = self.data_queue.get()

        dist = list(map(int,
                        self.serial_pattern.findall(raw)))
        if len(dist) < 4 or any(d <= 0 or d > MAX_RANGE
                                for d in dist[:4]):
            return

        pos = self.lse_trilateration(dist[:4])
        if np.isnan(pos).any():
            return

        # Median filter
        self.position_history.append(pos)
        if len(self.position_history) > 100:
            self.position_history.pop(0)
        filtered = np.median(np.array(self.position_history),
                              axis=0)

        # Vẽ TAG
        self.fpt_scatter.setData([filtered[0]],
                                 [filtered[1]])
        self.fpt_text.setPos(filtered[0],
                             filtered[1])

        # Vẽ trail
        # self.trail_history.append(filtered)
        # if len(self.trail_history) > 200:
        #     self.trail_history.pop(0)
        # trail = np.array(self.trail_history)
        # self.trail_curve.setData(trail[:,0], trail[:,1])

        # Vẽ đường thẳng tới target (nếu đã click)
        if self.target is not None:
            lx = [filtered[0], self.target[0]]
            ly = [filtered[1], self.target[1]]
            self.path_curve.setData(lx, ly)

        now = time.time()
        fps = 1.0 / (now - self.fps_time)
        self.fps_time = now
        self.setWindowTitle(f"Real-Time UWB Tracking (FPS: {fps:.1f})")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    tracker = FPTTracker()
    tracker.show()
    sys.exit(app.exec_())
