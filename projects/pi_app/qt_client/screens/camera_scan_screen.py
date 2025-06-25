from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
from pyzbar import pyzbar

class CameraScanScreen(QWidget):
    barcode_scanned = pyqtSignal(str)
    back_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cap = None
        self.timer = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Camera view fills the background
        self.camera_frame = QLabel()
        self.camera_frame.setAlignment(Qt.AlignCenter)
        self.camera_frame.setStyleSheet("background: #000;")
        layout.addWidget(self.camera_frame)
        # Floating overlay for back button
        back_overlay = QWidget(self)
        back_overlay.setAttribute(Qt.WA_TranslucentBackground)
        back_overlay.setStyleSheet("background: transparent;")
        back_layout = QHBoxLayout(back_overlay)
        back_layout.setContentsMargins(0, 0, 0, 0)
        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(36, 36)
        self.back_button.setStyleSheet("font-size: 20px; border-radius: 8px; border: 1px solid #bbb; background: rgba(245,246,250,0.92); padding: 0px;")
        self.back_button.setObjectName("link_button")
        self.back_button.clicked.connect(self._on_back_clicked)
        back_layout.addWidget(self.back_button, alignment=Qt.AlignLeft)
        back_overlay.setParent(self)
        back_overlay.move(40, 40)
        back_overlay.adjustSize()
        back_overlay.show()
        self.back_overlay = back_overlay

        # Floating overlay for info label
        info_overlay = QWidget(self)
        info_overlay.setAttribute(Qt.WA_TranslucentBackground)
        info_overlay.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_overlay)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_label = QLabel("Align the barcode with your camera.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: white; background: transparent; border-radius: 12px; border: none; padding: 10px 18px;")
        info_layout.addWidget(self.info_label)
        info_overlay.setParent(self)
        info_overlay.move(40, 100)
        info_overlay.adjustSize()
        info_overlay.show()
        self.info_overlay = info_overlay

    def showEvent(self, event):
        super().showEvent(event)
        self.start_camera()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        if self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            return
        barcodes = pyzbar.decode(frame)
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            self.barcode_scanned.emit(barcode_data)
            # Do not handle navigation here; let main window handle it
            return
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.camera_frame.setPixmap(QPixmap.fromImage(qt_image))

    def _on_back_clicked(self):
        self.stop_camera()
        self.back_requested.emit()
        # Do not handle navigation here; let main window handle it

    def stop_camera(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.camera_frame.clear()

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Dynamically scale font size based on window height
        font_size = max(18, int(self.height() * 0.045))
        self.info_label.setStyleSheet(
            f"color: white; background: transparent; border-radius: 12px; border: none; padding: 10px 18px; font-size: {font_size}px;"
        )
        self.info_label.adjustSize()  # Ensure label fits content
        self.info_overlay.adjustSize()  # Ensure overlay fits label
        # Center info_overlay in the middle of the screen
        info_size = self.info_overlay.size()
        x = (self.width() - info_size.width()) // 2
        y = (self.height() - info_size.height()) // 2
        self.info_overlay.move(x, y)
        # Keep back_overlay at top-left
        self.back_overlay.move(40, 40)
