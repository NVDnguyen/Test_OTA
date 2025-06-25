# home_screen.py
# Defines the UI for the home screen.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt
from qt_client.utils.serial_controller import SerialWriterThread

def create_home_screen_widget():
    """Creates and returns the home screen widget, its 'View Cart' button, and the serial output text area."""
    home_widget = QWidget()
    layout = QVBoxLayout(home_widget)
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

    serial_output_area = QTextEdit()
    serial_output_area.setObjectName("serial_output_area")
    serial_output_area.setReadOnly(True)
    serial_output_area.setPlaceholderText("Serial output will appear here...")
    layout.addWidget(serial_output_area, 1) # Give it some stretch factor

    # --- Serial send controls ---
    serial_send_layout = QHBoxLayout()
    serial_input = QLineEdit()
    serial_input.setPlaceholderText("Enter message to send to serial port...")
    serial_send_button = QPushButton("Send to Serial")
    serial_send_layout.addWidget(serial_input)
    serial_send_layout.addWidget(serial_send_button)
    layout.addLayout(serial_send_layout)

    # --- Serial writer thread setup ---
    # You may want to adjust port/baudrate as needed
    serial_writer = SerialWriterThread(port="/dev/ttyUSB0", baudrate=9600)
    serial_writer.start()

    def handle_write_success(msg):
        serial_output_area.append(f"[WRITE SUCCESS] {msg}")
    def handle_write_error(msg):
        serial_output_area.append(f"[WRITE ERROR] {msg}")

    serial_writer.write_success.connect(handle_write_success)
    serial_writer.error_occurred.connect(handle_write_error)

    def send_serial_message():
        msg = serial_input.text()
        if msg:
            serial_writer.send(msg)
            serial_input.clear()
    serial_send_button.clicked.connect(send_serial_message)

    layout.addStretch()

    view_cart_button = QPushButton("View Cart / Checkout")
    view_cart_button.setObjectName("checkout_button") # Reuse style from stylesheet
    view_cart_button.setMinimumHeight(40)
    layout.addWidget(view_cart_button, alignment=Qt.AlignCenter)
    
    login_button = QPushButton("Login / Register")
    login_button.setObjectName("link_button")
    login_button.setMinimumHeight(40)
    layout.addWidget(login_button, alignment=Qt.AlignCenter)
    
    return home_widget, view_cart_button, serial_output_area, login_button