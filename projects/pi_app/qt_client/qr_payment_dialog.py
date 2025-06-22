# qr_payment_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
import base64

class QRPaymentDialog(QDialog):
    payment_confirmed_mock = pyqtSignal(str) # Emits order_id
    
    def __init__(self, order_id: str, qr_svg_string: str, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.qr_svg_string = qr_svg_string
        self.setWindowTitle("Complete Your Payment")
        self.setModal(True)
        self.setFixedSize(400, 550)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignCenter)

        title_label = QLabel("Scan to Pay")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # QR Code Display
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setFixedSize(300, 300)
        self.display_qr_svg(self.qr_svg_string)
        main_layout.addWidget(self.qr_label)

        self.status_label = QLabel("Waiting for payment confirmation...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-weight: bold; color: #3498db;")
        main_layout.addWidget(self.status_label)

        main_layout.addStretch()

        # Mock Payment Confirmation Button (for testing only)
        mock_payment_widget = QWidget()
        mock_layout = QVBoxLayout(mock_payment_widget)
        mock_layout.setContentsMargins(0,0,0,0)
        mock_layout.addWidget(QLabel("--- For Testing Only ---", alignment=Qt.AlignCenter))
        self.mock_confirm_button = QPushButton("Simulate Payment Success")
        self.mock_confirm_button.setObjectName("checkout_button")
        self.mock_confirm_button.clicked.connect(self._on_mock_confirm_clicked)
        mock_layout.addWidget(self.mock_confirm_button)
        main_layout.addWidget(mock_payment_widget)

    def display_qr_svg(self, svg_string: str):
        # QPixmap can load SVG directly from bytes
        pixmap = QPixmap()
        pixmap.loadFromData(svg_string.encode('utf-8'), "SVG")
        self.qr_label.setPixmap(pixmap.scaled(self.qr_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_status(self, status_text: str, style_color: str = "#3498db"):
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"font-weight: bold; color: {style_color};")

    def _on_mock_confirm_clicked(self):
        self.mock_confirm_button.setEnabled(False) # Prevent multiple clicks
        self.payment_confirmed_mock.emit(self.order_id)