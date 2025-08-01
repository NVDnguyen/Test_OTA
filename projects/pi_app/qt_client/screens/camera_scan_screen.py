from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
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
        self.last_barcode = None  # Track last scanned barcode
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        # Camera view fills the background
        self.camera_frame = QLabel()
        self.camera_frame.setAlignment(Qt.AlignCenter)
        self.camera_frame.setStyleSheet("background: #000;")
        self.camera_frame.setSizePolicy(self.sizePolicy().Expanding, self.sizePolicy().Expanding)
        layout.addWidget(self.camera_frame)
        # Floating overlay for back button
        self.back_button = QPushButton("←")
        self.back_button.setMinimumSize(40, 40)
        self.back_button.setMaximumSize(64, 64)
        self.back_button.setStyleSheet(
            "font-size: 20px; border-radius: 10px; border: 1.5px solid #bbb; background: rgba(245,246,250,0.96); padding: 0px; min-width:40px; min-height:40px; max-width:64px; max-height:64px;"
        )
        self.back_button.setObjectName("link_button")
        self.back_button.clicked.connect(self._on_back_clicked)
        self.back_button.setParent(self)
        self.back_button.raise_()
        # Floating overlay for info label
        self.info_label = QLabel("Align the barcode with your camera.")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: white; background: rgba(0,0,0,0.45); border-radius: 12px; border: none; padding: 10px 18px; font-size: 18px;")
        self.info_label.setMinimumHeight(36)
        self.info_label.setParent(self)
        self.info_label.raise_()

    def showEvent(self, event):
        super().showEvent(event)
        self.start_camera()
        self._update_overlay_positions()

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
        found_new = False
        for barcode in barcodes:
            barcode_data = barcode.data.decode('utf-8')
            (x, y, w, h) = barcode.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, barcode_data, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            if barcode_data != self.last_barcode:
                self.last_barcode = barcode_data
                self.barcode_scanned.emit(barcode_data)
                found_new = True
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(self.camera_frame.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.camera_frame.setPixmap(scaled_pixmap)

    def _on_back_clicked(self):
        self.stop_camera()
        self.back_requested.emit()

    def stop_camera(self):
        if self.timer:
            self.timer.stop()
            self.timer = None
        if self.cap:
            self.cap.release()
            self.cap = None
        self.camera_frame.clear()
        self.last_barcode = None  # Reset last barcode

    def closeEvent(self, event):
        self.stop_camera()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_overlay_positions()
        # Dynamically scale font size based on window height
        font_size = max(15, min(22, int(self.height() * 0.045)))
        self.info_label.setStyleSheet(
            f"color: white; background: rgba(0,0,0,0.45); border-radius: 12px; border: none; padding: 10px 18px; font-size: {font_size}px;"
        )
        self.info_label.adjustSize()

    def _update_overlay_positions(self):
        # Back button: always top-left, with margin
        margin = max(10, int(self.height() * 0.025))
        btn_size = max(40, min(64, int(self.height() * 0.09)))
        self.back_button.setFixedSize(btn_size, btn_size)
        self.back_button.move(margin, margin)
        # Info label: centered horizontally, near bottom
        info_size = self.info_label.size()
        x = max(0, (self.width() - info_size.width()) // 2)
        y = self.height() - info_size.height() - margin * 2
        y = max(margin, y)
        self.info_label.move(x, y)

    def show_info_text(self, text):
        """Show custom text in the info label, overwriting its current value."""
        self.info_label.setText(text)
        self.info_label.adjustSize()
        self._update_overlay_positions()
