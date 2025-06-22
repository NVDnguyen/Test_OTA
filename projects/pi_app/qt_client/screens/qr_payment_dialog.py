# screens/qr_payment_dialog.py

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QMessageBox # Added for displaying messages

class QRPaymentDialog(QDialog):
    payment_confirmed = pyqtSignal(str) # Emits order_id
    
    def __init__(self, order_id: str, qr_svg_string: str, api_client, parent=None):
        super().__init__(parent)
        self.order_id = order_id
        self.qr_svg_string = qr_svg_string
        self.api_client = api_client
        self.setWindowTitle("Complete Your Payment")
        self.setModal(True)
        self.setFixedSize(400, 550)

        # Timer for polling the payment status
        self.polling_timer = QTimer(self)
        self.polling_timer.setInterval(3000) # Poll every 3 seconds
        self.polling_timer.timeout.connect(self._check_payment_status)

        self.init_ui()
        self.start_polling()

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
        mock_layout.addWidget(QLabel("Test", alignment=Qt.AlignCenter))
        self.mock_confirm_button = QPushButton("Simulate Payment Success")
        self.mock_confirm_button.setObjectName("checkout_button")
        self.mock_confirm_button.clicked.connect(self._on_mock_confirm_clicked) # Kept for testing
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

    def start_polling(self):
        """Starts the timer to poll for payment status."""
        if not self.polling_timer.isActive():
            print(f"Starting payment status polling for order {self.order_id}...")
            self._check_payment_status() # Check immediately on start
            self.polling_timer.start()

    def stop_polling(self):
        """Stops the polling timer."""
        if self.polling_timer.isActive():
            print("Stopping payment status polling.")
            self.polling_timer.stop()

    def _check_payment_status(self):
        """Method called by the timer to check the order status via API."""
        print(f"Checking status for order {self.order_id}...")
        try:
            response = self.api_client.get(f"/api/orders/{self.order_id}/status", retry_on_refresh=False)
            status_data = response.json()
            current_status = status_data.get("status")
            self.update_status(f"Status: {current_status.upper()}")

            if current_status == "paid":
                self.update_status("Payment Received! Processing order...", "#28a745")
            elif current_status == "completed":
                self.stop_polling()
                self.update_status("Order Completed!", "#28a745")
                QMessageBox.information(self, "Order Complete", "Your order has been successfully processed!")
                self.payment_confirmed.emit(self.order_id)
                self.accept() # Close dialog
            elif current_status == "failed":
                self.stop_polling()
                self.update_status("Payment Failed!", "#dc3545")
                QMessageBox.critical(self, "Payment Failed", "Your payment could not be processed.")
                self.reject() # Close dialog

        except Exception as e:
            print(f"Error checking payment status: {e}")
            # We'll let the timer continue retrying in case of transient network errors.

    def _on_mock_confirm_clicked(self):
        self.mock_confirm_button.setEnabled(False) # Prevent multiple clicks
        self.payment_confirmed.emit(self.order_id)
        self.accept() # Close the dialog

    def closeEvent(self, event):
        """Ensure the timer is stopped when the dialog is closed."""
        self.stop_polling()
        super().closeEvent(event)