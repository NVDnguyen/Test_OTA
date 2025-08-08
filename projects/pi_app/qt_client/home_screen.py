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
    serial_output_area.setStyleSheet("font-size: 18px; padding: 8px;")
    layout.addWidget(serial_output_area, 1) # Give it some stretch factor

    # Helper to limit serial output to 32 lines
    def append_serial_output_limited(text):
        current = serial_output_area.toPlainText().splitlines()
        current.append(text.rstrip('\n'))
        # Keep only the last 32 lines
        current = current[-32:]
        serial_output_area.setPlainText('\n'.join(current))
        serial_output_area.moveCursor(serial_output_area.textCursor().End)

    # --- Serial send controls ---
    serial_send_layout = QHBoxLayout()
    serial_input = QLineEdit()
    serial_input.setPlaceholderText("Enter message to send to serial port...")
    serial_input.setMinimumHeight(40)
    serial_input.setStyleSheet("font-size: 18px; padding: 8px;")
    serial_send_button = QPushButton("Send to Serial")
    serial_send_button.setMinimumHeight(48)
    serial_send_button.setStyleSheet("font-size: 20px; padding: 8px 16px;")
    clear_serial_button = QPushButton("Clear Serial Output")
    clear_serial_button.setMinimumHeight(48)
    clear_serial_button.setStyleSheet("font-size: 20px; padding: 8px 16px;")
    serial_send_layout.addWidget(serial_input)
    serial_send_layout.addWidget(serial_send_button)
    serial_send_layout.addWidget(clear_serial_button)
    layout.addLayout(serial_send_layout)

    # --- Serial writer thread setup ---
    # You may want to adjust port/baudrate as needed
    serial_writer = SerialWriterThread(port="/dev/ttyUSB0", baudrate=9600)
    serial_writer.start()

    def handle_write_success(msg):
        append_serial_output_limited(f"[WRITE SUCCESS] {msg}")
    def handle_write_error(msg):
        append_serial_output_limited(f"[WRITE ERROR] {msg}")

    serial_writer.write_success.connect(handle_write_success)
    serial_writer.error_occurred.connect(handle_write_error)

    def send_serial_message():
        msg = serial_input.text()
        if msg:
            serial_writer.send(msg)
            serial_input.clear()
    serial_send_button.clicked.connect(send_serial_message)

    def clear_serial_output():
        serial_output_area.clear()
    clear_serial_button.clicked.connect(clear_serial_output)

    # Expose the limited append function for external use
    home_widget.append_serial_output = append_serial_output_limited

    layout.addStretch()

    view_cart_button = QPushButton("View Cart / Checkout")
    view_cart_button.setObjectName("checkout_button") # Reuse style from stylesheet
    view_cart_button.setMinimumHeight(56)
    view_cart_button.setStyleSheet("font-size: 22px; padding: 12px 0;")
    layout.addWidget(view_cart_button, alignment=Qt.AlignCenter)
    
    # tracker_button = QPushButton("Open UWB Tracker")
    # tracker_button.setObjectName("link_button")
    # tracker_button.setMinimumHeight(56)
    # tracker_button.setStyleSheet("font-size:22px; padding:12px 0;")
    # layout.addWidget(tracker_button, alignment=Qt.AlignCenter)

    login_button = QPushButton("Login / Register")
    login_button.setObjectName("link_button")
    login_button.setMinimumHeight(56)
    login_button.setStyleSheet("font-size: 22px; padding: 12px 0;")
    layout.addWidget(login_button, alignment=Qt.AlignCenter)
    

    return home_widget, view_cart_button, serial_output_area, login_button
    # return home_widget, view_cart_button, serial_output_area, login_button, tracker_button
