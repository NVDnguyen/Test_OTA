# screens/home_screen.py
# Defines the UI for the home screen.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal

class HomeScreen(QWidget):
    send_serial_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(20)
        
        title_label = QLabel("Welcome to Our Store!")
        title_label.setObjectName("title_label") # Reuse existing style from stylesheet
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        products_info_label = QLabel("This is the home screen.\nBrowse our amazing products here (TODO: Implement product browsing).")
        products_info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(products_info_label)
        
        layout.addSpacing(20)

        self.serial_output_area = QTextEdit()
        self.serial_output_area.setObjectName("serial_output_area")
        self.serial_output_area.setReadOnly(True)
        self.serial_output_area.setPlaceholderText("Serial output will appear here...")
        layout.addWidget(self.serial_output_area, 1) # Give it some stretch factor

        # --- Serial send controls ---
        serial_send_layout = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enter message to send to serial port...")
        self.serial_send_button = QPushButton("Send to Serial")
        serial_send_layout.addWidget(self.serial_input)
        serial_send_layout.addWidget(self.serial_send_button)
        layout.addLayout(serial_send_layout)
        self.serial_send_button.clicked.connect(self._emit_serial_message)

        layout.addStretch()

        self.view_cart_button = QPushButton("View Cart / Checkout")
        self.view_cart_button.setObjectName("checkout_button") # Reuse style from stylesheet
        self.view_cart_button.setMinimumHeight(40)
        layout.addWidget(self.view_cart_button, alignment=Qt.AlignCenter)
        
        self.map_button = QPushButton("Product Map Search")
        self.map_button.setObjectName("checkout_button")  # Use the same style as 'View Cart / Checkout'
        self.map_button.setMinimumHeight(40)
        layout.addWidget(self.map_button, alignment=Qt.AlignCenter)
        
        self.login_button = QPushButton("Logout")
        self.login_button.setObjectName("link_button")
        self.login_button.setMinimumHeight(40)
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

    def append_serial_output(self, text):
        self.serial_output_area.moveCursor(self.serial_output_area.textCursor().End)
        self.serial_output_area.insertPlainText(text)
        self.serial_output_area.moveCursor(self.serial_output_area.textCursor().End)

    def set_serial_output(self, text):
        self.serial_output_area.setPlainText(text)

    def clear_serial_output(self):
        self.serial_output_area.clear()

    def set_map_button_callback(self, callback):
        self.map_button.clicked.connect(callback)

    def set_view_cart_callback(self, callback):
        self.view_cart_button.clicked.connect(callback)

    def set_login_button_callback(self, callback):
        self.login_button.clicked.connect(callback)

    def _emit_serial_message(self):
        msg = self.serial_input.text()
        if msg:
            self.send_serial_message.emit(msg)
            self.serial_input.clear()